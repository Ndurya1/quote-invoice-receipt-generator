import unittest

from tests import test_receipt_endpoint


class ReceiptListTests(unittest.TestCase):
    setUpClass = classmethod(test_receipt_endpoint.ReceiptEndpointTests.setUpClass.__func__)
    setUp = test_receipt_endpoint.ReceiptEndpointTests.setUp
    drop_test_schema = test_receipt_endpoint.ReceiptEndpointTests.drop_test_schema
    login = test_receipt_endpoint.ReceiptEndpointTests.login
    payload = test_receipt_endpoint.ReceiptEndpointTests.payload
    post = test_receipt_endpoint.ReceiptEndpointTests.post

    def get(self, **params):
        return self.client.get('/api/v1/receipts', params=params,
                               headers={'Authorization': 'Bearer ' + self.token})

    def test_empty_defaults_pages_and_persisted_values(self):
        self.assertEqual(self.get().json(), {'data': [], 'meta': {'page': 1, 'page_size': 20, 'total': 0}})
        receipts = [self.post(self.payload()).json()['data'] for _ in range(3)]
        response = self.get(page_size=2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(response.json()['data'], list(reversed(receipts))[:2])
        self.assertEqual(response.json()['meta'], {'page': 1, 'page_size': 2, 'total': 3})
        self.assertEqual(self.get(page=2, page_size=2).json()['data'], receipts[:1])
        self.assertEqual(self.get(page=3, page_size=2).json()['data'], [])

    def test_authentication_bounds_and_isolation(self):
        self.post(self.payload())
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        self.token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        self.assertEqual(self.get().json()['meta']['total'], 0)
        self.assertEqual(self.get().json()['data'], [])
        self.assertEqual(self.client.get('/api/v1/receipts').status_code, 401)
        for params in ({'page': 0}, {'page': 2147483648}, {'page_size': 101},
                       {'page_size': 0}, {'page': 'bad'}):
            with self.subTest(params=params):
                self.assertEqual(self.get(**params).status_code, 422)
