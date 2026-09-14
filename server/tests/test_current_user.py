import unittest
from datetime import datetime, timezone
from uuid import UUID, uuid4

import jwt

from app.accounts.tokens import AUDIENCE, ISSUER
from tests import test_login


class CurrentUserTests(unittest.TestCase):
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def me(self, token):
        response = self.client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer ' + token})
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def assert_unauthenticated(self, response):
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers['www-authenticate'], 'Bearer')
        self.assertEqual(response.json(), {'error': {
            'code': 'AUTHENTICATION_REQUIRED', 'message': 'Authentication is required.', 'details': {},
        }})

    def test_login_and_refreshed_access_tokens_return_only_public_fields(self):
        pair = self.login().json()['data']
        refreshed = self.client.post('/api/v1/auth/refresh', json={
            'refresh_token': pair['refresh_token'],
        }).json()['data']['access_token']
        self.connection.execute('UPDATE users SET name = %s, phone = %s WHERE id = %s',
                                ('Updated Owner', '+254700123456', UUID(self.user_id)))
        for token in (pair['access_token'], refreshed):
            response = self.me(token)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            self.assertEqual(response.json(), {'data': {
                'id': self.user_id, 'name': 'Updated Owner',
                'email': 'owner@example.com', 'phone': '+254700123456',
            }})

    def test_identity_comes_from_token_and_cannot_be_overridden(self):
        other = self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'OtherPassword123',
        }).json()['data']
        token = self.login().json()['data']['access_token']
        response = self.client.get('/api/v1/auth/me', params={'user_id': other['id']},
                                   headers={'Authorization': 'Bearer ' + token, 'X-User-Id': other['id']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['id'], self.user_id)
        other_token = self.login(email='other@example.com', password='OtherPassword123').json()['data']['access_token']
        self.assertEqual(self.me(other_token).json(), {'data': other})

    def test_missing_and_malformed_authorization(self):
        for headers in ({}, {'Authorization': 'Basic abc'}, {'Authorization': 'Bearer'},
                        {'Authorization': 'Bearer '}, {'Authorization': 'Bearer not-a-token'}):
            with self.subTest(headers=headers):
                self.assert_unauthenticated(self.client.get('/api/v1/auth/me', headers=headers))

    def test_invalid_access_tokens_are_rejected(self):
        pair = self.login().json()['data']
        claims = jwt.decode(pair['access_token'], test_login.TEST_KEY,
                            algorithms=['HS256'], issuer=ISSUER, audience=AUDIENCE)
        now = int(datetime.now(timezone.utc).timestamp())
        tokens = [pair['refresh_token']]
        for changes in ({'iat': now - 120, 'exp': now - 60}, {'iss': 'foreign'},
                        {'aud': 'foreign'}, {'sub': 'bad-uuid'}, {'sub': str(uuid4())},
                        {'jti': 123}, {'jti': None}, {'iat': now + 3600},
                        {'exp': claims['iat']}, {'exp': str(now + 3600)}):
            tokens.append(jwt.encode({**claims, **changes}, test_login.TEST_KEY, algorithm='HS256'))
        for field in claims:
            tokens.append(jwt.encode({k: v for k, v in claims.items() if k != field},
                                     test_login.TEST_KEY, algorithm='HS256'))
        tokens.append(jwt.encode(claims, 'different-signing-key-of-at-least-32-bytes', algorithm='HS256'))
        tokens.append(jwt.encode(claims, test_login.TEST_KEY * 2, algorithm='HS512'))
        for index, token in enumerate(tokens):
            with self.subTest(case=index):
                self.assert_unauthenticated(self.me(token))

    def test_deleted_user_is_unauthenticated(self):
        token = self.login().json()['data']['access_token']
        self.connection.execute('DELETE FROM users WHERE id = %s', (UUID(self.user_id),))
        self.assert_unauthenticated(self.me(token))

    def test_openapi_documents_bearer_security_and_public_response(self):
        schema = self.client.get('/openapi.json').json()
        operation = schema['paths']['/api/v1/auth/me']['get']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        self.assertEqual(schema['components']['securitySchemes']['HTTPBearer']['scheme'], 'bearer')
        self.assertEqual(set(schema['components']['schemas']['UserResponse']['properties']),
                         {'id', 'name', 'email', 'phone'})
