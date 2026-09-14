import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext

from app.common.enums import DiscountType
from app.common.errors import DomainError
from app.common.line_items import LineItemInput
from app.common.totals import calculate_document_totals


class DocumentTotalsTests(unittest.TestCase):
    def item(self, quantity='1', price='100', position=0):
        return LineItemInput(description='Work', quantity=quantity, unit_price=price, position=position)

    def test_complete_document_with_tax_and_fixed_discount(self):
        items = [self.item('2', '15000', 1), self.item('1.25', '4000', 2)]
        original = [item.model_dump() for item in items]
        result = calculate_document_totals(items, tax_rate=Decimal('16'),
                                           discount_type=DiscountType.FIXED, discount_value=Decimal('2000'))
        self.assertEqual([i.line_total for i in result.items], [Decimal('30000'), Decimal('5000')])
        self.assertEqual((result.subtotal, result.tax_amount, result.discount_amount, result.total),
                         (Decimal('35000'), Decimal('5600'), Decimal('2000'), Decimal('38600')))
        self.assertEqual(str(result.tax_rate), '16.000')
        self.assertEqual(str(result.discount_value), '2000.00')
        self.assertEqual([i.position for i in result.items], [1, 2])
        self.assertEqual([item.model_dump() for item in items], original)

    def test_percentage_uses_subtotal_and_defaults_are_zero(self):
        result = calculate_document_totals([self.item()], tax_rate=Decimal('16'),
                                           discount_type=DiscountType.PERCENTAGE, discount_value=Decimal('10'))
        self.assertEqual(result.total, Decimal('106.00'))
        default = calculate_document_totals([self.item()])
        self.assertEqual(default.total, Decimal('100.00'))
        self.assertEqual(default.tax_amount, Decimal('0.00'))
        self.assertEqual(default.discount_amount, Decimal('0.00'))
        self.assertEqual(default.discount_type, DiscountType.NONE)

    def test_rounding_matches_returned_lines_and_generator_is_consumed_once(self):
        result = calculate_document_totals((self.item('0.005', '1') for _ in range(2)))
        self.assertEqual([i.line_total for i in result.items], [Decimal('0.01')] * 2)
        self.assertEqual(result.subtotal, Decimal('0.02'))
        self.assertEqual(result.total, sum(i.line_total for i in result.items))

    def test_empty_and_invalid_financial_inputs(self):
        cases = [( [], {}, 'EMPTY_LINE_ITEMS'),
                 ([self.item()], {'tax_rate': Decimal('-1')}, 'INVALID_TAX_RATE'),
                 ([self.item()], {'discount_type': DiscountType.FIXED, 'discount_value': Decimal('101')}, 'INVALID_DISCOUNT'),
                 ([self.item('2', '999999999999.99')], {}, 'LINE_TOTAL_OUT_OF_RANGE'),
                 ([self.item('1', '999999999999.99')] * 2, {}, 'SUBTOTAL_OUT_OF_RANGE'),
                 ([self.item('1', '999999999999.99')], {'tax_rate': Decimal('200')}, 'TAX_AMOUNT_OUT_OF_RANGE'),
                 ([self.item('1', '999999999999.99')], {'tax_rate': Decimal('1')}, 'TOTAL_OUT_OF_RANGE')]
        for items, kwargs, code in cases:
            with self.subTest(code=code), self.assertRaises(DomainError) as error:
                calculate_document_totals(items, **kwargs)
            self.assertEqual(error.exception.code, code)

    def test_discount_can_bring_gross_overflow_back_into_range_or_total_to_zero(self):
        result = calculate_document_totals([self.item('1', '999999999999.99')], tax_rate=Decimal('100'),
                                           discount_type=DiscountType.FIXED, discount_value=Decimal('999999999999.99'))
        self.assertEqual(result.total, Decimal('999999999999.99'))
        result = calculate_document_totals([self.item()], tax_rate=Decimal('16'),
                                           discount_type=DiscountType.FIXED, discount_value=Decimal('116'))
        self.assertEqual(str(result.total), '0.00')

    def test_output_is_immutable_and_independent_of_source_edits(self):
        item = self.item()
        result = calculate_document_totals([item])
        item.quantity = Decimal('2')
        self.assertEqual(result.items[0].quantity, Decimal('1'))
        with self.assertRaises(FrozenInstanceError):
            result.total = Decimal('0')
        with self.assertRaises(FrozenInstanceError):
            result.items[0].line_total = Decimal('0')

    def test_ambient_decimal_context_does_not_affect_or_leak_from_service(self):
        items = [self.item('1', '12345.67')]
        with localcontext() as caller:
            caller.prec = 3
            caller.rounding = ROUND_DOWN
            caller.traps[Inexact] = True
            result = calculate_document_totals(items, tax_rate=Decimal('16'),
                                               discount_type=DiscountType.PERCENTAGE, discount_value=Decimal('10'))
            self.assertEqual(str(result.total), '13086.41')
            self.assertEqual(caller.prec, 3)
            self.assertEqual(caller.rounding, ROUND_DOWN)
            self.assertTrue(caller.traps[Inexact])
