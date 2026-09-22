import unittest

from tests import test_quote_queries


class QuoteListTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_queries.QuoteQueryTests.setUpClass.__func__)
    setUp = test_quote_queries.QuoteQueryTests.setUp
    drop_test_schema = test_quote_queries.QuoteQueryTests.drop_test_schema
    login = test_quote_queries.QuoteQueryTests.login
    payload = test_quote_queries.QuoteQueryTests.payload
    post = test_quote_queries.QuoteQueryTests.post

    def get(self, **params):
        return self.client.get('/api/v1/quotes', params=params,
                               headers={'Authorization': 'Bearer ' + self.token})

    def test_empty_defaults_pages_and_persisted_values(self):
        self.assertEqual(self.get().json(), {'data': [], 'meta': {'page': 1, 'page_size': 20, 'total': 0}})
        quotes = [self.post(self.payload()).json()['data'] for _ in range(3)]
        response = self.get(page_size=2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(response.json()['data'], list(reversed(quotes))[:2])
        self.assertEqual(response.json()['meta'], {'page': 1, 'page_size': 2, 'total': 3})
        self.assertEqual(self.get(page=2, page_size=2).json()['data'], quotes[:1])
        self.assertEqual(self.get(page=3, page_size=2).json()['data'], [])

    def test_authentication_bounds_and_foreign_quotes(self):
        self.post(self.payload())
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        self.token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        self.assertEqual(self.get().json()['meta']['total'], 0)
        self.assertEqual(self.get().json()['data'], [])
        self.assertEqual(self.client.get('/api/v1/quotes').status_code, 401)
        for params in ({'page': 0}, {'page': 2147483648}, {'page_size': 101},
                       {'page_size': 0}, {'page': 'bad'}):
            with self.subTest(params=params):
                self.assertEqual(self.get(**params).status_code, 422)

    def test_filters_search_and_sort_apply_before_pagination(self):
        first = self.post(self.payload(notes='alpha proposal')).json()['data']
        second = self.post(self.payload(notes='beta proposal')).json()['data']
        self.client.post(
            f"/api/v1/quotes/{first['id']}/send",
            headers={'Authorization': 'Bearer ' + self.token},
        )
        response = self.get(status='SENT', search='ALPHA', sort='quote_number', page_size=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['meta']['total'], 1)
        self.assertEqual(response.json()['data'][0]['id'], first['id'])
        self.assertEqual(self.get(client_id=self.client_id, sort='-total').status_code, 200)
        self.assertEqual(self.get(sort='unknown').status_code, 422)
