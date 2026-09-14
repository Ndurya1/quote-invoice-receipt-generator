import unittest
from uuid import UUID

from app.business.schemas import BusinessProfilePut
from app.business.service import upsert_profile
from tests import test_login


class BusinessProfilePutTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def put(self, payload, token=None):
        if token is None:
            token = self.login().json()['data']['access_token']
        response = self.client.put('/api/v1/business-profile', json=payload,
                                   headers={'Authorization': 'Bearer ' + token})
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_create_defaults_and_read_back(self):
        token = self.login().json()['data']['access_token']
        response = self.put({'business_name': '  Example Ltd  '}, token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        data = response.json()['data']
        self.assertEqual(data['user_id'], self.user_id)
        self.assertEqual(data['business_name'], 'Example Ltd')
        self.assertEqual(data['default_currency'], 'KES')
        UUID(data['id'])
        for field in ('logo_url', 'email', 'phone', 'address', 'tax_number'):
            self.assertIsNone(data[field])
        read = self.client.get('/api/v1/business-profile', headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(read.json(), response.json())

    def test_replacement_preserves_identity_and_resets_omitted_fields(self):
        token = self.login().json()['data']['access_token']
        payload = {'business_name': 'Example', 'logo_url': 'https://example.com/logo.png',
                   'email': 'billing@example.com', 'phone': '+254700123456', 'address': 'Nairobi',
                   'tax_number': 'TAX-123', 'default_currency': 'USD'}
        original = self.put(payload, token).json()['data']
        for field, value in payload.items():
            self.assertEqual(original[field], value)
        repeated = self.put(payload, token).json()['data']
        self.assertEqual(repeated['id'], original['id'])
        self.assertEqual(repeated['created_at'], original['created_at'])
        replaced = self.put({'business_name': 'New Name'}, token).json()['data']
        self.assertEqual(replaced['id'], original['id'])
        self.assertEqual(replaced['created_at'], original['created_at'])
        self.assertEqual(replaced['business_name'], 'New Name')
        self.assertEqual(replaced['default_currency'], 'KES')
        for field in ('logo_url', 'email', 'phone', 'address', 'tax_number'):
            self.assertIsNone(replaced[field])
        self.assertEqual(self.connection.execute('SELECT count(*) FROM business_profiles').fetchone()[0], 1)

    def test_invalid_input_does_not_change_existing_profile(self):
        token = self.login().json()['data']['access_token']
        original = self.put({'business_name': 'Original'}, token).json()
        invalid = [{}, {'business_name': ' '}, {'business_name': 'x' * 161},
                   {'business_name': None}]
        for field, value in (('default_currency', 'kes'), ('default_currency', 'KES\n'),
                             ('default_currency', None), ('default_currency', 123),
                             ('email', 'invalid'), ('logo_url', 'javascript:alert(1)'),
                             ('phone', '1' * 31), ('tax_number', 'x' * 101)):
            invalid.append({'business_name': 'Changed', field: value})
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.put(payload, token)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')
        read = self.client.get('/api/v1/business-profile', headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(read.json(), original)

    def test_ownership_and_server_fields_cannot_be_overridden(self):
        other = self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'OtherPassword123',
        }).json()['data']
        other_token = self.login(email='other@example.com', password='OtherPassword123').json()['data']['access_token']
        other_profile = self.put({'business_name': 'Other Business'}, other_token).json()
        token = self.login().json()['data']['access_token']
        for field, value in (('user_id', other['id']), ('id', other_profile['data']['id']),
                             ('created_at', '2020-01-01T00:00:00Z'), ('updated_at', '2020-01-01T00:00:00Z')):
            self.assertEqual(self.put({'business_name': 'Attack', field: value}, token).status_code, 422)
        response = self.client.put('/api/v1/business-profile', params={'user_id': other['id']},
                                   headers={'Authorization': 'Bearer ' + token},
                                   json={'business_name': 'Own Business'})
        self.assertEqual(response.json()['data']['user_id'], self.user_id)
        read = self.client.get('/api/v1/business-profile', headers={'Authorization': 'Bearer ' + other_token})
        self.assertEqual(read.json(), other_profile)

    def test_unauthenticated_writes_are_rejected(self):
        pair = self.login().json()['data']
        for headers in ({}, {'Authorization': 'Bearer invalid'},
                        {'Authorization': 'Bearer ' + pair['refresh_token']}):
            response = self.client.put('/api/v1/business-profile', headers=headers,
                                       json={'business_name': 'Example'})
            self.assertEqual(response.status_code, 401)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM business_profiles').fetchone()[0], 0)

    def test_service_respects_enclosing_transaction_rollback(self):
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                upsert_profile(self.connection, user_id=UUID(self.user_id),
                               payload=BusinessProfilePut(business_name='Example'))
                raise RuntimeError('abort')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM business_profiles').fetchone()[0], 0)
