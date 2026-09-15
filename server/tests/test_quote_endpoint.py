import unittest
from uuid import UUID, uuid4

from tests import test_login


class QuoteEndpointTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def setUp(self):
        test_login.LoginTests.setUp(self)
        self.token = self.login().json()['data']['access_token']
        self.client_id = self.client.post('/api/v1/clients', json={'name': 'Acme'},
                                          headers={'Authorization': 'Bearer ' + self.token}).json()['data']['id']

    def payload(self, **changes):
        return {'client_id': self.client_id, 'issue_date': '2026-09-15', 'currency': 'KES',
                'tax_rate': '16', 'discount_type': 'FIXED', 'discount_value': '10',
                'items': [{'description': 'Work', 'quantity': '1.25', 'unit_price': '80'}], **changes}

    def post(self, payload):
        response = self.client.post('/api/v1/quotes', json=payload,
                                    headers={'Authorization': 'Bearer ' + self.token})
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_creation_returns_persisted_draft_number_totals_and_items(self):
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(set(response.json()), {'data'})
        data = response.json()['data']
        self.assertEqual(data['quote_number'], 'QT-0001')
        self.assertEqual(data['status'], 'DRAFT')
        self.assertEqual(data['user_id'], self.user_id)
        self.assertEqual(data['client_id'], self.client_id)
        self.assertEqual([data[k] for k in ('subtotal', 'tax_rate', 'tax_amount', 'discount_amount', 'total')],
                         ['100.00', '16.000', '16.00', '10.00', '106.00'])
        self.assertEqual(len(data['items']), 1)
        item = data['items'][0]
        self.assertEqual(item['quote_id'], data['id'])
        self.assertEqual(item['line_total'], '100.00')
        self.assertEqual(self.connection.execute('SELECT quote_number FROM quotes WHERE id = %s',
                                                (UUID(data['id']),)).fetchone()[0], 'QT-0001')
        self.assertEqual(self.post(self.payload()).json()['data']['quote_number'], 'QT-0002')

    def test_invalid_and_forged_fields_never_create_rows(self):
        payloads = [self.payload(items=[]), self.payload(currency='kes'), self.payload(expiry_date='2026-09-14')]
        payloads += [self.payload(**{field: 'forged'}) for field in
                     ('user_id', 'quote_number', 'subtotal', 'tax_amount', 'discount_amount', 'total', 'status')]
        payloads.append(self.payload(items=[{'description': 'Work', 'quantity': '1', 'unit_price': '1', 'line_total': '999'}]))
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.post(payload)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')
        response = self.post(self.payload(discount_value='1000'))
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['error']['code'], 'INVALID_DISCOUNT')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quotes').fetchone()[0], 0)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quote_number_counters').fetchone()[0], 0)

    def test_foreign_and_missing_clients_rejected(self):
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'OtherPassword123'})
        other_token = self.login(email='other@example.com', password='OtherPassword123').json()['data']['access_token']
        foreign = self.client.post('/api/v1/clients', json={'name': 'Foreign'},
                                   headers={'Authorization': 'Bearer ' + other_token}).json()['data']['id']
        for client_id in (foreign, str(uuid4())):
            response = self.post(self.payload(client_id=client_id))
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()['error']['code'], 'CLIENT_NOT_FOUND')

    def test_authentication_required(self):
        refresh = self.login().json()['data']['refresh_token']
        for headers in ({}, {'Authorization': 'Bearer invalid'}, {'Authorization': 'Bearer ' + refresh}):
            response = self.client.post('/api/v1/quotes', json=self.payload(), headers=headers)
            self.assertEqual(response.status_code, 401)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quotes').fetchone()[0], 0)

    def test_item_database_failure_rolls_back_and_returns_safe_error(self):
        self.connection.execute('''CREATE FUNCTION reject_endpoint_item() RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Private database detail'; END; $$;
            CREATE TRIGGER reject_endpoint_item BEFORE INSERT ON quote_items
            FOR EACH ROW EXECUTE FUNCTION reject_endpoint_item();''')
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error']['code'], 'INTERNAL_SERVER_ERROR')
        self.assertNotIn('Private database detail', response.text)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quotes').fetchone()[0], 0)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quote_number_counters').fetchone()[0], 0)

    def test_openapi_documents_authenticated_creation(self):
        path = self.client.get('/openapi.json').json()['paths']['/api/v1/quotes']
        self.assertEqual(set(path), {'post'})
        self.assertEqual(path['post']['security'], [{'HTTPBearer': []}])
        self.assertIn('201', path['post']['responses'])
