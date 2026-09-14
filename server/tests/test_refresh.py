import unittest
from datetime import datetime, timezone
from uuid import UUID

import jwt

from app.accounts.tokens import AUDIENCE, ISSUER
from tests import test_login


class RefreshTests(unittest.TestCase):
    # Reuse the isolated PostgreSQL fixture without inheriting login test cases.
    setUpClass = classmethod(test_login.LoginTests.setUpClass.__func__)
    setUp = test_login.LoginTests.setUp
    drop_test_schema = test_login.LoginTests.drop_test_schema
    login = test_login.LoginTests.login

    def refresh(self, token):
        response = self.client.post('/api/v1/auth/refresh', json={'refresh_token': token})
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_login_refresh_returns_new_access_token_and_allows_reuse(self):
        pair = self.login().json()['data']
        issued = []
        for _ in range(2):
            response = self.refresh(pair['refresh_token'])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            self.assertEqual(response.headers['pragma'], 'no-cache')
            self.assertEqual(set(response.json()), {'data'})
            data = response.json()['data']
            self.assertEqual(set(data), {'access_token', 'token_type'})
            self.assertEqual(data['token_type'], 'bearer')
            claims = jwt.decode(data['access_token'], test_login.TEST_KEY,
                                algorithms=['HS256'], issuer=ISSUER, audience=AUDIENCE)
            self.assertEqual(claims['sub'], self.user_id)
            self.assertEqual(claims['type'], 'access')
            self.assertEqual(claims['exp'] - claims['iat'], 900)
            issued.append(data['access_token'])
        self.assertEqual(len(set([pair['access_token'], *issued])), 3)

    def test_invalid_tokens_have_same_safe_error(self):
        pair = self.login().json()['data']
        claims = jwt.decode(pair['refresh_token'], test_login.TEST_KEY,
                            algorithms=['HS256'], issuer=ISSUER, audience=AUDIENCE)
        now = int(datetime.now(timezone.utc).timestamp())
        tokens = ['not-a-jwt', pair['access_token']]
        for changes in ({'iat': now - 120, 'exp': now - 60},
                        {'iss': 'foreign'}, {'aud': 'foreign'},
                        {'sub': 'invalid-uuid'}, {'jti': 'invalid-uuid'},
                        {'iat': now + 3600}, {'exp': claims['iat']},
                        {'exp': str(now + 3600)}):
            tokens.append(jwt.encode({**claims, **changes}, test_login.TEST_KEY, algorithm='HS256'))
        for field in claims:
            tokens.append(jwt.encode({k: v for k, v in claims.items() if k != field},
                                     test_login.TEST_KEY, algorithm='HS256'))
        tokens.append(jwt.encode(claims, 'different-test-key-at-least-32-bytes', algorithm='HS256'))
        tokens.append(jwt.encode(claims, test_login.TEST_KEY * 2, algorithm='HS512'))
        for index, token in enumerate(tokens):
            with self.subTest(case=index):
                response = self.refresh(token)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.headers['www-authenticate'], 'Bearer')
                self.assertEqual(response.json(), {'error': {
                    'code': 'INVALID_REFRESH_TOKEN',
                    'message': 'The refresh token is invalid or expired.', 'details': {},
                }})

    def test_deleted_user_cannot_refresh(self):
        token = self.login().json()['data']['refresh_token']
        self.connection.execute('DELETE FROM users WHERE id = %s', (UUID(self.user_id),))
        self.assertEqual(self.refresh(token).status_code, 401)

    def test_missing_or_malformed_request_returns_validation_error(self):
        for payload in ({}, {'refresh_token': ''}, {'refresh_token': None},
                        {'refresh_token': 123}, {'refresh_token': {'secret': 'hidden'}}):
            with self.subTest(payload=payload):
                response = self.client.post('/api/v1/auth/refresh', json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')
                self.assertNotIn('hidden', response.text)
