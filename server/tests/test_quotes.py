import unittest
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from psycopg import errors, sql
from psycopg.rows import class_row

from app.accounts.service import create_user
from app.common.enums import DiscountType
from app.common.numbering import next_quote_number
from app.quotes.models import Quote, QuoteStatus
from tests import test_accounts


class QuotePersistenceTests(unittest.TestCase):
    setUpClass = classmethod(test_accounts.UserPersistenceTests.setUpClass.__func__)
    drop_test_schema = test_accounts.UserPersistenceTests.drop_test_schema

    def setUp(self):
        test_accounts.UserPersistenceTests.setUp(self)
        self.owner = create_user(self.connection, name='Owner', email='owner@example.com', password='test-password')
        self.client_id = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Client') RETURNING id", (self.owner.id,),
        ).fetchone()[0]

    def insert(self, **changes):
        with self.connection.transaction():
            values = {
                'user_id': self.owner.id, 'client_id': self.client_id,
                'quote_number': next_quote_number(self.connection, user_id=self.owner.id),
                'issue_date': date(2026, 9, 14), 'currency': 'KES',
                'subtotal': Decimal('100.00'), 'total': Decimal('100.00'), **changes,
            }
            with self.connection.cursor(row_factory=class_row(Quote)) as cursor:
                cursor.execute(sql.SQL('INSERT INTO quotes ({}) VALUES ({}) RETURNING *').format(
                    sql.SQL(', ').join(map(sql.Identifier, values)),
                    sql.SQL(', ').join(sql.Placeholder() for _ in values),
                ), tuple(values.values()))
                return cursor.fetchone()

    def test_creation_maps_defaults_and_database_types(self):
        quote = self.insert()
        self.assertIsInstance(quote, Quote)
        self.assertIsInstance(quote.id, UUID)
        self.assertEqual((quote.user_id, quote.client_id), (self.owner.id, self.client_id))
        self.assertEqual(quote.quote_number, 'QT-0001')
        self.assertEqual(quote.issue_date, date(2026, 9, 14))
        self.assertEqual(quote.currency, 'KES')
        self.assertIs(quote.status, QuoteStatus.DRAFT)
        self.assertIs(quote.discount_type, DiscountType.NONE)
        for field in ('expiry_date', 'notes', 'terms'):
            self.assertIsNone(getattr(quote, field))
        for field in ('subtotal', 'tax_rate', 'tax_amount', 'discount_value', 'discount_amount', 'total'):
            self.assertIsInstance(getattr(quote, field), Decimal)
        self.assertEqual((quote.tax_rate, quote.tax_amount, quote.discount_value, quote.discount_amount), (0, 0, 0, 0))
        self.assertEqual(quote.created_at.utcoffset(), timedelta(0))
        self.assertEqual(quote.created_at, quote.updated_at)

    def test_all_fields_round_trip(self):
        quote = self.insert(expiry_date=date(2026, 9, 30), tax_rate=Decimal('16.000'),
                            tax_amount=Decimal('16.00'), discount_type='FIXED',
                            discount_value=Decimal('10.00'), discount_amount=Decimal('10.00'),
                            total=Decimal('106.00'), status='SENT', notes='Notes', terms='Terms')
        self.assertEqual(quote.expiry_date, date(2026, 9, 30))
        self.assertIs(quote.status, QuoteStatus.SENT)
        self.assertIs(quote.discount_type, DiscountType.FIXED)
        self.assertEqual((quote.tax_rate, quote.tax_amount, quote.discount_value, quote.discount_amount, quote.total),
                         (Decimal('16'), Decimal('16'), Decimal('10'), Decimal('10'), Decimal('106')))
        self.assertEqual((quote.notes, quote.terms), ('Notes', 'Terms'))

    def test_nonnegative_money_and_valid_dates_enforced(self):
        for field in ('subtotal', 'tax_rate', 'tax_amount', 'discount_value', 'discount_amount', 'total'):
            with self.subTest(field=field), self.assertRaises(errors.CheckViolation):
                self.insert(**{field: Decimal('-1')})
        with self.assertRaises(errors.CheckViolation):
            self.insert(expiry_date=date(2026, 9, 13))
        self.assertEqual(self.insert(expiry_date=date(2026, 9, 14)).expiry_date, date(2026, 9, 14))

    def test_number_unique_per_owner_and_foreign_keys_required(self):
        original = self.insert()
        with self.assertRaises(errors.UniqueViolation):
            self.insert(quote_number=original.quote_number)
        other = create_user(self.connection, name='Other', email='other@example.com', password='test-password')
        other_client = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Other') RETURNING id", (other.id,),
        ).fetchone()[0]
        self.assertEqual(self.insert(user_id=other.id, client_id=other_client, quote_number=original.quote_number).quote_number,
                         original.quote_number)
        for field in ('user_id', 'client_id'):
            with self.subTest(field=field), self.assertRaises(errors.ForeignKeyViolation):
                self.insert(**{field: uuid4()})

    def test_status_enum_matches_database_and_invalid_status_rejected(self):
        labels = self.connection.execute('SELECT unnest(enum_range(NULL::quote_status))::text').fetchall()
        self.assertEqual([row[0] for row in labels], [status.value for status in QuoteStatus])
        with self.assertRaises(errors.InvalidTextRepresentation):
            self.insert(status='UNKNOWN')

    def test_documented_indexes_exist(self):
        indexes = dict(self.connection.execute(
            "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = current_schema() AND tablename = 'quotes'"
        ).fetchall())
        for name, columns in (('quotes_user_id_idx', '(user_id)'), ('quotes_client_id_idx', '(client_id)'),
                              ('quotes_created_at_idx', '(created_at)'), ('quotes_user_status_idx', '(user_id, status)')):
            self.assertIn(columns, indexes[name])
