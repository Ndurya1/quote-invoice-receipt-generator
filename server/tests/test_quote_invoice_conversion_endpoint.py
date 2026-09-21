import unittest
from uuid import UUID, uuid4

from tests import test_quote_endpoint


class QuoteInvoiceConversionEndpointTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_endpoint.QuoteEndpointTests.setUpClass.__func__)
    setUp = test_quote_endpoint.QuoteEndpointTests.setUp
    drop_test_schema = test_quote_endpoint.QuoteEndpointTests.drop_test_schema
    login = test_quote_endpoint.QuoteEndpointTests.login
    payload = test_quote_endpoint.QuoteEndpointTests.payload
    post = test_quote_endpoint.QuoteEndpointTests.post

    def convert(self, quote_id, payload=None, token=None):
        return self.client.post(
            f'/api/v1/quotes/{quote_id}/convert',
            json=payload or {'issue_date': '2026-09-20', 'due_date': '2026-10-01'},
            headers={'Authorization': 'Bearer ' + (token or self.token)},
        )

    def accept(self, quote_id):
        return self.client.post(
            f'/api/v1/quotes/{quote_id}/accept',
            headers={'Authorization': 'Bearer ' + self.token},
        )

    def test_accepted_quote_conversion_returns_created_invoice(self):
        quote = self.post(self.payload()).json()['data']
        self.assertEqual(self.accept(quote['id']).status_code, 200)
        response = self.convert(quote['id'])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        data = response.json()['data']
        self.assertEqual(data['source_quote_id'], quote['id'])
        self.assertEqual(data['status'], 'DRAFT')
        self.assertEqual(data['invoice_number'], 'INV-0001')
        self.assertEqual(len(data['items']), len(quote['items']))

    def test_request_validation_and_authentication(self):
        quote = self.post(self.payload()).json()['data']
        invalid_payloads = [
            {'issue_date': '2026-09-20', 'due_date': '2026-09-19'},
            {'issue_date': '2026-09-20', 'unexpected': 'forged'},
            {'due_date': '2026-10-01'},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.convert(quote['id'], payload)
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.post(
            f"/api/v1/quotes/{quote['id']}/convert", json={'issue_date': '2026-09-20'},
        ).status_code, 401)

    def test_foreign_and_missing_quotes_are_not_found(self):
        quote = self.post(self.payload()).json()['data']
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        other_token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        foreign = self.convert(quote['id'], token=other_token)
        missing = self.convert(str(uuid4()), token=other_token)
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json(), missing.json())
        self.assertEqual(foreign.json()['error']['code'], 'QUOTE_NOT_FOUND')

    def test_openapi_documents_conversion_contract(self):
        operation = self.client.get('/openapi.json').json()['paths'][
            '/api/v1/quotes/{quote_id}/convert']['post']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        self.assertIn('201', operation['responses'])
        self.assertIn('requestBody', operation)
