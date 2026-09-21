import unittest
from uuid import UUID

from tests import test_quote_endpoint


class HistoricalIntegrityTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_endpoint.QuoteEndpointTests.setUpClass.__func__)
    setUp = test_quote_endpoint.QuoteEndpointTests.setUp
    drop_test_schema = test_quote_endpoint.QuoteEndpointTests.drop_test_schema
    login = test_quote_endpoint.QuoteEndpointTests.login
    payload = test_quote_endpoint.QuoteEndpointTests.payload
    post_quote = test_quote_endpoint.QuoteEndpointTests.post

    def auth_headers(self):
        return {'Authorization': 'Bearer ' + self.token}

    def accept_quote(self, quote_id):
        return self.client.post(f'/api/v1/quotes/{quote_id}/accept', headers=self.auth_headers())

    def convert_quote(self, quote_id):
        return self.client.post(
            f'/api/v1/quotes/{quote_id}/convert',
            json={'issue_date': '2026-09-20', 'due_date': '2026-10-01'},
            headers=self.auth_headers(),
        )

    def convert_invoice(self, invoice_id):
        return self.client.post(
            f'/api/v1/invoices/{invoice_id}/convert',
            json={'issue_date': '2026-10-02'},
            headers=self.auth_headers(),
        )

    def get_quote(self, quote_id):
        return self.client.get(f'/api/v1/quotes/{quote_id}', headers=self.auth_headers())

    def get_invoice(self, invoice_id):
        return self.client.get(f'/api/v1/invoices/{invoice_id}', headers=self.auth_headers())

    def test_quote_and_items_remain_unchanged_after_invoice_edit_attempt(self):
        quote = self.post_quote(self.payload(notes='Original quote')).json()['data']
        before = self.get_quote(quote['id']).json()['data']
        self.assertEqual(self.accept_quote(quote['id']).status_code, 200)
        invoice = self.convert_quote(quote['id']).json()['data']

        edited = self.client.patch(
            f"/api/v1/invoices/{invoice['id']}",
            json={'notes': 'Edited destination invoice'},
            headers=self.auth_headers(),
        )

        self.assertEqual(edited.status_code, 409)
        self.assertEqual(edited.json()['error']['code'], 'INVALID_INVOICE_STATUS')
        after = self.get_quote(quote['id']).json()['data']
        for field in before.keys() - {'status', 'updated_at'}:
            self.assertEqual(after[field], before[field], field)
        self.assertEqual(after['status'], 'CONVERTED')
        self.assertEqual(after['items'], before['items'])

    def test_invoice_remains_unchanged_when_linked_receipt_edit_is_rejected(self):
        invoice = self.client.post(
            '/api/v1/invoices',
            json={'client_id': self.client_id, 'issue_date': '2026-09-15',
                  'currency': 'KES', 'notes': 'Original invoice',
                  'items': [{'description': 'Work', 'quantity': '1', 'unit_price': '80'}]},
            headers=self.auth_headers(),
        ).json()['data']
        before = self.get_invoice(invoice['id']).json()['data']
        receipt = self.convert_invoice(invoice['id']).json()['data']

        edited = self.client.patch(
            f"/api/v1/receipts/{receipt['id']}",
            json={'notes': 'Attempted receipt edit'},
            headers=self.auth_headers(),
        )

        self.assertEqual(edited.status_code, 409)
        self.assertEqual(edited.json()['error']['code'], 'INVALID_RECEIPT_STATUS')
        after = self.get_invoice(invoice['id']).json()['data']
        self.assertEqual(after, before)

    def test_full_conversion_lineage_uses_independent_documents_and_items(self):
        quote = self.post_quote(self.payload()).json()['data']
        self.assertEqual(self.accept_quote(quote['id']).status_code, 200)
        invoice = self.convert_quote(quote['id']).json()['data']
        receipt = self.convert_invoice(invoice['id']).json()['data']

        self.assertEqual(invoice['source_quote_id'], quote['id'])
        self.assertEqual(receipt['source_invoice_id'], invoice['id'])
        self.assertEqual((quote['quote_number'], invoice['invoice_number'], receipt['receipt_number']),
                         ('QT-0001', 'INV-0001', 'RCT-0001'))
        self.assertEqual((invoice['client_id'], receipt['client_id']), (quote['client_id'], quote['client_id']))
        self.assertEqual((invoice['currency'], receipt['currency']), (quote['currency'], quote['currency']))
        self.assertEqual(len(quote['items']), len(invoice['items']))
        self.assertEqual(len(invoice['items']), len(receipt['items']))
        self.assertNotEqual(quote['items'][0]['id'], invoice['items'][0]['id'])
        self.assertNotEqual(invoice['items'][0]['id'], receipt['items'][0]['id'])
        self.assertEqual(invoice['items'][0]['description'], quote['items'][0]['description'])
        self.assertEqual(receipt['items'][0]['description'], invoice['items'][0]['description'])
        self.assertEqual((quote['total'], invoice['total'], receipt['total']),
                         ('106.00', '106.00', '106.00'))
        self.assertEqual(self.connection.execute(
            'SELECT count(*) FROM invoices WHERE source_quote_id = %s', (UUID(quote['id']),)
        ).fetchone()[0], 1)
        self.assertEqual(self.connection.execute(
            'SELECT count(*) FROM receipts WHERE source_invoice_id = %s', (UUID(invoice['id']),)
        ).fetchone()[0], 1)
