import unittest
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

from app.common.calculations import calculate_discount_amount
from app.common.enums import DiscountType
from app.common.errors import DomainError


class DiscountTests(unittest.TestCase):
    def test_none_requires_zero_value(self):
        self.assertEqual(str(calculate_discount_amount(Decimal('100'))), '0.00')
        with self.assertRaises(DomainError) as error:
            calculate_discount_amount(Decimal('100'), DiscountType.NONE, Decimal('1'))
        self.assertEqual(error.exception.code, 'INVALID_DISCOUNT')

    def test_percentage_uses_subtotal_and_rounds_half_up(self):
        for subtotal, value, expected in (('100', '0', '0.00'), ('100', '100', '100.00'),
                                          ('100', '7.12', '7.12'), ('1', '0.50', '0.01'),
                                          ('0', '100', '0.00')):
            with self.subTest(subtotal=subtotal, value=value):
                amount = calculate_discount_amount(Decimal(subtotal), DiscountType.PERCENTAGE,
                                                   Decimal(value), tax_amount=Decimal('16'))
                self.assertEqual(str(amount), expected)

    def test_fixed_discount_can_include_tax_but_not_exceed_gross_amount(self):
        self.assertEqual(str(calculate_discount_amount(Decimal('100'), DiscountType.FIXED,
                                                      Decimal('116'), tax_amount=Decimal('16'))), '116.00')
        with self.assertRaises(DomainError) as error:
            calculate_discount_amount(Decimal('100'), DiscountType.FIXED,
                                      Decimal('116.01'), tax_amount=Decimal('16'))
        self.assertEqual(error.exception.code, 'INVALID_DISCOUNT')

    def test_invalid_values_types_and_percentage_limit(self):
        for value in (Decimal('-1'), Decimal('0.001'), Decimal('NaN'), Decimal('Infinity'),
                      Decimal('1000000000000'), None, '10', 10.0, True):
            with self.subTest(value=value), self.assertRaises(DomainError) as error:
                calculate_discount_amount(Decimal('100'), DiscountType.FIXED, value)
            self.assertEqual(error.exception.code, 'INVALID_DISCOUNT')
        for kind, value in ((DiscountType.PERCENTAGE, Decimal('100.01')),
                            ('FIXED', Decimal('1')), ('OTHER', Decimal('0')), (None, Decimal('0'))):
            with self.subTest(kind=kind), self.assertRaises(DomainError):
                calculate_discount_amount(Decimal('100'), kind, value)

    def test_invalid_subtotal_and_tax_rejected(self):
        for value in (Decimal('-1'), Decimal('0.001'), Decimal('NaN'), None, 1.0):
            with self.subTest(value=value):
                with self.assertRaises(DomainError) as error:
                    calculate_discount_amount(value)
                self.assertEqual(error.exception.code, 'INVALID_SUBTOTAL')
                with self.assertRaises(DomainError) as error:
                    calculate_discount_amount(Decimal('100'), tax_amount=value)
                self.assertEqual(error.exception.code, 'INVALID_TAX_AMOUNT')

    def test_maximum_amount_and_signed_zero(self):
        maximum = Decimal('999999999999.99')
        self.assertEqual(calculate_discount_amount(maximum, DiscountType.FIXED, maximum), maximum)
        self.assertEqual(calculate_discount_amount(maximum, DiscountType.PERCENTAGE, Decimal('100')), maximum)
        self.assertEqual(str(calculate_discount_amount(Decimal('0'), DiscountType.FIXED, Decimal('-0'))), '0.00')

    def test_caller_context_does_not_change_rounding(self):
        with localcontext() as caller:
            caller.prec = 3
            caller.rounding = ROUND_DOWN
            caller.traps[Inexact] = True
            amount = calculate_discount_amount(Decimal('12345.67'), DiscountType.PERCENTAGE, Decimal('16'))
            self.assertEqual(str(amount), '1975.31')
            self.assertEqual(caller.prec, 3)
            self.assertEqual(caller.rounding, ROUND_DOWN)
            self.assertTrue(caller.traps[Inexact])
