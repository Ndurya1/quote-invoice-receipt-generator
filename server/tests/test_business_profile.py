import unittest
from datetime import timedelta
from uuid import UUID, uuid4

from psycopg import errors
from psycopg.rows import class_row

from app.accounts.service import create_user
from app.business.models import BusinessProfile
from tests import test_accounts


class BusinessProfileTests(unittest.TestCase):
    setUpClass = classmethod(test_accounts.UserPersistenceTests.setUpClass.__func__)
    setUp = test_accounts.UserPersistenceTests.setUp
    drop_test_schema = test_accounts.UserPersistenceTests.drop_test_schema

    def create_owner(self, email='owner@example.com'):
        return create_user(self.connection, name='Owner', email=email, password='test-password')

    def insert_minimal_profile(self, user_id):
        with self.connection.cursor(row_factory=class_row(BusinessProfile)) as cursor:
            cursor.execute(
                'INSERT INTO business_profiles (user_id, business_name) VALUES (%s, %s) RETURNING *',
                (user_id, "Owner's Business"),
            )
            return cursor.fetchone()

    def test_creation_uses_database_defaults_and_nullable_fields(self):
        owner = self.create_owner()
        profile = self.insert_minimal_profile(owner.id)
        self.assertIsInstance(profile, BusinessProfile)
        self.assertIsInstance(profile.id, UUID)
        self.assertEqual(profile.user_id, owner.id)
        self.assertEqual(profile.business_name, "Owner's Business")
        self.assertEqual(profile.default_currency, 'KES')
        for field in ('logo_url', 'email', 'phone', 'address', 'tax_number'):
            self.assertIsNone(getattr(profile, field))
        self.assertEqual(profile.created_at.utcoffset(), timedelta(0))
        self.assertEqual(profile.created_at, profile.updated_at)

    def test_full_profile_round_trips_and_update_refreshes_timestamp(self):
        owner = self.create_owner()
        with self.connection.cursor(row_factory=class_row(BusinessProfile)) as cursor:
            cursor.execute(
                '''INSERT INTO business_profiles
                   (user_id, business_name, logo_url, email, phone, address, tax_number, default_currency)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *''',
                (owner.id, 'Example Ltd', 'https://example.com/logo.png', 'billing@example.com',
                 '+254700123456', 'Nairobi', 'TAX-123', 'USD'),
            )
            profile = cursor.fetchone()
            self.assertEqual(profile.model_dump(exclude={'id', 'created_at', 'updated_at'}), {
                'user_id': owner.id, 'business_name': 'Example Ltd',
                'logo_url': 'https://example.com/logo.png', 'email': 'billing@example.com',
                'phone': '+254700123456', 'address': 'Nairobi', 'tax_number': 'TAX-123',
                'default_currency': 'USD',
            })
            cursor.execute('UPDATE business_profiles SET business_name = %s WHERE id = %s RETURNING *',
                           ('Updated Ltd', profile.id))
            updated = cursor.fetchone()
        self.assertEqual(updated.id, profile.id)
        self.assertEqual(updated.created_at, profile.created_at)
        self.assertGreater(updated.updated_at, profile.updated_at)

    def test_second_profile_for_same_user_is_rejected(self):
        owner = self.create_owner()
        original = self.insert_minimal_profile(owner.id)
        with self.assertRaises(errors.UniqueViolation):
            self.insert_minimal_profile(owner.id)
        self.assertEqual(self.connection.execute('SELECT id FROM business_profiles').fetchall(),
                         [(original.id,)])
        other = self.create_owner('other@example.com')
        self.assertNotEqual(self.insert_minimal_profile(other.id).id, original.id)

    def test_owner_must_exist_and_required_fields_cannot_be_null(self):
        with self.assertRaises(errors.ForeignKeyViolation):
            self.insert_minimal_profile(uuid4())
        owner = self.create_owner()
        for user_id, name, currency in ((None, 'Business', 'KES'),
                                        (owner.id, None, 'KES'), (owner.id, 'Business', None)):
            with self.subTest(user_id=user_id, name=name, currency=currency):
                with self.assertRaises(errors.NotNullViolation):
                    self.connection.execute(
                        'INSERT INTO business_profiles (user_id, business_name, default_currency) VALUES (%s, %s, %s)',
                        (user_id, name, currency),
                    )
