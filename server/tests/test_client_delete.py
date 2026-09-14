import unittest
from uuid import UUID, uuid4

from psycopg import sql

from app.clients.service import delete_client
from tests import test_client_detail


class ClientDeleteTests(unittest.TestCase):
    setUpClass = classmethod(test_client_detail.ClientDetailTests.setUpClass.__func__)
    setUp = test_client_detail.ClientDetailTests.setUp
    drop_test_schema = test_client_detail.ClientDetailTests.drop_test_schema
    login = test_client_detail.ClientDetailTests.login
    create = test_client_detail.ClientDetailTests.create
    read = test_client_detail.ClientDetailTests.read

    def delete(self, token, client_id, **params):
        response = self.client.delete('/api/v1/clients/' + client_id, params=params,
                                      headers={'Authorization': 'Bearer ' + token})
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_unreferenced_client_deleted_with_empty_204(self):
        token = self.login().json()['data']['access_token']
        created = self.create(token)
        response = self.delete(token, created['id'])
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertEqual(self.read(token, created['id']).status_code, 404)
        self.assertEqual(self.delete(token, created['id']).status_code, 404)

    def test_each_document_type_blocks_deletion_and_remains_unchanged(self):
        token = self.login().json()['data']['access_token']
        for table, number_column in (('quotes', 'quote_number'), ('invoices', 'invoice_number'),
                                      ('receipts', 'receipt_number')):
            with self.subTest(table=table):
                created = self.create(token)
                document_id = self.connection.execute(
                    sql.SQL('INSERT INTO {} (user_id, client_id, {}, issue_date, currency, subtotal, total) '
                            "VALUES (%s, %s, %s, CURRENT_DATE, 'KES', 0, 0) RETURNING id")
                    .format(sql.Identifier(table), sql.Identifier(number_column)),
                    (UUID(self.user_id), UUID(created['id']), 'TEST-1'),
                ).fetchone()[0]
                query = sql.SQL('SELECT * FROM {} WHERE id = %s').format(sql.Identifier(table))
                original = self.connection.execute(query, (document_id,)).fetchone()
                response = self.delete(token, created['id'])
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json(), {'error': {
                    'code': 'CLIENT_IN_USE',
                    'message': 'Client is referenced by documents and cannot be deleted.', 'details': {},
                }})
                self.assertEqual(self.read(token, created['id']).json(), {'data': created})
                self.assertEqual(self.connection.execute(query, (document_id,)).fetchone(), original)
        # A blocked delete does not leave subsequent requests unusable.
        unreferenced = self.create(token)
        self.assertEqual(self.delete(token, unreferenced['id']).status_code, 204)

    def test_foreign_and_missing_clients_return_same_404(self):
        other = self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'OtherPassword123',
        }).json()['data']
        other_token = self.login(email='other@example.com', password='OtherPassword123').json()['data']['access_token']
        foreign = self.create(other_token)
        token = self.login().json()['data']['access_token']
        for client_id in (foreign['id'], str(uuid4())):
            response = self.delete(token, client_id, user_id=other['id'])
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {'error': {
                'code': 'CLIENT_NOT_FOUND', 'message': 'Client not found.', 'details': {},
            }})
        self.assertEqual(self.read(other_token, foreign['id']).json(), {'data': foreign})

    def test_authentication_and_uuid_validation(self):
        pair = self.login().json()['data']
        created = self.create(pair['access_token'])
        for headers in ({}, {'Authorization': 'Bearer invalid'},
                        {'Authorization': 'Bearer ' + pair['refresh_token']}):
            response = self.client.delete('/api/v1/clients/' + created['id'], headers=headers)
            self.assertEqual(response.status_code, 401)
        self.assertEqual(self.delete(pair['access_token'], 'invalid-uuid').status_code, 422)
        self.assertEqual(self.read(pair['access_token'], created['id']).json(), {'data': created})

    def test_service_delete_respects_outer_transaction_rollback(self):
        token = self.login().json()['data']['access_token']
        created = self.create(token)
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                delete_client(self.connection, user_id=UUID(self.user_id), client_id=UUID(created['id']))
                raise RuntimeError('abort')
        self.assertEqual(self.read(token, created['id']).json(), {'data': created})

    def test_openapi_documents_bodyless_authenticated_delete(self):
        operation = self.client.get('/openapi.json').json()['paths']['/api/v1/clients/{client_id}']['delete']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        self.assertNotIn('content', operation['responses']['204'])
