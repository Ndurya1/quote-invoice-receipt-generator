import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from psycopg import sql

from app.accounts.passwords import verify_password
from app.common.database import DatabaseSettings, connect_database
from app.common.migrations import apply_migrations
from app.common.settings import Settings
from app.main import create_app


class RegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
        if not os.getenv("TEST_DATABASE_URL"):
            raise unittest.SkipTest("Set TEST_DATABASE_URL to run PostgreSQL integration tests")
        cls.settings = DatabaseSettings.from_environment()
        cls.settings.connection_url(test=True)

    def setUp(self):
        self.connection = connect_database(self.settings, test=True)
        self.addCleanup(self.connection.close)
        self.schema = "registration_test_" + uuid4().hex
        self.connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        self.addCleanup(self.drop_test_schema)
        self.connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
        apply_migrations(self.connection)
        self.request_connections = []

        def connect_to_schema(settings, *, test=False):
            self.assertTrue(test, "Test-mode API must select TEST_DATABASE_URL")
            connection = connect_database(settings, test=test)
            self.request_connections.append(connection)
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
            return connection

        connection_patch = patch("app.common.dependencies.connect_database", side_effect=connect_to_schema)
        connection_patch.start()
        self.addCleanup(connection_patch.stop)
        self.client = TestClient(create_app(Settings(environment="test")), raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def drop_test_schema(self):
        # Only this test's generated schema in the explicitly separate test database.
        self.connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))

    def payload(self, **changes):
        return {"name": "Owner", "email": "owner@example.com", "password": "Example123", **changes}

    def post(self, payload):
        response = self.client.post("/api/v1/auth/register", json=payload)
        self.assertTrue(all(connection.closed for connection in self.request_connections))
        return response

    def test_registration_returns_public_fields_and_persists_hash(self):
        response = self.post(self.payload(name="  Owner  ", email=" OWNER@EXAMPLE.COM ", phone="0712345678"))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["content-type"], "application/json")
        user_id = UUID(response.json()["data"]["id"])
        self.assertEqual(response.json(), {"data": {
            "id": str(user_id), "name": "Owner", "email": "owner@example.com", "phone": "0712345678",
        }})
        stored = self.connection.execute(
            "SELECT name, email, phone, password_hash FROM users WHERE id = %s", (user_id,)
        ).fetchone()
        self.assertEqual(stored[:3], ("Owner", "owner@example.com", "0712345678"))
        self.assertTrue(verify_password("Example123", stored[3]))
        self.assertNotIn("Example123", response.text)
        self.assertNotIn(stored[3], response.text)

    def test_optional_phone_and_server_managed_input(self):
        forged_id = str(uuid4())
        response = self.post(self.payload(id=forged_id, password_hash="forged", created_at="2000-01-01"))
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.json()["data"]["phone"])
        self.assertNotEqual(response.json()["data"]["id"], forged_id)
        stored_hash = self.connection.execute("SELECT password_hash FROM users").fetchone()[0]
        self.assertNotEqual(stored_hash, "forged")

    def test_duplicate_normalized_email_returns_conflict_without_changes(self):
        self.assertEqual(self.post(self.payload()).status_code, 201)
        for email in ("owner@example.com", " OWNER@EXAMPLE.COM "):
            with self.subTest(email=email):
                response = self.post(self.payload(email=email, password="Different123"))
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json(), {"error": {
                    "code": "EMAIL_ALREADY_REGISTERED",
                    "message": "An account with this email already exists.", "details": {},
                }})
        self.assertEqual(self.connection.execute("SELECT count(*) FROM users").fetchone()[0], 1)
        self.assertTrue(verify_password("Example123", self.connection.execute("SELECT password_hash FROM users").fetchone()[0]))
        self.assertEqual(self.post(self.payload(email="another@example.com")).status_code, 201)

    def test_invalid_and_missing_fields_do_not_create_users(self):
        invalid = [self.payload(email="invalid"), self.payload(name=" "),
                   self.payload(phone="+letters"), self.payload(password="weak")]
        for field in ("name", "email", "password"):
            payload = self.payload()
            del payload[field]
            invalid.append(payload)
        for payload in invalid:
            with self.subTest(fields=list(payload)):
                response = self.post(payload)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
                self.assertNotIn("Example123", response.text)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM users").fetchone()[0], 0)

    def test_unrelated_unique_failure_remains_generic_server_error(self):
        self.connection.execute("CREATE UNIQUE INDEX test_unique_name ON users(name)")
        self.assertEqual(self.post(self.payload()).status_code, 201)
        response = self.post(self.payload(email="another@example.com"))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "INTERNAL_SERVER_ERROR")
        self.assertNotIn("test_unique_name", response.text)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM users").fetchone()[0], 1)

    def test_openapi_describes_registration_contract(self):
        document = self.client.get("/openapi.json").json()
        route = document["paths"]["/api/v1/auth/register"]["post"]
        self.assertIn("201", route["responses"])
        self.assertIn("422", route["responses"])
        self.assertEqual(document["components"]["schemas"]["UserCreate"]["required"], ["name", "email", "password"])
        self.assertEqual(set(document["components"]["schemas"]["UserResponse"]["properties"]), {"id", "name", "email", "phone"})
