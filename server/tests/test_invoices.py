import unittest
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from psycopg import errors, sql
from psycopg.rows import class_row

from app.accounts.service import create_user
from app.common.enums import DiscountType
from app.common.numbering import next_invoice_number
from app.invoices.models import Invoice, InvoiceStatus
from tests import test_accounts


class InvoicePersistenceTests(unittest.TestCase):
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
                'invoice_number': next_invoice_number(self.connection, user_id=self.owner.id),
                'issue_date': date(2026, 9, 14), 'currency': 'KES',
                'subtotal': Decimal('100.00'), 'total': Decimal('100.00'), **changes,
            }
            with self.connection.cursor(row_factory=class_row(Invoice)) as cursor:
                cursor.execute(sql.SQL('INSERT INTO invoices ({}) VALUES ({}) RETURNING *').format(
                    sql.SQL(', ').join(map(sql.Identifier, values)),
                    sql.SQL(', ').join(sql.Placeholder() for _ in values),
                ), tuple(values.values()))
                return cursor.fetchone()

    def test_creation_maps_defaults_and_database_types(self):
        invoice = self.insert()
        self.assertIsInstance(invoice, Invoice)
        self.assertIsInstance(invoice.id, UUID)
        self.assertEqual((invoice.user_id, invoice.client_id), (self.owner.id, self.client_id))
        self.assertEqual(invoice.invoice_number, 'INV-0001')
        self.assertEqual(invoice.issue_date, date(2026, 9, 14))
        self.assertEqual(invoice.currency, 'KES')
        self.assertIs(invoice.status, InvoiceStatus.DRAFT)
        self.assertIs(invoice.discount_type, DiscountType.NONE)
        for field in ('source_quote_id', 'due_date', 'notes', 'terms'):
            self.assertIsNone(getattr(invoice, field))
        for field in ('subtotal', 'tax_rate', 'tax_amount', 'discount_value', 'discount_amount', 'total'):
            self.assertIsInstance(getattr(invoice, field), Decimal)
        self.assertEqual((invoice.tax_rate, invoice.tax_amount, invoice.discount_value, invoice.discount_amount), (0, 0, 0, 0))
        self.assertEqual(invoice.created_at.utcoffset(), timedelta(0))
        self.assertEqual(invoice.created_at, invoice.updated_at)

    def test_all_fields_round_trip(self):
        invoice = self.insert(due_date=date(2026, 9, 30), tax_rate=Decimal('16.000'),
                            tax_amount=Decimal('16.00'), discount_type='FIXED',
                            discount_value=Decimal('10.00'), discount_amount=Decimal('10.00'),
                            total=Decimal('106.00'), status='SENT', notes='Notes', terms='Terms')
        self.assertEqual(invoice.due_date, date(2026, 9, 30))
        self.assertIs(invoice.status, InvoiceStatus.SENT)
        self.assertIs(invoice.discount_type, DiscountType.FIXED)
        self.assertEqual((invoice.tax_rate, invoice.tax_amount, invoice.discount_value, invoice.discount_amount, invoice.total),
                         (Decimal('16'), Decimal('16'), Decimal('10'), Decimal('10'), Decimal('106')))
        self.assertEqual((invoice.notes, invoice.terms), ('Notes', 'Terms'))

    def test_nonnegative_money_and_valid_dates_enforced(self):
        for field in ('subtotal', 'tax_rate', 'tax_amount', 'discount_value', 'discount_amount', 'total'):
            with self.subTest(field=field), self.assertRaises(errors.CheckViolation):
                self.insert(**{field: Decimal('-1')})
        with self.assertRaises(errors.CheckViolation):
            self.insert(due_date=date(2026, 9, 13))
        self.assertEqual(self.insert(due_date=date(2026, 9, 14)).due_date, date(2026, 9, 14))

    def test_number_unique_per_owner_and_foreign_keys_required(self):
        original = self.insert()
        with self.assertRaises(errors.UniqueViolation):
            self.insert(invoice_number=original.invoice_number)
        other = create_user(self.connection, name='Other', email='other@example.com', password='test-password')
        other_client = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Other') RETURNING id", (other.id,),
        ).fetchone()[0]
        self.assertEqual(self.insert(user_id=other.id, client_id=other_client, invoice_number=original.invoice_number).invoice_number,
                         original.invoice_number)
        for field in ('user_id', 'client_id'):
            with self.subTest(field=field), self.assertRaises(errors.ForeignKeyViolation):
                self.insert(**{field: uuid4()})

    def test_status_enum_matches_database_and_invalid_status_rejected(self):
        labels = self.connection.execute('SELECT unnest(enum_range(NULL::invoice_status))::text').fetchall()
        self.assertEqual([row[0] for row in labels], [status.value for status in InvoiceStatus])
        with self.assertRaises(errors.InvalidTextRepresentation):
            self.insert(status='UNKNOWN')

    def test_documented_indexes_exist(self):
        indexes = dict(self.connection.execute(
            "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = current_schema() AND tablename = 'invoices'"
        ).fetchall())
        for name, columns in (('invoices_user_id_idx', '(user_id)'), ('invoices_client_id_idx', '(client_id)'),
                              ('invoices_created_at_idx', '(created_at)'), ('invoices_user_status_idx', '(user_id, status)')):
            self.assertIn(columns, indexes[name])

    def test_source_quote_is_unique_optional_and_protects_history(self):
        quote_id = self.connection.execute(
            "INSERT INTO quotes (user_id, client_id, quote_number, issue_date, currency, subtotal, total) "
            "VALUES (%s, %s, 'QT-0001', '2026-09-14', 'KES', 100, 100) RETURNING id",
            (self.owner.id, self.client_id),
        ).fetchone()[0]
        self.assertIsNone(self.insert().source_quote_id)
        self.assertIsNone(self.insert().source_quote_id)
        self.assertEqual(self.insert(source_quote_id=quote_id).source_quote_id, quote_id)
        with self.assertRaises(errors.UniqueViolation):
            self.insert(source_quote_id=quote_id)
        with self.assertRaises(errors.ForeignKeyViolation):
            self.insert(source_quote_id=uuid4())
        with self.assertRaises(errors.RestrictViolation):
            self.connection.execute('DELETE FROM quotes WHERE id = %s', (quote_id,))
        indexes = self.connection.execute(
            "SELECT indexdef FROM pg_indexes WHERE schemaname = current_schema() AND tablename = 'invoices'"
        ).fetchall()
        self.assertTrue(any('UNIQUE INDEX' in row[0] and '(source_quote_id)' in row[0] for row in indexes))
