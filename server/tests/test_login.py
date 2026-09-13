import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import jwt
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from psycopg import sql

from app.accounts.passwords import DUMMY_PASSWORD_HASH, verify_password
from app.accounts.schemas import LoginRequest
from app.accounts.service import authenticate_user
from app.accounts.tokens import AUDIENCE, ISSUER, TokenSettings, get_token_settings, issue_token_pair
from app.common.database import DatabaseSettings, connect_database
from app.common.errors import DomainError
from app.common.migrations import apply_migrations
from app.common.settings import Settings
from app.main import create_app

TEST_KEY = "test-only-signing-key-not-for-deployment-123456789"


class TokenTests(unittest.TestCase):
    def test_signed_pair_has_distinct_types_ids_and_configured_expiry(self):
        user_id = uuid4()
        settings = TokenSettings(TEST_KEY, access_minutes=5, refresh_days=2)
        pair = issue_token_pair(user_id, settings)
        claims = [jwt.decode(token, TEST_KEY, algorithms=["HS256"], issuer=ISSUER, audience=AUDIENCE)
                  for token in (pair.access_token, pair.refresh_token)]
        self.assertEqual([claim["type"] for claim in claims], ["access", "refresh"])
        self.assertEqual([claim["exp"] - claim["iat"] for claim in claims], [300, 172800])
        self.assertNotEqual(claims[0]["jti"], claims[1]["jti"])
        for claim in claims:
            self.assertEqual(claim["sub"], str(user_id))
            self.assertEqual(set(claim), {"sub", "type", "iat", "exp", "jti", "iss", "aud"})
            UUID(claim["jti"])
        with self.assertRaises(jwt.InvalidSignatureError):
            jwt.decode(pair.access_token, "different-test-key-longer-than-32-bytes", algorithms=["HS256"], audience=AUDIENCE)
        self.assertNotIn(pair.access_token, repr(pair))
        self.assertNotIn(TEST_KEY, repr(settings))

    def test_signing_configuration_fails_without_a_key_or_valid_lifetimes(self):
        for changes in ({}, {"JWT_SECRET_KEY": "short"},
                        {"JWT_SECRET_KEY": TEST_KEY, "JWT_ACCESS_TOKEN_MINUTES": "0"},
                        {"JWT_SECRET_KEY": TEST_KEY, "JWT_REFRESH_TOKEN_DAYS": "-1"},
                        {"JWT_SECRET_KEY": TEST_KEY, "JWT_REFRESH_TOKEN_DAYS": "not-a-number"},
                        {"JWT_SECRET_KEY": TEST_KEY, "JWT_ACCESS_TOKEN_MINUTES": "1440", "JWT_REFRESH_TOKEN_DAYS": "1"}):
            with self.subTest(fields=list(changes)), patch.dict(os.environ, changes, clear=True), self.assertRaises(ValueError):
                TokenSettings.from_environment()
        with patch.dict(os.environ, {"JWT_SECRET_KEY": TEST_KEY}, clear=True):
            settings = TokenSettings.from_environment()
        self.assertEqual((settings.access_minutes, settings.refresh_days), (15, 7))

    def test_login_does_not_apply_registration_password_policy(self):
        for password in ("", "weak", "  exact Password123  "):
            request = LoginRequest(email=" OWNER@EXAMPLE.COM ", password=password)
            self.assertEqual(request.email, "owner@example.com")
            self.assertEqual(request.password, password)
            self.assertNotIn("password", request.model_dump())

    def test_unknown_email_still_verifies_dummy_hash(self):
        with patch("app.accounts.service.get_user_by_email", return_value=None), \
                patch("app.accounts.service.verify_password", wraps=verify_password) as verify:
            with self.assertRaises(DomainError) as error:
                authenticate_user(None, email="unknown@example.com", password="incorrect")
            self.assertEqual(error.exception.code, "INVALID_CREDENTIALS")
            verify.assert_called_once_with("incorrect", DUMMY_PASSWORD_HASH)


class LoginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
        if not os.getenv("TEST_DATABASE_URL"):
            raise unittest.SkipTest("Set TEST_DATABASE_URL to run PostgreSQL integration tests")
        cls.database_settings = DatabaseSettings.from_environment()
        cls.database_settings.connection_url(test=True)

    def setUp(self):
        self.connection = connect_database(self.database_settings, test=True)
        self.addCleanup(self.connection.close)
        self.schema = "login_test_" + uuid4().hex
        self.connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        self.addCleanup(self.drop_test_schema)
        self.connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
        apply_migrations(self.connection)
        self.request_connections = []

        def connect_to_schema(settings, *, test=False):
            self.assertTrue(test)
            connection = connect_database(settings, test=True)
            self.request_connections.append(connection)
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
            return connection

        connection_patch = patch("app.common.dependencies.connect_database", side_effect=connect_to_schema)
        connection_patch.start()
        self.addCleanup(connection_patch.stop)
        self.app = create_app(Settings(environment="test"))
        self.app.dependency_overrides[get_token_settings] = lambda: TokenSettings(TEST_KEY)
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)
        registered = self.client.post("/api/v1/auth/register", json={
            "name": "Owner", "email": "owner@example.com", "password": "ExactPassword123",
        })
        self.assertEqual(registered.status_code, 201)
        self.user_id = registered.json()["data"]["id"]

    def drop_test_schema(self):
        # Only this test's generated schema in the separate test database.
        self.connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))

    def login(self, **changes):
        response = self.client.post("/api/v1/auth/login", json={
            "email": "owner@example.com", "password": "ExactPassword123", **changes,
        })
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_registration_then_login_returns_signed_tokens(self):
        response = self.login(email=" OWNER@EXAMPLE.COM ", sub="forged", type="refresh", exp=9999999999)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["pragma"], "no-cache")
        self.assertEqual(set(response.json()), {"data"})
        data = response.json()["data"]
        self.assertEqual(set(data), {"access_token", "refresh_token", "token_type"})
        self.assertEqual(data["token_type"], "bearer")
        for kind in ("access", "refresh"):
            claims = jwt.decode(data[kind + "_token"], TEST_KEY, algorithms=["HS256"], issuer=ISSUER, audience=AUDIENCE)
            self.assertEqual(claims["sub"], self.user_id)
            self.assertEqual(claims["type"], kind)
            self.assertNotIn("email", claims)
            self.assertNotEqual(claims["exp"], 9999999999)
        self.assertNotIn("ExactPassword123", response.text)
        self.assertNotIn("argon2", response.text)
        again = self.login().json()["data"]
        self.assertNotEqual(data["access_token"], again["access_token"])
        self.assertNotEqual(data["refresh_token"], again["refresh_token"])
        self.assertEqual(self.connection.execute("SELECT count(*) FROM users").fetchone()[0], 1)

    def test_unknown_user_and_wrong_password_have_identical_errors(self):
        original = self.connection.execute("SELECT password_hash, updated_at FROM users").fetchone()
        unknown = self.login(email="unknown@example.com")
        wrong = self.login(password="wrong")
        self.assertEqual(unknown.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(unknown.json(), wrong.json())
        self.assertEqual(wrong.json(), {"error": {
            "code": "INVALID_CREDENTIALS", "message": "Invalid email or password.", "details": {},
        }})
        self.assertEqual(wrong.headers["www-authenticate"], "Bearer")
        self.assertEqual(self.connection.execute("SELECT password_hash, updated_at FROM users").fetchone(), original)
        self.assertEqual(self.login(password=" ExactPassword123 ").status_code, 401)
        self.assertEqual(self.login(password="").status_code, 401)

    def test_invalid_and_missing_fields_use_validation_envelope(self):
        for payload in ({}, {"email": "owner@example.com"}, {"password": "ExactPassword123"},
                        {"email": "invalid", "password": "ExactPassword123"},
                        {"email": "owner@example.com", "password": None}):
            with self.subTest(fields=list(payload)):
                response = self.client.post("/api/v1/auth/login", json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
                self.assertNotIn("ExactPassword123", response.text)

    def test_missing_signing_key_returns_generic_error_without_tokens(self):
        self.app.dependency_overrides.pop(get_token_settings)
        with patch.dict(os.environ, {"JWT_SECRET_KEY": ""}):
            response = self.login()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "INTERNAL_SERVER_ERROR")
        self.assertNotIn("JWT_SECRET_KEY", response.text)
        self.assertNotIn("access_token", response.text)

    def test_openapi_documents_login_without_adding_future_routes(self):
        paths = self.client.get("/openapi.json").json()["paths"]
        self.assertIn("200", paths["/api/v1/auth/login"]["post"]["responses"])
        self.assertIn("/api/v1/auth/refresh", paths)
        self.assertNotIn("/api/v1/auth/me", paths)
