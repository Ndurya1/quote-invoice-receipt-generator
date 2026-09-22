import unittest

from fastapi.testclient import TestClient

from app.common.settings import Settings
from app.main import create_app


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
