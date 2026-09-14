import unittest
from uuid import uuid4

from tests import test_login


class ClientDetailTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def create(self, token, **fields):
        response = self.client.post('/api/v1/clients', json={'name': 'Acme', **fields},
                                    headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(response.status_code, 201)
        return response.json()['data']

    def read(self, token, client_id, **params):
        response = self.client.get('/api/v1/clients/' + client_id, params=params,
                                   headers={'Authorization': 'Bearer ' + token})
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_owner_receives_exact_persisted_client(self):
        token = self.login().json()['data']['access_token']
        for fields in ({}, {'email': 'acme@example.com', 'phone': '+254700123456', 'address': 'Nairobi'}):
            created = self.create(token, **fields)
            response = self.read(token, created['id'])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            self.assertEqual(response.json(), {'data': created})

    def test_missing_and_foreign_clients_have_identical_errors(self):
        other = self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'OtherPassword123',
        }).json()['data']
        other_token = self.login(email='other@example.com', password='OtherPassword123').json()['data']['access_token']
        foreign = self.create(other_token)
        token = self.login().json()['data']['access_token']
        for client_id in (foreign['id'], str(uuid4())):
            response = self.read(token, client_id, user_id=other['id'])
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {'error': {
                'code': 'CLIENT_NOT_FOUND', 'message': 'Client not found.', 'details': {},
            }})
        own = self.create(token)
        self.assertEqual(self.read(token, own['id'], user_id=other['id']).json(), {'data': own})
        self.assertEqual(self.read(other_token, foreign['id']).json(), {'data': foreign})

    def test_invalid_uuid_returns_validation_error(self):
        token = self.login().json()['data']['access_token']
        response = self.read(token, 'not-a-uuid')
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')

    def test_access_authentication_is_required(self):
        pair = self.login().json()['data']
        created = self.create(pair['access_token'])
        for headers in ({}, {'Authorization': 'Bearer invalid'},
                        {'Authorization': 'Bearer ' + pair['refresh_token']}):
            response = self.client.get('/api/v1/clients/' + created['id'], headers=headers)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()['error']['code'], 'AUTHENTICATION_REQUIRED')
            self.assertEqual(response.headers['www-authenticate'], 'Bearer')

    def test_openapi_declares_uuid_and_bearer_security(self):
        path = self.client.get('/openapi.json').json()['paths']['/api/v1/clients/{client_id}']
        self.assertEqual(set(path), {'get', 'patch'})
        operation = path['get']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        parameter = next(p for p in operation['parameters'] if p['name'] == 'client_id')
        self.assertEqual(parameter['schema']['format'], 'uuid')
        self.assertIn('200', operation['responses'])
