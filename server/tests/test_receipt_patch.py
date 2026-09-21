import unittest
from uuid import UUID, uuid4

from tests import test_receipt_endpoint


class ReceiptPatchTests(unittest.TestCase):
    setUpClass = classmethod(test_receipt_endpoint.ReceiptEndpointTests.setUpClass.__func__)
    setUp = test_receipt_endpoint.ReceiptEndpointTests.setUp
    drop_test_schema = test_receipt_endpoint.ReceiptEndpointTests.drop_test_schema
    login = test_receipt_endpoint.ReceiptEndpointTests.login
    payload = test_receipt_endpoint.ReceiptEndpointTests.payload
    post = test_receipt_endpoint.ReceiptEndpointTests.post

    def setUp(self):
        test_receipt_endpoint.ReceiptEndpointTests.setUp(self)
        self.receipt = self.post(self.payload()).json()['data']
        self.url = '/api/v1/receipts/' + self.receipt['id']

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
        self.assertEqual(data['items'], self.receipt['items'])
        self.assertEqual(data['notes'], 'Updated')
        self.assertEqual(data, self.get())
        changed = self.patch({'items': [{'description': 'New', 'quantity': '2', 'unit_price': '100'}]}).json()['data']
        self.assertEqual(changed['total'], '210.00')
        self.assertEqual(changed, self.get())
        self.assertNotEqual(changed['items'][0]['id'], self.receipt['items'][0]['id'])

    def test_clear_fields_and_empty_patch(self):
        self.assertEqual(self.patch({}).json()['data'], self.receipt)
        new_client = self.client.post('/api/v1/clients', json={'name': 'New'},
                                      headers={'Authorization': 'Bearer ' + self.token}).json()['data']['id']
        changed = self.patch({'client_id': new_client, 'notes': None, 'currency': 'USD'})
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()['data']['client_id'], new_client)
        self.assertIsNone(changed.json()['data']['notes'])
        self.assertEqual(changed.json()['data']['receipt_number'], self.receipt['receipt_number'])

    def test_invalid_and_server_managed_values_do_not_write(self):
        invalid = [{'discount_type': 'NONE'}, {'items': []}, {'tax_rate': None},
                   {'currency': 'kes'}, {'discount_value': '999'}]
        invalid += [{field: 'forged'} for field in ('user_id', 'receipt_number', 'source_invoice_id',
                    'subtotal', 'tax_amount', 'discount_amount', 'total', 'created_at', 'updated_at', 'id')]
        invalid.append({'items': [{'description': 'x', 'quantity': '1', 'unit_price': '20', 'line_total': '999'}]})
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.patch(payload)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn('input', response.text)
                self.assertEqual(self.get(), self.receipt)

    def test_auth_foreign_receipt_and_foreign_client(self):
        self.assertEqual(self.client.patch(self.url, json={}).status_code, 401)
        self.assertEqual(self.patch({}, '/api/v1/receipts/bad').status_code, 422)
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
        self.assertEqual(self.get(), self.receipt)
        self.token = other_token
        foreign = self.patch({'notes': 'Foreign change'})
        missing = self.patch({}, '/api/v1/receipts/' + str(uuid4()))
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json(), missing.json())

    def test_invoice_link_conflict_and_openapi(self):
        invoice_id = self.connection.execute(
            "INSERT INTO invoices (user_id, client_id, invoice_number, issue_date, currency, subtotal, total) "
            "VALUES (%s, %s, 'INV-0001', '2026-09-15', 'KES', 100, 100) RETURNING id",
            (UUID(self.user_id), UUID(self.client_id)),
        ).fetchone()[0]
        self.connection.execute('UPDATE receipts SET source_invoice_id = %s WHERE id = %s',
                                (invoice_id, UUID(self.receipt['id'])))
        response = self.patch({'notes': 'Changed'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'INVALID_RECEIPT_STATUS')
        operation = self.client.get('/openapi.json').json()['paths']['/api/v1/receipts/{receipt_id}']['patch']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
