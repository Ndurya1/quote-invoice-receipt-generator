import unittest
from uuid import uuid4

from tests import test_receipt_endpoint


class ReceiptDetailTests(unittest.TestCase):
    setUpClass = classmethod(test_receipt_endpoint.ReceiptEndpointTests.setUpClass.__func__)
    setUp = test_receipt_endpoint.ReceiptEndpointTests.setUp
    drop_test_schema = test_receipt_endpoint.ReceiptEndpointTests.drop_test_schema
    login = test_receipt_endpoint.ReceiptEndpointTests.login
    payload = test_receipt_endpoint.ReceiptEndpointTests.payload
    post = test_receipt_endpoint.ReceiptEndpointTests.post

    def get(self, receipt_id, token=None):
        return self.client.get(
            f'/api/v1/receipts/{receipt_id}',
            headers={'Authorization': 'Bearer ' + (token or self.token)},
        )

    def test_owned_receipt_returns_persisted_detail(self):
        created = self.post(self.payload()).json()['data']
        response = self.get(created['id'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(response.json(), {'data': created})

    def test_missing_and_foreign_receipt_are_not_found(self):
        created = self.post(self.payload()).json()['data']
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        other_token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        for receipt_id in (created['id'], str(uuid4())):
            with self.subTest(receipt_id=receipt_id):
                response = self.get(receipt_id, token=other_token)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()['error']['code'], 'RECEIPT_NOT_FOUND')

    def test_authentication_required(self):
        receipt_id = self.post(self.payload()).json()['data']['id']
        self.assertEqual(self.client.get(f'/api/v1/receipts/{receipt_id}').status_code, 401)
