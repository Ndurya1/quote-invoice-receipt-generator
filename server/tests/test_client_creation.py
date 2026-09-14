import unittest
from uuid import UUID, uuid4

from app.clients.queries import get_client_for_user
from app.clients.schemas import ClientCreate
from app.clients.service import create_client
from tests import test_login


class ClientCreationTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def post(self, payload, token):
        response = self.client.post('/api/v1/clients', json=payload,
                                    headers={'Authorization': 'Bearer ' + token})
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_create_returns_persisted_client_and_optional_defaults(self):
        token = self.login().json()['data']['access_token']
        for payload in ({'name': '  Acme Ltd  '},
                        {'name': "O'Brien", 'email': 'accounts@example.com',
                         'phone': '+254700123456', 'address': 'Nairobi'},
                        {'name': 'Null contacts', 'email': None, 'phone': None, 'address': None}):
            response = self.post(payload, token)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            self.assertEqual(set(response.json()), {'data'})
            data = response.json()['data']
            self.assertEqual(data['user_id'], self.user_id)
            self.assertEqual(data['name'], payload['name'].strip())
            for field in ('email', 'phone', 'address'):
                self.assertEqual(data[field], payload.get(field))
            stored = get_client_for_user(self.connection, user_id=UUID(self.user_id), client_id=UUID(data['id']))
            self.assertEqual(stored.model_dump(mode='json'), data)

    def test_invalid_input_creates_no_rows(self):
        token = self.login().json()['data']['access_token']
        payloads = [{}, {'name': ''}, {'name': '  '}, {'name': None}, {'name': 123},
                    {'name': 'x' * 161}, {'name': 'Client', 'email': 'invalid'},
                    {'name': 'Client', 'phone': '1' * 31}, {'name': 'Client', 'address': []}]
        for field in ('user_id', 'id', 'created_at', 'updated_at', 'unknown'):
            payloads.append({'name': 'Client', field: str(uuid4())})
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.post(payload, token)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM clients').fetchone()[0], 0)

    def test_duplicate_emails_allowed_and_owners_cannot_be_overridden(self):
        other = self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'OtherPassword123',
        }).json()['data']
        token = self.login().json()['data']['access_token']
        other_token = self.login(email='other@example.com', password='OtherPassword123').json()['data']['access_token']
        payload = {'name': 'Client', 'email': 'shared@example.com'}
        ids = []
        for owner_token, owner_id in ((token, self.user_id), (token, self.user_id), (other_token, other['id'])):
            response = self.post(payload, owner_token)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()['data']['user_id'], owner_id)
            ids.append(response.json()['data']['id'])
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual(self.post({**payload, 'user_id': other['id']}, token).status_code, 422)
        response = self.client.post('/api/v1/clients', params={'user_id': other['id']}, json=payload,
                                    headers={'Authorization': 'Bearer ' + token, 'X-User-Id': other['id']})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['data']['user_id'], self.user_id)

    def test_unauthenticated_and_deleted_users_cannot_create(self):
        pair = self.login().json()['data']
        for headers in ({}, {'Authorization': 'Bearer invalid'},
                        {'Authorization': 'Bearer ' + pair['refresh_token']}):
            response = self.client.post('/api/v1/clients', json={'name': 'Client'}, headers=headers)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()['error']['code'], 'AUTHENTICATION_REQUIRED')
        self.connection.execute('DELETE FROM users WHERE id = %s', (UUID(self.user_id),))
        self.assertEqual(self.post({'name': 'Client'}, pair['access_token']).status_code, 401)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM clients').fetchone()[0], 0)

    def test_creation_respects_outer_transaction_rollback(self):
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                create_client(self.connection, user_id=UUID(self.user_id), payload=ClientCreate(name='Client'))
                raise RuntimeError('abort')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM clients').fetchone()[0], 0)

    def test_openapi_documents_authenticated_creation(self):
        path = self.client.get('/openapi.json').json()['paths']['/api/v1/clients']
        self.assertEqual(set(path), {'post'})
        self.assertEqual(path['post']['security'], [{'HTTPBearer': []}])
        self.assertIn('201', path['post']['responses'])
