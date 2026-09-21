import unittest
from uuid import UUID, uuid4

from tests import test_quote_queries


class QuotePatchTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_queries.QuoteQueryTests.setUpClass.__func__)
    drop_test_schema = test_quote_queries.QuoteQueryTests.drop_test_schema
    login = test_quote_queries.QuoteQueryTests.login
    payload = test_quote_queries.QuoteQueryTests.payload
    post = test_quote_queries.QuoteQueryTests.post

    def setUp(self):
        test_quote_queries.QuoteQueryTests.setUp(self)
        self.quote = self.post(self.payload(expiry_date='2026-09-30')).json()['data']
        self.url = '/api/v1/quotes/' + self.quote['id']

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
        self.assertEqual(data['items'], self.quote['items'])
        self.assertEqual(data['notes'], 'Updated')
        self.assertEqual(data, self.get())
        changed = self.patch({'items': [{'description': 'New', 'quantity': '2', 'unit_price': '100'}]}).json()['data']
        self.assertEqual(changed['total'], '210.00')
        self.assertEqual(changed, self.get())
        self.assertNotEqual(changed['items'][0]['id'], self.quote['items'][0]['id'])
        self.assertTrue(all(connection.closed for connection in self.request_connections))

    def test_clear_fields_change_client_and_empty_patch(self):
        self.assertEqual(self.patch({}).json()['data'], self.quote)
        new_client = self.client.post('/api/v1/clients', json={'name': 'New'},
                                     headers={'Authorization': 'Bearer ' + self.token}).json()['data']['id']
        changed = self.patch({'client_id': new_client, 'expiry_date': None, 'notes': None,
                              'terms': None, 'currency': 'USD', 'issue_date': '2026-10-01'}).json()['data']
        self.assertEqual(changed['client_id'], new_client)
        self.assertEqual(changed['currency'], 'USD')
        self.assertIsNone(changed['expiry_date'])
        self.assertEqual(changed['quote_number'], self.quote['quote_number'])

    def test_invalid_and_server_managed_values_do_not_write(self):
        invalid = [{'issue_date': '2026-10-01'}, {'discount_type': 'NONE'}, {'items': []},
                   {'tax_rate': None}, {'currency': 'kes'}, {'discount_value': '999'}]
        invalid += [{field: 'forged'} for field in ('user_id', 'quote_number', 'status', 'subtotal',
                    'tax_amount', 'discount_amount', 'total', 'created_at', 'updated_at', 'id')]
        invalid.append({'items': [{'description': 'x', 'quantity': '1', 'unit_price': '20', 'line_total': '999'}]})
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.patch(payload)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn('input', response.text)
                self.assertEqual(self.get(), self.quote)

    def test_auth_foreign_quote_and_foreign_client(self):
        self.assertEqual(self.client.patch(self.url, json={}).status_code, 401)
        self.assertEqual(self.patch({}, '/api/v1/quotes/bad').status_code, 422)
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
        self.assertEqual(self.get(), self.quote)
        self.token = other_token
        foreign = self.patch({'notes': 'Foreign change'})
        missing = self.patch({}, '/api/v1/quotes/' + str(uuid4()))
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json(), missing.json())

    def test_status_conflict_and_openapi(self):
        self.connection.execute("UPDATE quotes SET status = 'CONVERTED' WHERE id = %s", (UUID(self.quote['id']),))
        response = self.patch({'notes': 'Changed'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'INVALID_QUOTE_STATUS')
        operation = self.client.get('/openapi.json').json()['paths']['/api/v1/quotes/{quote_id}']['patch']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])

    def test_database_failure_returns_generic_error_and_rolls_back(self):
        self.connection.execute('''CREATE FUNCTION reject_patch_item() RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Private persistence detail'; END; $$;
            CREATE TRIGGER reject_patch_item BEFORE INSERT ON quote_items
            FOR EACH ROW EXECUTE FUNCTION reject_patch_item();''')
        response = self.patch({'notes': 'Changed', 'items': [{'description': 'New', 'quantity': '1', 'unit_price': '200'}]})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error']['code'], 'INTERNAL_SERVER_ERROR')
        self.assertNotIn('Private persistence detail', response.text)
        self.assertEqual(self.get(), self.quote)
