import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError

from app.accounts.service import create_user
from app.common.errors import DomainError
from app.quotes.schemas import QuoteCreate
from app.quotes.validation import validate_quote_create
from tests import test_quotes


def quote_payload(**changes):
    return {'client_id': str(uuid4()), 'issue_date': '2026-09-14', 'currency': 'KES',
            'items': [{'description': 'Work', 'quantity': '1.250', 'unit_price': '80.00'}], **changes}


class QuoteSchemaTests(unittest.TestCase):
    def test_valid_request_defaults_and_explicit_fields(self):
        request = QuoteCreate(**quote_payload())
        self.assertEqual(request.issue_date, date(2026, 9, 14))
        self.assertIsNone(request.expiry_date)
        self.assertIsNone(request.notes)
        self.assertIsNone(request.terms)
        self.assertEqual(request.tax_rate, Decimal('0'))
        self.assertEqual(request.discount_value, Decimal('0'))
        self.assertIsInstance(request.items[0].quantity, Decimal)
        full = QuoteCreate(**quote_payload(expiry_date='2026-09-14', tax_rate='16.000',
                                           discount_type='PERCENTAGE', discount_value='10.00',
                                           notes='Notes', terms='Terms'))
        self.assertEqual(full.expiry_date, full.issue_date)
        self.assertEqual(full.tax_rate, Decimal('16'))

    def test_required_fields_empty_items_and_dates(self):
        payload = quote_payload()
        for field in ('client_id', 'issue_date', 'currency', 'items'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                QuoteCreate(**{k: v for k, v in payload.items() if k != field})
        for changes in ({'items': []}, {'items': None}, {'client_id': 'bad'},
                        {'issue_date': '2026-02-30'}, {'expiry_date': '2026-09-13'},
                        {'currency': 'kes'}, {'currency': ' KES'}, {'currency': None}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                QuoteCreate(**quote_payload(**changes))

    def test_tax_and_discount_validation(self):
        for changes in ({'tax_rate': '-1'}, {'tax_rate': '1000'}, {'tax_rate': '0.0001'},
                        {'tax_rate': 'NaN'}, {'discount_type': 'other'}, {'discount_value': '-1'},
                        {'discount_value': 'Infinity'}, {'discount_value': '0.001'},
                        {'discount_value': '1'}, {'discount_type': 'PERCENTAGE', 'discount_value': '100.01'}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                QuoteCreate(**quote_payload(**changes))

    def test_nested_item_validation_and_computed_field_tampering(self):
        for changes in ({'description': ' '}, {'quantity': '0'}, {'quantity': '0.0001'},
                        {'unit_price': '-1'}, {'unit_price': '0.001'}, {'line_total': '1'}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                QuoteCreate(**quote_payload(items=[{'description': 'Work', 'quantity': '1', 'unit_price': '1', **changes}]))
        for field in ('id', 'user_id', 'quote_number', 'line_total', 'subtotal', 'tax_amount',
                      'discount_amount', 'total', 'status', 'created_at', 'updated_at'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                QuoteCreate(**quote_payload(**{field: 'forged'}))


class QuoteCreationValidationTests(unittest.TestCase):
    setUpClass = classmethod(test_quotes.QuotePersistenceTests.setUpClass.__func__)
    setUp = test_quotes.QuotePersistenceTests.setUp
    drop_test_schema = test_quotes.QuotePersistenceTests.drop_test_schema

    def validate(self, **changes):
        payload = QuoteCreate(**quote_payload(**{'client_id': self.client_id, **changes}))
        return validate_quote_create(self.connection, user_id=self.owner.id, payload=payload)

    def test_owned_client_and_calculated_totals_without_writes(self):
        result = self.validate(tax_rate='16', discount_type='FIXED', discount_value='10')
        self.assertEqual((result.subtotal, result.tax_amount, result.discount_amount, result.total),
                         (Decimal('100'), Decimal('16'), Decimal('10'), Decimal('106')))
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quotes').fetchone()[0], 0)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quote_number_counters').fetchone()[0], 0)

    def test_missing_and_foreign_client_rejected_identically(self):
        other = create_user(self.connection, name='Other', email='other@example.com', password='test-password')
        foreign_id = self.connection.execute("INSERT INTO clients (user_id, name) VALUES (%s, 'Other') RETURNING id",
                                             (other.id,)).fetchone()[0]
        for client_id in (uuid4(), foreign_id):
            with self.subTest(client_id=client_id), self.assertRaises(DomainError) as error:
                self.validate(client_id=client_id)
            self.assertEqual(error.exception.code, 'CLIENT_NOT_FOUND')
            self.assertEqual(error.exception.status_code, 404)

    def test_excessive_discount_and_financial_overflow_rejected(self):
        with self.assertRaises(DomainError) as error:
            self.validate(discount_type='FIXED', discount_value='100.01')
        self.assertEqual(error.exception.code, 'INVALID_DISCOUNT')
        self.assertEqual(self.validate(tax_rate='16', discount_type='FIXED', discount_value='116').total, Decimal('0'))
        with self.assertRaises(DomainError) as error:
            self.validate(items=[{'description': 'Work', 'quantity': '2', 'unit_price': '999999999999.99'}])
        self.assertEqual(error.exception.code, 'LINE_TOTAL_OUT_OF_RANGE')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quotes').fetchone()[0], 0)
