import unittest
from uuid import uuid4

from tests import test_invoice_endpoint


class InvoiceDetailTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_endpoint.InvoiceEndpointTests.setUpClass.__func__)
    setUp = test_invoice_endpoint.InvoiceEndpointTests.setUp
    drop_test_schema = test_invoice_endpoint.InvoiceEndpointTests.drop_test_schema
    login = test_invoice_endpoint.InvoiceEndpointTests.login
    payload = test_invoice_endpoint.InvoiceEndpointTests.payload
    post = test_invoice_endpoint.InvoiceEndpointTests.post

    def get(self, invoice_id, token=None):
        return self.client.get(
            f'/api/v1/invoices/{invoice_id}',
            headers={'Authorization': 'Bearer ' + (token or self.token)},
        )

    def test_owned_invoice_returns_persisted_detail(self):
        created = self.post(self.payload()).json()['data']
        response = self.get(created['id'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(response.json(), {'data': created})

    def test_missing_and_foreign_invoice_are_not_found(self):
        created = self.post(self.payload()).json()['data']
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        other_token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        for invoice_id in (created['id'], str(uuid4())):
            with self.subTest(invoice_id=invoice_id):
                response = self.get(invoice_id, token=other_token)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()['error']['code'], 'INVOICE_NOT_FOUND')

    def test_authentication_required(self):
        invoice_id = self.post(self.payload()).json()['data']['id']
        self.assertEqual(self.client.get(f'/api/v1/invoices/{invoice_id}').status_code, 401)
