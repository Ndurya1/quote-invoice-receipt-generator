import unittest

from pydantic import BaseModel, ValidationError

from app.common.enums import DiscountType
from tests import test_accounts


class DiscountInput(BaseModel):
    discount_type: DiscountType


class DiscountTypeTests(unittest.TestCase):
    def test_pydantic_parses_and_serializes_document_values(self):
        for value in ('NONE', 'FIXED', 'PERCENTAGE'):
            with self.subTest(value=value):
                parsed = DiscountInput.model_validate_json('{"discount_type":"' + value + '"}')
                self.assertIsInstance(parsed.discount_type, DiscountType)
                self.assertEqual(parsed.model_dump(mode='json'), {'discount_type': value})
                self.assertEqual(str(parsed.discount_type), value)

    def test_unknown_lowercase_and_non_string_values_are_rejected(self):
        for value in ('none', 'fixed', 'percentage', '', ' FIXED ', 'OTHER', None, 1):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                DiscountInput(discount_type=value)


class DiscountTypeDatabaseTests(unittest.TestCase):
    setUpClass = classmethod(test_accounts.UserPersistenceTests.setUpClass.__func__)
    setUp = test_accounts.UserPersistenceTests.setUp
    drop_test_schema = test_accounts.UserPersistenceTests.drop_test_schema

    def test_python_enum_matches_postgresql_enum(self):
        labels = self.connection.execute(
            "SELECT unnest(enum_range(NULL::discount_type))::text"
        ).fetchall()
        self.assertEqual([row[0] for row in labels], [member.value for member in DiscountType])
