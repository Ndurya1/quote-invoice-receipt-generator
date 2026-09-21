import unittest

from tests import test_invoice_endpoint


class InvoiceReceiptConversionWorkflowTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_endpoint.InvoiceEndpointTests.setUpClass.__func__)
    setUp = test_invoice_endpoint.InvoiceEndpointTests.setUp
    drop_test_schema = test_invoice_endpoint.InvoiceEndpointTests.drop_test_schema
    login = test_invoice_endpoint.InvoiceEndpointTests.login
    payload = test_invoice_endpoint.InvoiceEndpointTests.payload
    post = test_invoice_endpoint.InvoiceEndpointTests.post

    def convert(self, invoice_id, issue_date='2026-10-01'):
        return self.client.post(
            f'/api/v1/invoices/{invoice_id}/convert',
            json={'issue_date': issue_date},
            headers={'Authorization': 'Bearer ' + self.token},
        )

    def receipt_payload(self, client_id):
        return {
            'client_id': client_id,
            'issue_date': '2026-09-30',
            'currency': 'KES',
            'items': [{'description': 'Advance', 'quantity': '1', 'unit_price': '10'}],
        }

    def test_conversion_is_available_through_the_full_invoice_workflow(self):
        invoice = self.post(self.payload()).json()['data']
        before = self.client.get(
            f"/api/v1/invoices/{invoice['id']}",
            headers={'Authorization': 'Bearer ' + self.token},
        ).json()['data']

        response = self.convert(invoice['id'])

        self.assertEqual(response.status_code, 201)
        receipt = response.json()['data']
        self.assertEqual(receipt['source_invoice_id'], invoice['id'])
        self.assertEqual(receipt['client_id'], invoice['client_id'])
        self.assertEqual(receipt['currency'], invoice['currency'])
        self.assertEqual(receipt['items'][0]['description'], invoice['items'][0]['description'])

        after = self.client.get(
            f"/api/v1/invoices/{invoice['id']}",
            headers={'Authorization': 'Bearer ' + self.token},
        ).json()['data']
        self.assertEqual(after, before)

    def test_repeated_conversion_creates_independent_receipts(self):
        invoice = self.post(self.payload()).json()['data']

        first = self.convert(invoice['id'])
        second = self.convert(invoice['id'], issue_date='2026-10-02')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        first_data = first.json()['data']
        second_data = second.json()['data']
        self.assertEqual((first_data['receipt_number'], second_data['receipt_number']),
                         ('RCT-0001', 'RCT-0002'))
        self.assertNotEqual(first_data['id'], second_data['id'])

    def test_conversion_uses_shared_receipt_number_sequence(self):
        invoice = self.post(self.payload()).json()['data']
        direct = self.client.post(
            '/api/v1/receipts',
            json=self.receipt_payload(invoice['client_id']),
            headers={'Authorization': 'Bearer ' + self.token},
        )
        self.assertEqual(direct.status_code, 201)

        converted = self.convert(invoice['id'])

        self.assertEqual(converted.status_code, 201)
        self.assertEqual(converted.json()['data']['receipt_number'], 'RCT-0002')

    def test_database_failure_rolls_back_endpoint_conversion(self):
        invoice = self.post(self.payload()).json()['data']
        self.connection.execute('''CREATE FUNCTION reject_workflow_receipt_item() RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Private workflow detail'; END; $$;
            CREATE TRIGGER reject_workflow_receipt_item BEFORE INSERT ON receipt_items
            FOR EACH ROW EXECUTE FUNCTION reject_workflow_receipt_item();''')

        response = self.convert(invoice['id'])

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error']['code'], 'INTERNAL_SERVER_ERROR')
        self.assertNotIn('Private workflow detail', response.text)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM receipts').fetchone()[0], 0)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM receipt_number_counters').fetchone()[0], 0)
        self.assertEqual(self.client.get(
            f"/api/v1/invoices/{invoice['id']}",
            headers={'Authorization': 'Bearer ' + self.token},
        ).json()['data'], invoice)
