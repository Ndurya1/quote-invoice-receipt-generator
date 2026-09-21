import unittest
from uuid import uuid4

from tests import test_invoice_endpoint


class InvoiceMarkPaidTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_endpoint.InvoiceEndpointTests.setUpClass.__func__)
    setUp = test_invoice_endpoint.InvoiceEndpointTests.setUp
    drop_test_schema = test_invoice_endpoint.InvoiceEndpointTests.drop_test_schema
    login = test_invoice_endpoint.InvoiceEndpointTests.login
    payload = test_invoice_endpoint.InvoiceEndpointTests.payload
    post = test_invoice_endpoint.InvoiceEndpointTests.post

    def action(self, invoice_id, token=None):
        return self.client.post(
            f'/api/v1/invoices/{invoice_id}/mark-paid',
            headers={'Authorization': 'Bearer ' + (token or self.token)},
        )

    def test_sent_invoice_can_be_marked_paid_without_payment_record(self):
        invoice = self.post(self.payload()).json()['data']
        self.client.post(f"/api/v1/invoices/{invoice['id']}/send",
                         headers={'Authorization': 'Bearer ' + self.token})
        response = self.action(invoice['id'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(response.json()['data']['status'], 'PAID')
        self.assertEqual(response.json()['data']['items'], invoice['items'])
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoices').fetchone()[0], 1)

    def test_invalid_repeated_foreign_missing_and_unauthenticated_requests(self):
        invoice = self.post(self.payload()).json()['data']
        invalid = self.action(invoice['id'])
        self.assertEqual(invalid.status_code, 409)
        self.assertEqual(invalid.json()['error']['code'], 'INVALID_INVOICE_STATUS')
        self.assertEqual(self.action(str(uuid4())).status_code, 404)
        self.assertEqual(self.client.post(f"/api/v1/invoices/{invoice['id']}/mark-paid").status_code, 401)

        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        other_token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        foreign = self.action(invoice['id'], token=other_token)
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json()['error']['code'], 'INVOICE_NOT_FOUND')
