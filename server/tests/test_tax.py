import unittest
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

from app.common.calculations import calculate_tax_amount
from app.common.errors import DomainError


class TaxTests(unittest.TestCase):
    def test_percentage_calculation_and_default_zero(self):
        self.assertEqual(str(calculate_tax_amount(Decimal('35000.00'), Decimal('16'))), '5600.00')
        self.assertEqual(str(calculate_tax_amount(Decimal('35000.00'))), '0.00')
        self.assertEqual(str(calculate_tax_amount(Decimal('0'), Decimal('16'))), '0.00')
        self.assertEqual(str(calculate_tax_amount(Decimal('100'), Decimal('-0'))), '0.00')
        self.assertEqual(str(calculate_tax_amount(Decimal('100'), Decimal('999.999'))), '1000.00')

    def test_fractional_rates_and_half_up_rounding(self):
        for subtotal, rate, expected in (('100', '7.125', '7.13'), ('1', '0.499', '0.00'),
                                         ('1', '0.500', '0.01'), ('1', '0.501', '0.01')):
            with self.subTest(subtotal=subtotal, rate=rate):
                self.assertEqual(str(calculate_tax_amount(Decimal(subtotal), Decimal(rate))), expected)

    def test_invalid_rates_are_rejected(self):
        for rate in (Decimal('-0.001'), Decimal('1000'), Decimal('1.0001'),
                     Decimal('NaN'), Decimal('Infinity'), None, 16, 16.0, '16', True):
            with self.subTest(rate=rate), self.assertRaises(DomainError) as error:
                calculate_tax_amount(Decimal('100'), rate)
            self.assertEqual(error.exception.code, 'INVALID_TAX_RATE')
            self.assertEqual(error.exception.status_code, 422)

    def test_invalid_subtotals_are_rejected(self):
        for subtotal in (Decimal('-1'), Decimal('0.001'), Decimal('1000000000000'),
                         Decimal('NaN'), Decimal('Infinity'), None, 100, 100.0, '100', True):
            with self.subTest(subtotal=subtotal), self.assertRaises(DomainError) as error:
                calculate_tax_amount(subtotal)
            self.assertEqual(error.exception.code, 'INVALID_SUBTOTAL')

    def test_maximum_tax_amount_and_overflow(self):
        maximum = Decimal('999999999999.99')
        self.assertEqual(calculate_tax_amount(maximum, Decimal('100')), maximum)
        with self.assertRaises(DomainError) as error:
            calculate_tax_amount(maximum, Decimal('100.001'))
        self.assertEqual(error.exception.code, 'TAX_AMOUNT_OUT_OF_RANGE')
        self.assertEqual(error.exception.status_code, 422)

    def test_caller_decimal_context_is_isolated(self):
        with localcontext() as caller:
            caller.prec = 3
            caller.rounding = ROUND_DOWN
            caller.traps[Inexact] = True
            self.assertEqual(str(calculate_tax_amount(Decimal('12345.67'), Decimal('16'))), '1975.31')
            self.assertEqual(caller.prec, 3)
            self.assertEqual(caller.rounding, ROUND_DOWN)
            self.assertTrue(caller.traps[Inexact])
