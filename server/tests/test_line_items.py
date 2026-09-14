import unittest
from decimal import Decimal

from pydantic import ValidationError

from app.common.line_items import LineItemInput


class LineItemTests(unittest.TestCase):
    def item(self, **changes):
        return LineItemInput(**{
            'description': 'Consulting', 'quantity': '1.250', 'unit_price': '1500.50', **changes,
        })

    def test_decimal_values_preserve_exact_amounts_and_default_position(self):
        item = self.item(description='  Consulting  ')
        self.assertEqual(item.description, 'Consulting')
        self.assertIsInstance(item.quantity, Decimal)
        self.assertIsInstance(item.unit_price, Decimal)
        self.assertEqual(item.quantity, Decimal('1.250'))
        self.assertEqual(item.unit_price, Decimal('1500.50'))
        self.assertEqual(item.position, 0)
        self.assertEqual(item.model_dump(mode='json')['unit_price'], '1500.50')
        self.assertEqual(self.item(quantity=2, unit_price=0).unit_price, Decimal(0))
        self.assertEqual(self.item(quantity=Decimal('0.001')).quantity, Decimal('0.001'))

    def test_json_strings_and_numbers_parse_as_decimals(self):
        for payload in ('{"description":"Work","quantity":"1.125","unit_price":"0.10"}',
                        '{"description":"Work","quantity":1.125,"unit_price":0.10}'):
            item = LineItemInput.model_validate_json(payload)
            self.assertEqual(item.quantity, Decimal('1.125'))
            self.assertEqual(item.unit_price, Decimal('0.10'))
            self.assertIsInstance(item.unit_price, Decimal)

    def test_quantity_must_be_positive_and_fit_database_precision(self):
        self.assertEqual(self.item(quantity='999999999.999').quantity, Decimal('999999999.999'))
        for value in ('0', '-0.001', '0.0001', '1.2345', '1000000000', None, True, 'bad'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.item(quantity=value)

    def test_price_must_be_nonnegative_and_fit_database_precision(self):
        self.assertEqual(self.item(unit_price='999999999999.99').unit_price, Decimal('999999999999.99'))
        for value in ('-0.01', '0.001', '1.234', '1000000000000', None, True, 'bad'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.item(unit_price=value)

    def test_non_finite_amounts_rejected(self):
        for field in ('quantity', 'unit_price'):
            for value in ('NaN', 'Infinity', '-Infinity', Decimal('NaN'), float('inf')):
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    self.item(**{field: value})

    def test_required_fields_and_description_validation(self):
        for value in ('', ' \n\t ', None, 123):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.item(description=value)
        payload = {'description': 'Work', 'quantity': 1, 'unit_price': 0}
        for field in payload:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                LineItemInput(**{k: v for k, v in payload.items() if k != field})

    def test_position_matches_postgresql_integer_range_without_coercion(self):
        for value in (-2147483648, -1, 0, 2147483647):
            self.assertEqual(self.item(position=value).position, value)
        for value in (-2147483649, 2147483648, 1.5, 1.0, '1', True, None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.item(position=value)

    def test_computed_and_unknown_fields_rejected(self):
        for field in ('line_total', 'subtotal', 'total', 'user_id', 'unknown'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.item(**{field: '10'})
