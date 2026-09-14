import unittest
from uuid import UUID

from tests import test_login


class BusinessProfileReadTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def insert_profile(self, user_id, name='Example Business'):
        return self.connection.execute(
            'INSERT INTO business_profiles (user_id, business_name) VALUES (%s, %s) RETURNING id',
            (UUID(user_id), name),
        ).fetchone()[0]

    def read(self, token, **kwargs):
        response = self.client.get('/api/v1/business-profile',
                                   headers={'Authorization': 'Bearer ' + token}, **kwargs)
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_returns_persisted_profile_with_defaults_and_current_values(self):
        profile_id = self.insert_profile(self.user_id)
        token = self.login().json()['data']['access_token']
        response = self.read(token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(set(response.json()), {'data'})
        data = response.json()['data']
        self.assertEqual(set(data), {'id', 'user_id', 'business_name', 'logo_url', 'email',
                                    'phone', 'address', 'tax_number', 'default_currency',
                                    'created_at', 'updated_at'})
        self.assertEqual(data['id'], str(profile_id))
        self.assertEqual(data['user_id'], self.user_id)
        self.assertEqual(data['business_name'], 'Example Business')
        self.assertEqual(data['default_currency'], 'KES')
        for field in ('logo_url', 'email', 'phone', 'address', 'tax_number'):
            self.assertIsNone(data[field])
        self.assertEqual(data['created_at'], data['updated_at'])
        self.connection.execute(
            'UPDATE business_profiles SET address = %s, email = %s WHERE id = %s',
            ('Nairobi', 'billing@example.com', profile_id),
        )
        updated = self.read(token).json()['data']
        self.assertEqual(updated['address'], 'Nairobi')
        self.assertEqual(updated['email'], 'billing@example.com')

    def test_missing_profile_returns_404_without_creating_one(self):
        token = self.login().json()['data']['access_token']
        response = self.read(token)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': {
            'code': 'BUSINESS_PROFILE_NOT_FOUND', 'message': 'Business profile not found.', 'details': {},
        }})
        self.assertEqual(self.connection.execute('SELECT count(*) FROM business_profiles').fetchone()[0], 0)

    def test_foreign_profile_is_never_returned_even_with_caller_user_id(self):
        other = self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'OtherPassword123',
        }).json()['data']
        other_profile = self.insert_profile(other['id'], 'Other Business')
        token = self.login().json()['data']['access_token']
        self.assertEqual(self.read(token, params={'user_id': other['id']}).status_code, 404)
        own_profile = self.insert_profile(self.user_id)
        response = self.read(token, params={'user_id': other['id'], 'id': str(other_profile)})
        self.assertEqual(response.json()['data']['id'], str(own_profile))
        other_token = self.login(email='other@example.com', password='OtherPassword123').json()['data']['access_token']
        self.assertEqual(self.read(other_token).json()['data']['id'], str(other_profile))

    def test_missing_invalid_and_refresh_credentials_are_rejected(self):
        pair = self.login().json()['data']
        for headers in ({}, {'Authorization': 'Basic abc'}, {'Authorization': 'Bearer invalid'},
                        {'Authorization': 'Bearer ' + pair['refresh_token']}):
            response = self.client.get('/api/v1/business-profile', headers=headers)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()['error']['code'], 'AUTHENTICATION_REQUIRED')
            self.assertEqual(response.headers['www-authenticate'], 'Bearer')

    def test_deleted_user_cannot_read_profile(self):
        token = self.login().json()['data']['access_token']
        self.connection.execute('DELETE FROM users WHERE id = %s', (UUID(self.user_id),))
        self.assertEqual(self.read(token).status_code, 401)

    def test_openapi_declares_authenticated_get_only(self):
        path = self.client.get('/openapi.json').json()['paths']['/api/v1/business-profile']
        self.assertEqual(set(path), {'get'})
        self.assertEqual(path['get']['security'], [{'HTTPBearer': []}])
        self.assertIn('200', path['get']['responses'])
