import unittest
from uuid import UUID

from tests import test_login


class DashboardTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def auth(self):
        return {'Authorization': 'Bearer ' + self.token}

    def create_client(self, name='Acme Ltd'):
        return self.client.post('/api/v1/clients', json={'name': name}, headers=self.auth()).json()['data']['id']

    def quote_payload(self, client_id, **changes):
        return {
            'client_id': client_id,
            'issue_date': '2026-09-15',
            'currency': 'KES',
            'items': [{'description': 'Work', 'quantity': '1', 'unit_price': '100'}],
            **changes,
        }

    def invoice_payload(self, client_id, **changes):
        return {
            'client_id': client_id,
            'issue_date': '2026-09-15',
            'currency': 'KES',
            'items': [{'description': 'Work', 'quantity': '1', 'unit_price': '100'}],
            **changes,
        }

    def receipt_payload(self, client_id, **changes):
        return {
            'client_id': client_id,
            'issue_date': '2026-09-15',
            'currency': 'KES',
            'items': [{'description': 'Work', 'quantity': '1', 'unit_price': '100'}],
            **changes,
        }

    def get_summary(self, headers=None):
        return self.client.get(
            '/api/v1/dashboard/summary',
            headers=self.auth() if headers is None else headers,
        )

    def setUp(self):
        test_login.LoginTests.setUp(self)
        self.token = self.login().json()['data']['access_token']

    def test_empty_account_returns_zero_summary(self):
        response = self.get_summary()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(response.json(), {
            'data': {
                'quotes': {'total': 0, 'draft': 0, 'sent': 0, 'accepted': 0},
                'invoices': {'total': 0, 'draft': 0, 'sent': 0, 'paid': 0, 'overdue': 0},
                'receipts': {'total': 0},
                'recent_documents': [],
            },
        })

    def test_counts_and_recent_documents_are_owner_scoped(self):
        client_id = self.create_client()
        quote = self.client.post('/api/v1/quotes', json=self.quote_payload(client_id), headers=self.auth()).json()['data']
        self.client.post('/api/v1/quotes/' + quote['id'] + '/send', headers=self.auth())
        accepted = self.client.post('/api/v1/quotes', json=self.quote_payload(client_id), headers=self.auth()).json()['data']
        self.client.post('/api/v1/quotes/' + accepted['id'] + '/accept', headers=self.auth())

        invoice = self.client.post('/api/v1/invoices', json=self.invoice_payload(client_id), headers=self.auth()).json()['data']
        self.client.post('/api/v1/invoices/' + invoice['id'] + '/send', headers=self.auth())
        paid = self.client.post('/api/v1/invoices', json=self.invoice_payload(client_id), headers=self.auth()).json()['data']
        self.client.post('/api/v1/invoices/' + paid['id'] + '/send', headers=self.auth())
        self.client.post('/api/v1/invoices/' + paid['id'] + '/mark-paid', headers=self.auth())
        overdue = self.client.post('/api/v1/invoices', json=self.invoice_payload(client_id), headers=self.auth()).json()['data']
        self.connection.execute('UPDATE invoices SET status = %s WHERE id = %s', ('OVERDUE', UUID(overdue['id'])))

        self.client.post('/api/v1/receipts', json=self.receipt_payload(client_id), headers=self.auth())
        response = self.get_summary()
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['quotes'], {'total': 2, 'draft': 0, 'sent': 1, 'accepted': 1})
        self.assertEqual(data['invoices'], {'total': 3, 'draft': 0, 'sent': 1, 'paid': 1, 'overdue': 1})
        self.assertEqual(data['receipts'], {'total': 1})
        self.assertEqual(len(data['recent_documents']), 5)
        self.assertEqual({row['type'] for row in data['recent_documents']}, {'quote', 'invoice', 'receipt'})

        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        other_token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        other_client = self.client.post('/api/v1/clients', json={'name': 'Other Client'},
                                        headers={'Authorization': 'Bearer ' + other_token}).json()['data']['id']
        self.client.post('/api/v1/quotes', json=self.quote_payload(other_client),
                         headers={'Authorization': 'Bearer ' + other_token})
        self.assertEqual(self.get_summary().json()['data']['quotes']['total'], 2)

    def test_authentication_and_openapi_contract(self):
        for headers in ({}, {'Authorization': 'Bearer invalid'}):
            response = self.get_summary(headers)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()['error']['code'], 'AUTHENTICATION_REQUIRED')
        operation = self.client.get('/openapi.json').json()['paths']['/api/v1/dashboard/summary']['get']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
