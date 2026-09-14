import unittest
from uuid import UUID, uuid4

from app.clients.schemas import ClientPatch
from app.clients.service import update_client
from tests import test_client_detail


class ClientPatchTests(unittest.TestCase):
    setUpClass = classmethod(test_client_detail.ClientDetailTests.setUpClass.__func__)
    setUp = test_client_detail.ClientDetailTests.setUp
    drop_test_schema = test_client_detail.ClientDetailTests.drop_test_schema
    login = test_client_detail.ClientDetailTests.login
    create = test_client_detail.ClientDetailTests.create
    read = test_client_detail.ClientDetailTests.read

    def patch(self, token, client_id, payload):
        response = self.client.patch('/api/v1/clients/' + client_id, json=payload,
                                     headers={'Authorization': 'Bearer ' + token})
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_partial_update_preserves_omitted_and_immutable_fields(self):
        token = self.login().json()['data']['access_token']
        original = self.create(token, email='original@example.com', phone='123', address='Nairobi')
        response = self.patch(token, original['id'], {'name': '  New Name  '})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        updated = response.json()['data']
        for field in ('id', 'user_id', 'created_at', 'email', 'phone', 'address'):
            self.assertEqual(updated[field], original[field])
        self.assertEqual(updated['name'], 'New Name')
        self.assertGreater(updated['updated_at'], original['updated_at'])
        self.assertEqual(self.read(token, original['id']).json(), response.json())
        self.assertEqual(self.patch(token, original['id'], {}).json(), response.json())

    def test_contacts_can_change_and_be_cleared(self):
        token = self.login().json()['data']['access_token']
        original = self.create(token)
        fields = {'email': 'new@example.com', 'phone': '+254700123456', 'address': 'Kisii'}
        updated = self.patch(token, original['id'], fields).json()['data']
        for field, value in fields.items():
            self.assertEqual(updated[field], value)
        cleared = self.patch(token, original['id'], dict.fromkeys(fields)).json()['data']
        for field in fields:
            self.assertIsNone(cleared[field])
        self.assertEqual(cleared['name'], original['name'])

    def test_invalid_and_server_managed_fields_do_not_change_row(self):
        token = self.login().json()['data']['access_token']
        original = self.create(token)
        payloads = [{'name': None}, {'name': ''}, {'name': ' '}, {'name': 'x' * 161},
                    {'email': 'invalid'}, {'phone': '1' * 31}, {'address': []}]
        payloads += [{field: str(uuid4())} for field in ('user_id', 'id', 'created_at', 'updated_at', 'unknown')]
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.patch(token, original['id'], payload)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(self.read(token, original['id']).json(), {'data': original})

    def test_foreign_and_missing_clients_cannot_be_updated(self):
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'OtherPassword123',
        })
        other_token = self.login(email='other@example.com', password='OtherPassword123').json()['data']['access_token']
        foreign = self.create(other_token)
        token = self.login().json()['data']['access_token']
        for client_id in (foreign['id'], str(uuid4())):
            for payload in ({'name': 'Attack'}, {}):
                response = self.patch(token, client_id, payload)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()['error']['code'], 'CLIENT_NOT_FOUND')
        self.assertEqual(self.read(other_token, foreign['id']).json(), {'data': foreign})

    def test_authentication_and_uuid_validation(self):
        pair = self.login().json()['data']
        original = self.create(pair['access_token'])
        for headers in ({}, {'Authorization': 'Bearer invalid'},
                        {'Authorization': 'Bearer ' + pair['refresh_token']}):
            response = self.client.patch('/api/v1/clients/' + original['id'],
                                         json={'name': 'Changed'}, headers=headers)
            self.assertEqual(response.status_code, 401)
        self.assertEqual(self.patch(pair['access_token'], 'bad-uuid', {}).status_code, 422)
        self.assertEqual(self.read(pair['access_token'], original['id']).json(), {'data': original})

    def test_service_update_rolls_back_with_outer_transaction(self):
        token = self.login().json()['data']['access_token']
        original = self.create(token)
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                update_client(self.connection, user_id=UUID(self.user_id), client_id=UUID(original['id']),
                              payload=ClientPatch(name='Changed'))
                raise RuntimeError('abort')
        self.assertEqual(self.read(token, original['id']).json(), {'data': original})
