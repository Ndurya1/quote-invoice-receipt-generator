import unittest

from fastapi.testclient import TestClient

from app.common.settings import Settings
from app.main import create_app
from tests import test_login


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Settings(environment='test'))
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def test_documented_mvp_route_map_and_methods_are_exposed(self):
        paths = self.client.get('/openapi.json').json()['paths']
        expected = {
            '/api/v1/auth/register': {'post'},
            '/api/v1/auth/login': {'post'},
            '/api/v1/auth/refresh': {'post'},
            '/api/v1/auth/me': {'get'},
            '/api/v1/business-profile': {'get', 'put'},
            '/api/v1/clients': {'get', 'post'},
            '/api/v1/clients/{client_id}': {'get', 'patch', 'delete'},
            '/api/v1/quotes': {'get', 'post'},
            '/api/v1/quotes/{quote_id}': {'get', 'patch', 'delete'},
            '/api/v1/quotes/{quote_id}/send': {'post'},
            '/api/v1/quotes/{quote_id}/accept': {'post'},
            '/api/v1/quotes/{quote_id}/reject': {'post'},
            '/api/v1/quotes/{quote_id}/convert': {'post'},
            '/api/v1/quotes/{quote_id}/pdf': {'get'},
            '/api/v1/invoices': {'get', 'post'},
            '/api/v1/invoices/{invoice_id}': {'get', 'patch', 'delete'},
            '/api/v1/invoices/{invoice_id}/send': {'post'},
            '/api/v1/invoices/{invoice_id}/mark-paid': {'post'},
            '/api/v1/invoices/{invoice_id}/cancel': {'post'},
            '/api/v1/invoices/{invoice_id}/convert': {'post'},
            '/api/v1/invoices/{invoice_id}/pdf': {'get'},
            '/api/v1/receipts': {'get', 'post'},
            '/api/v1/receipts/{receipt_id}': {'get', 'patch', 'delete'},
            '/api/v1/receipts/{receipt_id}/pdf': {'get'},
            '/api/v1/dashboard/summary': {'get'},
        }
        for path, methods in expected.items():
            with self.subTest(path=path):
                self.assertIn(path, paths)
                self.assertTrue(methods <= set(paths[path]))

    def test_pdf_routes_advertise_pdf_responses(self):
        paths = self.client.get('/openapi.json').json()['paths']
        for resource, identifier in (
            ('quotes', 'quote_id'), ('invoices', 'invoice_id'), ('receipts', 'receipt_id'),
        ):
            with self.subTest(resource=resource):
                operation = paths[f'/api/v1/{resource}/{{{identifier}}}/pdf']['get']
                self.assertIn('application/pdf', operation['responses']['200']['content'])


class ServerManagedFieldTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def setUp(self):
        test_login.LoginTests.setUp(self)
        self.token = self.login().json()['data']['access_token']
        self.headers = {'Authorization': 'Bearer ' + self.token}
        self.client_id = self.client.post(
            '/api/v1/clients', json={'name': 'Acme Ltd'}, headers=self.headers,
        ).json()['data']['id']

    def base_payload(self):
        return {
            'client_id': self.client_id, 'issue_date': '2026-09-15', 'currency': 'KES',
            'items': [{'description': 'Work', 'quantity': '1', 'unit_price': '100'}],
        }

    def test_client_server_managed_fields_are_rejected(self):
        payload = {
            'name': 'Forged', 'id': '00000000-0000-0000-0000-000000000001',
            'user_id': self.user_id, 'created_at': '2026-09-15T00:00:00Z',
            'updated_at': '2026-09-15T00:00:00Z',
        }
        response = self.client.post('/api/v1/clients', json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM clients').fetchone()[0], 1)

    def test_document_server_managed_fields_and_item_totals_are_rejected(self):
        attempts = [
            ('quotes', {
                **self.base_payload(), 'quote_number': 'QT-9999', 'user_id': self.user_id,
                'status': 'ACCEPTED', 'subtotal': '999999.00', 'total': '999999.00',
                'source_quote_id': '00000000-0000-0000-0000-000000000001',
            }),
            ('invoices', {
                **self.base_payload(), 'invoice_number': 'INV-9999', 'user_id': self.user_id,
                'status': 'PAID', 'subtotal': '999999.00', 'total': '999999.00',
                'source_quote_id': '00000000-0000-0000-0000-000000000001',
            }),
            ('receipts', {
                **self.base_payload(), 'receipt_number': 'RCT-9999', 'user_id': self.user_id,
                'subtotal': '999999.00', 'total': '999999.00',
                'source_invoice_id': '00000000-0000-0000-0000-000000000001',
            }),
        ]
        for resource, payload in attempts:
            payload['items'][0]['line_total'] = '999999.00'
            with self.subTest(resource=resource):
                response = self.client.post(f'/api/v1/{resource}', json=payload, headers=self.headers)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')
        for table in ('quotes', 'invoices', 'receipts'):
            self.assertEqual(self.connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0], 0)
