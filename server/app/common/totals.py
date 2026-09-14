"""Shared authoritative totals for all document types and conversions."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext

from app.common.calculations import (
    MAX_MONEY, MONEY_QUANTUM, _sum_line_totals, calculate_discount_amount,
    calculate_line_total, calculate_tax_amount,
)
from app.common.enums import DiscountType
from app.common.errors import DomainError
from app.common.line_items import LineItemInput


@dataclass(frozen=True)
class CalculatedLineItem:
    description: str
    quantity: Decimal
    unit_price: Decimal
    position: int
    line_total: Decimal


@dataclass(frozen=True)
class DocumentTotals:
    items: tuple[CalculatedLineItem, ...]
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    discount_type: DiscountType
    discount_value: Decimal
    discount_amount: Decimal
    total: Decimal


def calculate_document_totals(
    items: Iterable[LineItemInput], *, tax_rate: Decimal = Decimal('0'),
    discount_type: DiscountType = DiscountType.NONE, discount_value: Decimal = Decimal('0'),
) -> DocumentTotals:
    """Consume validated items once; derive every total without mutating inputs."""
    calculated = tuple(
        CalculatedLineItem(item.description, item.quantity, item.unit_price,
                           item.position, calculate_line_total(item))
        for item in items
    )
    if not calculated:
        raise DomainError('EMPTY_LINE_ITEMS', 'At least one line item is required.', status_code=422)
    subtotal = _sum_line_totals(item.line_total for item in calculated)
    tax_amount = calculate_tax_amount(subtotal, tax_rate)
    discount_amount = calculate_discount_amount(
        subtotal, discount_type, discount_value, tax_amount=tax_amount,
    )
    with localcontext(Context(prec=32, rounding=ROUND_HALF_UP)):
        total = (subtotal + tax_amount - discount_amount).quantize(MONEY_QUANTUM)
        if not 0 <= total <= MAX_MONEY:
            raise DomainError('TOTAL_OUT_OF_RANGE', 'Total exceeds the supported monetary range.',
                              status_code=422)
        return DocumentTotals(
            items=calculated, subtotal=subtotal,
            tax_rate=tax_rate.quantize(Decimal('0.001')).copy_abs(), tax_amount=tax_amount,
            discount_type=discount_type,
            discount_value=discount_value.quantize(MONEY_QUANTUM).copy_abs(),
            discount_amount=discount_amount, total=total.copy_abs(),
        )
