import unittest
from uuid import uuid4

from tests import test_invoice_endpoint


class InvoiceReceiptConversionEndpointTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_endpoint.InvoiceEndpointTests.setUpClass.__func__)
    setUp = test_invoice_endpoint.InvoiceEndpointTests.setUp
    drop_test_schema = test_invoice_endpoint.InvoiceEndpointTests.drop_test_schema
    login = test_invoice_endpoint.InvoiceEndpointTests.login
    payload = test_invoice_endpoint.InvoiceEndpointTests.payload
    post = test_invoice_endpoint.InvoiceEndpointTests.post

    def convert(self, invoice_id, payload=None, token=None):
        return self.client.post(
            f'/api/v1/invoices/{invoice_id}/convert',
            json={'issue_date': '2026-10-01'} if payload is None else payload,
            headers={'Authorization': 'Bearer ' + (token or self.token)},
        )

    def test_invoice_conversion_returns_created_receipt(self):
        invoice = self.post(self.payload()).json()['data']
        response = self.convert(invoice['id'])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        data = response.json()['data']
        self.assertEqual(data['source_invoice_id'], invoice['id'])
        self.assertEqual(data['receipt_number'], 'RCT-0001')
        self.assertEqual(data['currency'], invoice['currency'])
        self.assertEqual(len(data['items']), len(invoice['items']))

    def test_request_validation_and_authentication(self):
        invoice = self.post(self.payload()).json()['data']
        for payload in ({}, {'issue_date': '2026-10-01', 'unexpected': 'forged'},
                        {'issue_date': 'not-a-date'}):
            with self.subTest(payload=payload):
                response = self.convert(invoice['id'], payload)
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.post(
            f"/api/v1/invoices/{invoice['id']}/convert", json={'issue_date': '2026-10-01'},
        ).status_code, 401)

    def test_cancelled_foreign_and_missing_invoices_are_rejected(self):
        invoice = self.post(self.payload()).json()['data']
        self.connection.execute("UPDATE invoices SET status = 'CANCELLED' WHERE id = %s", (invoice['id'],))
        cancelled = self.convert(invoice['id'])
        self.assertEqual(cancelled.status_code, 409)
        self.assertEqual(cancelled.json()['error']['code'], 'INVALID_INVOICE_STATUS')

        invoice = self.post(self.payload()).json()['data']
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        other_token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        foreign = self.convert(invoice['id'], token=other_token)
        missing = self.convert(str(uuid4()), token=other_token)
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json(), missing.json())
        self.assertEqual(foreign.json()['error']['code'], 'INVOICE_NOT_FOUND')

    def test_openapi_documents_conversion_contract(self):
        operation = self.client.get('/openapi.json').json()['paths'][
            '/api/v1/invoices/{invoice_id}/convert']['post']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        self.assertIn('201', operation['responses'])
        self.assertIn('requestBody', operation)
