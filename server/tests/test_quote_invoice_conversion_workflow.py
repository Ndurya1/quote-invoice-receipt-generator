import unittest
from uuid import UUID

from tests import test_quote_endpoint


class QuoteInvoiceConversionWorkflowTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_endpoint.QuoteEndpointTests.setUpClass.__func__)
    setUp = test_quote_endpoint.QuoteEndpointTests.setUp
    drop_test_schema = test_quote_endpoint.QuoteEndpointTests.drop_test_schema
    login = test_quote_endpoint.QuoteEndpointTests.login
    payload = test_quote_endpoint.QuoteEndpointTests.payload
    post = test_quote_endpoint.QuoteEndpointTests.post

    def convert(self, quote_id):
        return self.client.post(
            f'/api/v1/quotes/{quote_id}/convert',
            json={'issue_date': '2026-09-20', 'due_date': '2026-10-01'},
            headers={'Authorization': 'Bearer ' + self.token},
        )

    def accept(self, quote_id):
        return self.client.post(
            f'/api/v1/quotes/{quote_id}/accept',
            headers={'Authorization': 'Bearer ' + self.token},
        )

    def test_independent_numbering_and_lineage_after_existing_direct_invoice(self):
        direct = self.client.post(
            '/api/v1/invoices',
            json={'client_id': self.client_id, 'issue_date': '2026-09-15', 'currency': 'KES',
                  'items': [{'description': 'Direct', 'quantity': '1', 'unit_price': '10'}]},
            headers={'Authorization': 'Bearer ' + self.token},
        ).json()['data']
        quote = self.post(self.payload()).json()['data']
        self.assertEqual(self.accept(quote['id']).status_code, 200)
        converted = self.convert(quote['id'])
        self.assertEqual(converted.status_code, 201)
        invoice = converted.json()['data']
        self.assertEqual(direct['invoice_number'], 'INV-0001')
        self.assertEqual(invoice['invoice_number'], 'INV-0002')
        self.assertEqual(invoice['source_quote_id'], quote['id'])
        self.assertNotEqual(invoice['id'], direct['id'])
        self.assertEqual(invoice['client_id'], quote['client_id'])
        self.assertEqual(invoice['currency'], quote['currency'])

    def test_quote_source_is_preserved_and_repeated_conversion_is_stable(self):
        quote = self.post(self.payload()).json()['data']
        before = self.client.get(
            f"/api/v1/quotes/{quote['id']}", headers={'Authorization': 'Bearer ' + self.token},
        ).json()['data']
        self.assertEqual(self.accept(quote['id']).status_code, 200)
        converted = self.convert(quote['id']).json()['data']
        source = self.client.get(
            f"/api/v1/quotes/{quote['id']}", headers={'Authorization': 'Bearer ' + self.token},
        ).json()['data']
        for field in before.keys() - {'status', 'updated_at'}:
            self.assertEqual(source[field], before[field], field)
        self.assertEqual(source['status'], 'CONVERTED')
        repeated = self.convert(quote['id'])
        self.assertEqual(repeated.status_code, 409)
        self.assertEqual(repeated.json()['error']['code'], 'QUOTE_ALREADY_CONVERTED')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoices WHERE source_quote_id = %s',
                                                  (UUID(quote['id']),)).fetchone()[0], 1)
        self.assertEqual(converted['source_quote_id'], quote['id'])

    def test_unaccepted_statuses_cannot_convert(self):
        for status, actions in [('DRAFT', ()), ('SENT', ('send',)),
                                ('REJECTED', ('send', 'reject')), ('EXPIRED', ())]:
            quote = self.post(self.payload()).json()['data']
            for action in actions:
                self.assertEqual(self.client.post(
                    f"/api/v1/quotes/{quote['id']}/{action}",
                    headers={'Authorization': 'Bearer ' + self.token},
                ).status_code, 200)
            if status == 'EXPIRED':
                self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                        (status, UUID(quote['id'])))
            response = self.convert(quote['id'])
            with self.subTest(status=status):
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()['error']['code'], 'INVALID_QUOTE_STATUS')

    def test_database_failure_rolls_back_invoice_quote_and_number(self):
        quote = self.post(self.payload()).json()['data']
        self.assertEqual(self.accept(quote['id']).status_code, 200)
        self.connection.execute('''CREATE FUNCTION reject_workflow_item() RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Private workflow detail'; END; $$;
            CREATE TRIGGER reject_workflow_item BEFORE INSERT ON invoice_items
            FOR EACH ROW EXECUTE FUNCTION reject_workflow_item();''')
        response = self.convert(quote['id'])
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error']['code'], 'INTERNAL_SERVER_ERROR')
        self.assertNotIn('Private workflow detail', response.text)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoices').fetchone()[0], 0)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM invoice_number_counters').fetchone()[0], 0)
        saved = self.client.get(
            f"/api/v1/quotes/{quote['id']}", headers={'Authorization': 'Bearer ' + self.token},
        ).json()['data']
        self.assertEqual(saved['status'], 'ACCEPTED')
