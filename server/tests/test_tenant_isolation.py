import unittest
from uuid import UUID

from tests import test_login


class TenantIsolationTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def setUp(self):
        test_login.LoginTests.setUp(self)
        self.owner_token = self.login().json()['data']['access_token']
        self.owner_headers = {'Authorization': 'Bearer ' + self.owner_token}
        other = self.client.post('/api/v1/auth/register', json={
            'name': 'Other User', 'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']
        self.other_token = self.client.post('/api/v1/auth/login', json={
            'email': other['email'], 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        self.other_headers = {'Authorization': 'Bearer ' + self.other_token}
        self.owner_client_id = self.create_client(self.owner_headers, 'Owner Client')
        self.other_client_id = self.create_client(self.other_headers, 'Other Client')

    def create_client(self, headers, name):
        response = self.client.post('/api/v1/clients', json={'name': name}, headers=headers)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['data']['id']

    def quote_payload(self, client_id):
        return {
            'client_id': client_id, 'issue_date': '2026-09-15', 'currency': 'KES',
            'items': [{'description': 'Work', 'quantity': '1', 'unit_price': '100'}],
        }

    def invoice_payload(self, client_id):
        return {
            'client_id': client_id, 'issue_date': '2026-09-15', 'currency': 'KES',
            'items': [{'description': 'Work', 'quantity': '1', 'unit_price': '100'}],
        }

    def receipt_payload(self, client_id):
        return {
            'client_id': client_id, 'issue_date': '2026-09-15', 'currency': 'KES',
            'items': [{'description': 'Work', 'quantity': '1', 'unit_price': '100'}],
        }

    def create_quote(self, headers=None, client_id=None):
        response = self.client.post(
            '/api/v1/quotes', json=self.quote_payload(client_id or self.owner_client_id),
            headers=headers or self.owner_headers,
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['data']

    def create_invoice(self, headers=None, client_id=None):
        response = self.client.post(
            '/api/v1/invoices', json=self.invoice_payload(client_id or self.owner_client_id),
            headers=headers or self.owner_headers,
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['data']

    def create_receipt(self, headers=None, client_id=None):
        response = self.client.post(
            '/api/v1/receipts', json=self.receipt_payload(client_id or self.owner_client_id),
            headers=headers or self.owner_headers,
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['data']

    def test_foreign_client_read_patch_delete_are_not_visible(self):
        client_id = self.owner_client_id
        read = self.client.get(f'/api/v1/clients/{client_id}', headers=self.other_headers)
        self.assertEqual(read.status_code, 404)
        self.assertEqual(read.json()['error']['code'], 'CLIENT_NOT_FOUND')

        patch = self.client.patch(
            f'/api/v1/clients/{client_id}', json={'name': 'Hijacked'}, headers=self.other_headers,
        )
        self.assertEqual(patch.status_code, 404)
        self.assertEqual(patch.json()['error']['code'], 'CLIENT_NOT_FOUND')

        delete = self.client.delete(f'/api/v1/clients/{client_id}', headers=self.other_headers)
        self.assertEqual(delete.status_code, 404)
        self.assertEqual(delete.json()['error']['code'], 'CLIENT_NOT_FOUND')

        owner_read = self.client.get(f'/api/v1/clients/{client_id}', headers=self.owner_headers)
        self.assertEqual(owner_read.status_code, 200)
        self.assertEqual(owner_read.json()['data']['name'], 'Owner Client')
