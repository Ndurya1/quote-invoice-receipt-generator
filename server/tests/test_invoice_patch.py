import unittest
from uuid import UUID, uuid4

from tests import test_invoice_endpoint


class InvoicePatchTests(unittest.TestCase):
    setUpClass = classmethod(test_invoice_endpoint.InvoiceEndpointTests.setUpClass.__func__)
    setUp = test_invoice_endpoint.InvoiceEndpointTests.setUp
    drop_test_schema = test_invoice_endpoint.InvoiceEndpointTests.drop_test_schema
    login = test_invoice_endpoint.InvoiceEndpointTests.login
    payload = test_invoice_endpoint.InvoiceEndpointTests.payload
    post = test_invoice_endpoint.InvoiceEndpointTests.post

    def setUp(self):
        test_invoice_endpoint.InvoiceEndpointTests.setUp(self)
        self.invoice = self.post(self.payload()).json()['data']
        self.url = '/api/v1/invoices/' + self.invoice['id']

    def patch(self, changes, url=None):
        return self.client.patch(url or self.url, json=changes,
                                 headers={'Authorization': 'Bearer ' + self.token})

    def get(self):
        return self.client.get(self.url, headers={'Authorization': 'Bearer ' + self.token}).json()['data']

    def test_partial_recalculation_replacement_and_readback(self):
        response = self.patch({'tax_rate': '10', 'notes': 'Updated'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        data = response.json()['data']
        self.assertEqual(data['total'], '100.00')
        self.assertEqual(data['items'], self.invoice['items'])
        self.assertEqual(data['notes'], 'Updated')
        self.assertEqual(data, self.get())
        changed = self.patch({'items': [{'description': 'New', 'quantity': '2', 'unit_price': '100'}]}).json()['data']
        self.assertEqual(changed['total'], '210.00')
        self.assertEqual(changed, self.get())
        self.assertNotEqual(changed['items'][0]['id'], self.invoice['items'][0]['id'])

    def test_clear_fields_and_empty_patch(self):
        self.assertEqual(self.patch({}).json()['data'], self.invoice)
        new_client = self.client.post('/api/v1/clients', json={'name': 'New'},
                                      headers={'Authorization': 'Bearer ' + self.token}).json()['data']['id']
        changed = self.patch({'client_id': new_client, 'due_date': None, 'notes': None,
                              'terms': None, 'currency': 'USD'})
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()['data']['client_id'], new_client)
        self.assertIsNone(changed.json()['data']['due_date'])
        self.assertEqual(changed.json()['data']['invoice_number'], self.invoice['invoice_number'])

    def test_invalid_and_server_managed_values_do_not_write(self):
        invalid = [{'due_date': '2026-09-14'}, {'discount_type': 'NONE'}, {'items': []},
                   {'tax_rate': None}, {'currency': 'kes'}, {'discount_value': '999'}]
        invalid += [{field: 'forged'} for field in ('user_id', 'invoice_number', 'status', 'subtotal',
                    'tax_amount', 'discount_amount', 'total', 'created_at', 'updated_at', 'id', 'source_quote_id')]
        invalid.append({'items': [{'description': 'x', 'quantity': '1', 'unit_price': '20', 'line_total': '999'}]})
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.patch(payload)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn('input', response.text)
                self.assertEqual(self.get(), self.invoice)

    def test_auth_foreign_invoice_and_foreign_client(self):
        self.assertEqual(self.client.patch(self.url, json={}).status_code, 401)
        self.assertEqual(self.patch({}, '/api/v1/invoices/bad').status_code, 422)
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        other_token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        foreign_client = self.client.post('/api/v1/clients', json={'name': 'Foreign'},
                                          headers={'Authorization': 'Bearer ' + other_token}).json()['data']['id']
        response = self.patch({'client_id': foreign_client})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error']['code'], 'CLIENT_NOT_FOUND')
        self.assertEqual(self.get(), self.invoice)
        self.token = other_token
        foreign = self.patch({'notes': 'Foreign change'})
        missing = self.patch({}, '/api/v1/invoices/' + str(uuid4()))
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json(), missing.json())

    def test_status_conflict_and_openapi(self):
        self.connection.execute("UPDATE invoices SET status = 'PAID' WHERE id = %s", (UUID(self.invoice['id']),))
        response = self.patch({'notes': 'Changed'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'INVALID_INVOICE_STATUS')
        operation = self.client.get('/openapi.json').json()['paths']['/api/v1/invoices/{invoice_id}']['patch']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
