import unittest
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

from app.common.calculations import calculate_line_total
from app.common.errors import DomainError
from app.common.line_items import LineItemInput


class LineTotalTests(unittest.TestCase):
    def item(self, quantity, unit_price):
        return LineItemInput(description='Work', quantity=quantity, unit_price=unit_price)

    def test_exact_decimal_multiplication_and_fractional_quantities(self):
        for quantity, price, expected in (('2', '1500.50', '3001.00'),
                                          ('1.250', '100', '125.00'),
                                          ('3', '0.10', '0.30'), ('0.001', '10', '0.01')):
            with self.subTest(quantity=quantity, price=price):
                item = self.item(quantity, price)
                original = item.model_dump()
                total = calculate_line_total(item)
                self.assertIsInstance(total, Decimal)
                self.assertEqual(str(total), expected)
                self.assertEqual(item.model_dump(), original)

    def test_round_half_up_at_cent_boundaries(self):
        for quantity, expected in (('0.004', '0.00'), ('0.005', '0.01'),
                                   ('0.006', '0.01'), ('1.005', '1.01')):
            with self.subTest(quantity=quantity):
                self.assertEqual(str(calculate_line_total(self.item(quantity, '1'))), expected)

    def test_zero_price_has_canonical_two_decimal_zero(self):
        for price in ('0', '-0.00'):
            self.assertEqual(str(calculate_line_total(self.item('999999999.999', price))), '0.00')

    def test_maximum_storable_total_and_overflow(self):
        self.assertEqual(calculate_line_total(self.item('1', '999999999999.99')),
                         Decimal('999999999999.99'))
        for quantity, price in (('2', '999999999999.99'),
                               ('999999999.999', '999999999999.99'),
                               ('1.005', '995024875621.89')):
            with self.subTest(quantity=quantity, price=price), self.assertRaises(DomainError) as error:
                calculate_line_total(self.item(quantity, price))
            self.assertEqual(error.exception.code, 'LINE_TOTAL_OUT_OF_RANGE')
            self.assertEqual(error.exception.status_code, 422)

    def test_ambient_decimal_context_cannot_change_result(self):
        item = self.item('1.005', '1')
        with localcontext() as caller:
            caller.prec = 3
            caller.rounding = ROUND_DOWN
            caller.traps[Inexact] = True
            self.assertEqual(str(calculate_line_total(item)), '1.01')
            self.assertEqual(caller.prec, 3)
            self.assertEqual(caller.rounding, ROUND_DOWN)
            self.assertTrue(caller.traps[Inexact])
