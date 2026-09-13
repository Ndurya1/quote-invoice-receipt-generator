import unittest
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from app.accounts.models import User
from app.accounts.schemas import UserCreate, UserResponse


class RegistrationSchemaTests(unittest.TestCase):
    def payload(self, **changes):
        return {"name": "Owner", "email": "owner@example.com", "password": "Example123", **changes}

    def test_normalizes_name_and_email(self):
        request = UserCreate(**self.payload(name="  Owner  ", email=" OWNER@EXAMPLE.COM "))
        self.assertEqual(request.name, "Owner")
        self.assertEqual(request.email, "owner@example.com")

    def test_name_limits(self):
        for name in ("", "   ", "n" * 121, None):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                UserCreate(**self.payload(name=name))
        self.assertEqual(len(UserCreate(**self.payload(name="n" * 120)).name), 120)

    def test_email_and_required_fields(self):
        with self.assertRaises(ValidationError):
            UserCreate(**self.payload(email="not-an-email"))
        for field in ("name", "email", "password"):
            data = self.payload()
            del data[field]
            with self.subTest(field=field), self.assertRaises(ValidationError):
                UserCreate(**data)

    def test_optional_local_and_international_phone(self):
        self.assertIsNone(UserCreate(**self.payload()).phone)
        for phone in (None, "0712345678", "+254712345678", "1" * 30):
            with self.subTest(phone=phone):
                self.assertEqual(UserCreate(**self.payload(phone=phone)).phone, phone)
        self.assertEqual(UserCreate(**self.payload(phone="  +254712345678  ")).phone, "+254712345678")

    def test_invalid_phone(self):
        for phone in ("", " ", "+", "+abcdef", "123abc", "12+34", "++123", "12 34", "١٢٣", "1" * 31, "+" + "1" * 30):
            with self.subTest(phone=phone), self.assertRaises(ValidationError):
                UserCreate(**self.payload(phone=phone))

    def test_password_rules_and_whitespace_preserved(self):
        for password in ("Aa1", "NoDigitsHere", "lowercase123", "UPPERCASE123"):
            with self.subTest(password=password), self.assertRaises(ValidationError):
                UserCreate(**self.payload(password=password))
        password = "  Example123  "
        self.assertEqual(UserCreate(**self.payload(password=password)).password, password)

    def test_password_excluded_from_serialization_and_repr(self):
        request = UserCreate(**self.payload())
        self.assertEqual(request.password, "Example123")
        for result in (request.model_dump(), jsonable_encoder(request)):
            self.assertNotIn("password", result)
        self.assertNotIn("Example123", request.model_dump_json())
        self.assertNotIn("Example123", repr(request))

    def test_response_accepts_persisted_user_and_matches_contract(self):
        user = User(
            id=uuid4(), name="Owner", email="owner@example.com", phone=None,
            password_hash="private-hash", created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        response = UserResponse.model_validate(user)
        self.assertEqual(response.id, user.id)
        self.assertEqual(jsonable_encoder(response), {
            "id": str(user.id), "name": "Owner", "email": "owner@example.com", "phone": None,
        })
