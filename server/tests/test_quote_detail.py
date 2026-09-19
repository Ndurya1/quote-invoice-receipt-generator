import unittest
from uuid import uuid4

from tests import test_quote_queries


class QuoteDetailTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_queries.QuoteQueryTests.setUpClass.__func__)
    setUp = test_quote_queries.QuoteQueryTests.setUp
    drop_test_schema = test_quote_queries.QuoteQueryTests.drop_test_schema
    login = test_quote_queries.QuoteQueryTests.login
    payload = test_quote_queries.QuoteQueryTests.payload
    post = test_quote_queries.QuoteQueryTests.post

    def get(self, quote_id):
        return self.client.get('/api/v1/quotes/' + str(quote_id),
                               headers={'Authorization': 'Bearer ' + self.token})

    def test_detail_returns_persisted_values_and_ordered_items(self):
        quote = self.post(self.payload(items=[
            {'description': 'Last', 'quantity': '2', 'unit_price': '25', 'position': 8},
            {'description': 'First', 'quantity': '1.25', 'unit_price': '80', 'position': 0},
        ])).json()['data']
        quote['items'].reverse()
        response = self.get(quote['id'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data'], quote)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertTrue(all(connection.closed for connection in self.request_connections))

    def test_missing_foreign_invalid_uuid_and_authentication(self):
        quote = self.post(self.payload()).json()['data']
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        self.token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        missing, foreign = self.get(uuid4()), self.get(quote['id'])
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(missing.json(), foreign.json())
        self.assertEqual(foreign.json()['error']['code'], 'QUOTE_NOT_FOUND')
        self.assertEqual(self.get('bad').status_code, 422)
        self.assertEqual(self.client.get('/api/v1/quotes/' + quote['id']).status_code, 401)

    def test_openapi_detail_requires_authentication(self):
        operation = self.client.get('/openapi.json').json()['paths']['/api/v1/quotes/{quote_id}']['get']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        self.assertIn('200', operation['responses'])
