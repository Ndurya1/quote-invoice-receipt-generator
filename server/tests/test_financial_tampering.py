import json
import unittest
from decimal import Decimal

from pydantic import TypeAdapter, ValidationError

from app.common.enums import DiscountType
from app.common.line_items import LineItemInput
from app.common.totals import calculate_document_totals

COMPUTED_FIELDS = ('line_total', 'subtotal', 'tax_amount', 'discount_amount', 'total')


class FinancialTamperingTests(unittest.TestCase):
    def line_payload(self):
        return {'description': 'Work', 'quantity': '2', 'unit_price': '50.00'}

    def test_json_line_items_reject_each_injected_computed_field(self):
        adapter = TypeAdapter(list[LineItemInput])
        for field in COMPUTED_FIELDS:
            for forged in ('0.00', '-100.00', '999999999999.99', None, {'value': '0'}):
                with self.subTest(field=field, forged=forged), self.assertRaises(ValidationError) as error:
                    adapter.validate_json(json.dumps([
                        self.line_payload(), {**self.line_payload(), field: forged},
                    ]))
                self.assertEqual(error.exception.errors()[0]['loc'], (1, field))
                self.assertEqual(error.exception.errors()[0]['type'], 'extra_forbidden')

    def test_totals_service_refuses_each_submitted_computed_argument(self):
        item = LineItemInput.model_validate(self.line_payload())
        for field in COMPUTED_FIELDS:
            with self.subTest(field=field), self.assertRaises(TypeError):
                calculate_document_totals([item], **{field: Decimal('0.00')})
        with self.assertRaises(TypeError):
            calculate_document_totals([item], **dict.fromkeys(COMPUTED_FIELDS, Decimal('0.00')))

    def test_validated_inputs_produce_authoritative_values_after_rejected_tampering(self):
        payload = self.line_payload()
        with self.assertRaises(ValidationError):
            LineItemInput.model_validate({**payload, 'line_total': '1.00'})
        item = LineItemInput.model_validate_json(json.dumps(payload))
        result = calculate_document_totals(
            [item], tax_rate=Decimal('16'), discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal('10'),
        )
        self.assertEqual(result.items[0].line_total, Decimal('100.00'))
        self.assertEqual(result.subtotal, Decimal('100.00'))
        self.assertEqual(result.tax_amount, Decimal('16.00'))
        self.assertEqual(result.discount_amount, Decimal('10.00'))
        self.assertEqual(result.total, Decimal('106.00'))
