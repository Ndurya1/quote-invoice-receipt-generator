import unittest
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

from app.common.calculations import calculate_subtotal
from app.common.errors import DomainError
from app.common.line_items import LineItemInput


class SubtotalTests(unittest.TestCase):
    def item(self, quantity, price):
        return LineItemInput(description='Work', quantity=quantity, unit_price=price)

    def test_sums_exact_decimal_line_totals_without_mutation(self):
        items = [self.item('2', '10.10'), self.item('1.250', '4.00'), self.item('3', '0.10')]
        original = [item.model_dump() for item in items]
        subtotal = calculate_subtotal(items)
        self.assertIsInstance(subtotal, Decimal)
        self.assertEqual(str(subtotal), '25.50')
        self.assertEqual([item.model_dump() for item in items], original)

    def test_sums_rounded_lines_rather_than_rounding_raw_sum(self):
        items = [self.item('0.005', '1'), self.item('0.005', '1')]
        self.assertEqual(str(calculate_subtotal(items)), '0.02')

    def test_empty_single_zero_and_generator_inputs(self):
        self.assertEqual(str(calculate_subtotal([])), '0.00')
        self.assertEqual(str(calculate_subtotal([self.item('1', '0')])), '0.00')
        self.assertEqual(str(calculate_subtotal([self.item('1', '12.34')])), '12.34')
        self.assertEqual(str(calculate_subtotal(self.item('1', '0.10') for _ in range(100))), '10.00')

    def test_maximum_subtotal_and_aggregate_overflow(self):
        items = [self.item('1', '999999999999.98'), self.item('1', '0.01')]
        self.assertEqual(calculate_subtotal(items), Decimal('999999999999.99'))
        with self.assertRaises(DomainError) as error:
            calculate_subtotal([*items, self.item('1', '0.01')])
        self.assertEqual(error.exception.code, 'SUBTOTAL_OUT_OF_RANGE')
        self.assertEqual(error.exception.status_code, 422)

    def test_individual_line_overflow_is_propagated(self):
        with self.assertRaises(DomainError) as error:
            calculate_subtotal([self.item('2', '999999999999.99')])
        self.assertEqual(error.exception.code, 'LINE_TOTAL_OUT_OF_RANGE')

    def test_caller_decimal_settings_do_not_change_subtotal(self):
        items = [self.item('1', '12345.67'), self.item('0.005', '1')]
        with localcontext() as caller:
            caller.prec = 3
            caller.rounding = ROUND_DOWN
            caller.traps[Inexact] = True
            self.assertEqual(str(calculate_subtotal(items)), '12345.68')
            self.assertEqual(caller.prec, 3)
            self.assertEqual(caller.rounding, ROUND_DOWN)
            self.assertTrue(caller.traps[Inexact])
