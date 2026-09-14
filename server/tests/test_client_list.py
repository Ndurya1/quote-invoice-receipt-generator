import unittest
from uuid import UUID

from tests import test_login


class ClientListTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def seed(self, user_id, count):
        with self.connection.transaction():
            return sorted(str(self.connection.execute(
                'INSERT INTO clients (user_id, name) VALUES (%s, %s) RETURNING id',
                (UUID(user_id), 'Client'),
            ).fetchone()[0]) for _ in range(count))

    def get(self, token, **params):
        response = self.client.get('/api/v1/clients', params=params,
                                   headers={'Authorization': 'Bearer ' + token})
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_default_page_and_last_and_out_of_range_pages(self):
        ids = self.seed(self.user_id, 23)
        token = self.login().json()['data']['access_token']
        response = self.get(token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(response.json()['meta'], {'page': 1, 'page_size': 20, 'total': 23})
        self.assertEqual([row['id'] for row in response.json()['data']], ids[:20])
        for page, expected in ((2, ids[20:]), (3, [])):
            data = self.get(token, page=page).json()
            self.assertEqual(data['meta'], {'page': page, 'page_size': 20, 'total': 23})
            self.assertEqual([row['id'] for row in data['data']], expected)
        self.assertEqual(len(self.get(token, page_size=100).json()['data']), 23)
        data = self.get(token, page=2, page_size=5).json()
        self.assertEqual(data['meta'], {'page': 2, 'page_size': 5, 'total': 23})
        self.assertEqual([row['id'] for row in data['data']], ids[5:10])

    def test_empty_account_and_foreign_clients_do_not_affect_total(self):
        other = self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'OtherPassword123',
        }).json()['data']
        self.seed(other['id'], 3)
        token = self.login().json()['data']['access_token']
        self.assertEqual(self.get(token, user_id=other['id']).json(), {
            'data': [], 'meta': {'page': 1, 'page_size': 20, 'total': 0},
        })
        own = self.seed(self.user_id, 2)
        data = self.get(token, user_id=other['id']).json()
        self.assertEqual(data['meta']['total'], 2)
        self.assertEqual([row['id'] for row in data['data']], own)
        self.assertTrue(all(row['user_id'] == self.user_id for row in data['data']))

    def test_invalid_pagination_returns_validation_error(self):
        token = self.login().json()['data']['access_token']
        for params in ({'page': 0}, {'page': -1}, {'page': 'abc'}, {'page': '1.5'},
                       {'page': 2147483648}, {'page_size': 0}, {'page_size': -1},
                       {'page_size': 101}, {'page_size': 'abc'}):
            with self.subTest(params=params):
                response = self.get(token, **params)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')

    def test_authentication_required(self):
        pair = self.login().json()['data']
        for headers in ({}, {'Authorization': 'Bearer invalid'},
                        {'Authorization': 'Bearer ' + pair['refresh_token']}):
            response = self.client.get('/api/v1/clients', headers=headers)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()['error']['code'], 'AUTHENTICATION_REQUIRED')

    def test_openapi_documents_authenticated_pagination(self):
        operation = self.client.get('/openapi.json').json()['paths']['/api/v1/clients']['get']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        parameters = {p['name']: p['schema'] for p in operation['parameters']}
        self.assertEqual(parameters['page']['default'], 1)
        self.assertEqual(parameters['page_size']['default'], 20)
        self.assertEqual(parameters['page_size']['maximum'], 100)
