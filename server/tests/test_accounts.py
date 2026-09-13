import os
import unittest
from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
from psycopg import sql

from app.accounts.models import User
from app.accounts.passwords import hash_password, verify_password
from app.accounts.service import create_user
from app.common.database import DatabaseSettings, connect_database
from app.common.errors import DomainError
from app.common.migrations import apply_migrations


class PasswordTests(unittest.TestCase):
    def test_hashing_is_salted_and_verification_checks_password(self):
        password = "A test password with Unicode: café"
        first = hash_password(password)
        second = hash_password(password)
        self.assertTrue(first.startswith("$argon2id$"))
        self.assertNotEqual(first, second)
        self.assertNotIn(password, first)
        self.assertTrue(verify_password(password, first))
        self.assertTrue(verify_password(password, second))
        self.assertFalse(verify_password("incorrect password", first))


class UserPersistenceTests(unittest.TestCase):
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
        self.schema = "accounts_test_" + uuid4().hex
        self.connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        self.addCleanup(self.drop_test_schema)
        self.connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema)))
        apply_migrations(self.connection)

    def drop_test_schema(self):
        # Only this test's randomly generated schema in the separate test DB.
        self.connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))

    def test_creation_persists_uuid_fields_and_hash(self):
        user = create_user(
            self.connection, name="O'Brien", email="owner@example.com",
            password="test-only-password", phone="0712345678",
        )
        self.assertIsInstance(user, User)
        self.assertIsInstance(user.id, UUID)
        self.assertEqual(user.name, "O'Brien")
        self.assertEqual(user.email, "owner@example.com")
        self.assertEqual(user.phone, "0712345678")
        self.assertEqual(user.created_at.utcoffset(), timedelta(0))
        self.assertEqual(user.created_at, user.updated_at)
        stored = self.connection.execute(
            "SELECT id, name, email, phone, password_hash FROM users WHERE id = %s", (user.id,)
        ).fetchone()
        self.assertEqual(stored[:4], (user.id, user.name, user.email, user.phone))
        self.assertEqual(stored[4], user.password_hash)
        self.assertNotEqual(stored[4], "test-only-password")
        self.assertTrue(verify_password("test-only-password", stored[4]))

    def test_optional_phone_and_serialization_hide_hash(self):
        user = create_user(self.connection, name="Owner", email="owner@example.com", password="test-password")
        self.assertIsNone(user.phone)
        self.assertNotIn("password_hash", user.model_dump())
        self.assertNotIn("password_hash", user.model_dump_json())
        self.assertNotIn("password_hash", jsonable_encoder(user))
        self.assertNotIn(user.password_hash, repr(user))

    def test_duplicate_email_is_rejected_and_connection_remains_usable(self):
        original = create_user(self.connection, name="Original", email="same@example.com", password="first-password")
        with self.assertRaises(DomainError) as error:
            create_user(self.connection, name="Duplicate", email="same@example.com", password="second-password")
        self.assertEqual(error.exception.code, "EMAIL_ALREADY_REGISTERED")
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM users").fetchone()[0], 1)
        existing_id, existing_hash = self.connection.execute("SELECT id, password_hash FROM users").fetchone()
        self.assertEqual(existing_id, original.id)
        self.assertTrue(verify_password("first-password", existing_hash))
        self.assertFalse(verify_password("second-password", existing_hash))

    def test_creation_respects_outer_transaction_rollback(self):
        with self.assertRaisesRegex(RuntimeError, "Abort enclosing operation"):
            with self.connection.transaction():
                create_user(self.connection, name="Owner", email="owner@example.com", password="test-password")
                raise RuntimeError("Abort enclosing operation")
        self.assertEqual(self.connection.execute("SELECT count(*) FROM users").fetchone()[0], 0)
