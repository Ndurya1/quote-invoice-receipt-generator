import unittest
from uuid import UUID

from tests import test_login


class PdfTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def setUp(self):
        test_login.LoginTests.setUp(self)
        self.token = self.login().json()['data']['access_token']
        self.headers = {'Authorization': 'Bearer ' + self.token}
        client_response = self.client.post(
            '/api/v1/clients', json={'name': 'Acme Ltd', 'email': 'hello@example.com'},
            headers=self.headers,
        )
        self.assertEqual(client_response.status_code, 201, client_response.text)
        self.client_id = client_response.json()['data']['id']
        self.client.put('/api/v1/business-profile', json={
            'business_name': 'Ndurya Digital', 'email': 'billing@example.com',
            'address': 'Nairobi, Kenya', 'default_currency': 'KES',
        }, headers=self.headers)

    def quote_payload(self):
        return {
            'client_id': self.client_id, 'issue_date': '2026-09-15',
            'expiry_date': '2026-09-30', 'currency': 'KES',
            'tax_rate': '16', 'discount_type': 'FIXED', 'discount_value': '10',
            'notes': 'Thank you.', 'terms': 'Valid for 14 days.',
            'items': [{'description': 'Website work', 'quantity': '1', 'unit_price': '100'}],
        }

    def invoice_payload(self):
        return {
            'client_id': self.client_id, 'issue_date': '2026-09-15',
            'due_date': '2026-09-30', 'currency': 'KES',
            'tax_rate': '16', 'discount_type': 'FIXED', 'discount_value': '10',
            'notes': 'Invoice note.', 'terms': 'Pay promptly.',
            'items': [{'description': 'Consulting', 'quantity': '1', 'unit_price': '100'}],
        }

    def receipt_payload(self):
        return {
            'client_id': self.client_id, 'issue_date': '2026-09-15', 'currency': 'KES',
            'tax_rate': '16', 'discount_type': 'FIXED', 'discount_value': '10',
            'notes': 'Payment received.',
            'items': [{'description': 'Support', 'quantity': '1', 'unit_price': '100'}],
        }

    def create_documents(self):
        quote = self.client.post('/api/v1/quotes', json=self.quote_payload(), headers=self.headers).json()['data']
        invoice = self.client.post('/api/v1/invoices', json=self.invoice_payload(), headers=self.headers).json()['data']
        receipt = self.client.post('/api/v1/receipts', json=self.receipt_payload(), headers=self.headers).json()['data']
        return quote, invoice, receipt

    def test_owner_can_download_all_persisted_documents(self):
        quote, invoice, receipt = self.create_documents()
        for resource, document in (('quotes', quote), ('invoices', invoice), ('receipts', receipt)):
            with self.subTest(resource=resource):
                response = self.client.get(
                    f'/api/v1/{resource}/{document["id"]}/pdf?total=999999',
                    headers=self.headers,
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers['content-type'], 'application/pdf')
                self.assertEqual(response.headers['cache-control'], 'no-store')
                self.assertIn(f'filename="{document[resource[:-1] + "_number"]}.pdf"', response.headers['content-disposition'])
                self.assertIn(document[resource[:-1] + '_number'].encode(), response.content)
                self.assertIn(b'100.00', response.content)
                self.assertIn(b'Ndurya Digital', response.content)
                self.assertIn(b'Acme Ltd', response.content)

    def test_foreign_and_unauthenticated_requests_are_rejected(self):
        quote, invoice, receipt = self.create_documents()
        for resource, document in (('quotes', quote), ('invoices', invoice), ('receipts', receipt)):
            with self.subTest(resource=resource):
                response = self.client.get(f'/api/v1/{resource}/{document["id"]}/pdf')
                self.assertEqual(response.status_code, 401)
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        other_token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        other_headers = {'Authorization': 'Bearer ' + other_token}
        for resource, document in (('quotes', quote), ('invoices', invoice), ('receipts', receipt)):
            with self.subTest(resource=resource):
                response = self.client.get(
                    f'/api/v1/{resource}/{document["id"]}/pdf', headers=other_headers,
                )
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()['error']['code'], resource[:-1].upper() + '_NOT_FOUND')

    def test_malformed_ids_and_openapi_contract(self):
        for resource in ('quotes', 'invoices', 'receipts'):
            response = self.client.get(f'/api/v1/{resource}/not-a-uuid/pdf', headers=self.headers)
            self.assertEqual(response.status_code, 422)
        paths = self.client.get('/openapi.json').json()['paths']
        for resource in ('quotes', 'invoices', 'receipts'):
            operation = paths[f'/api/v1/{resource}/{{{resource[:-1]}_id}}/pdf']['get']
            self.assertEqual(operation['security'], [{'HTTPBearer': []}])
            self.assertIn('application/pdf', operation['responses']['200']['content'])

    def test_missing_documents_use_domain_not_found_errors(self):
        missing = UUID('00000000-0000-0000-0000-000000000001')
        for resource in ('quotes', 'invoices', 'receipts'):
            response = self.client.get(f'/api/v1/{resource}/{missing}/pdf', headers=self.headers)
            self.assertEqual(response.status_code, 404)
