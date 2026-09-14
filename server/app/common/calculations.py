"""Authoritative Decimal calculations for billing documents."""

from collections.abc import Iterable
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from typing import Annotated

from pydantic import Field, TypeAdapter, ValidationError

from app.common.errors import DomainError
from app.common.enums import DiscountType
from app.common.line_items import LineItemInput

MONEY_QUANTUM = Decimal('0.01')
MAX_MONEY = Decimal('999999999999.99')

_MONEY_INPUT = TypeAdapter(Annotated[Decimal, Field(
    strict=True, ge=0, max_digits=14, decimal_places=2, allow_inf_nan=False,
)])
_TAX_RATE_INPUT = TypeAdapter(Annotated[Decimal, Field(
    strict=True, ge=0, max_digits=6, decimal_places=3, allow_inf_nan=False,
)])


def calculate_discount_amount(
    subtotal: Decimal, discount_type: DiscountType = DiscountType.NONE,
    discount_value: Decimal = Decimal('0'), *, tax_amount: Decimal = Decimal('0'),
) -> Decimal:
    """Derive a discount without allowing subtotal + tax - discount to be negative."""
    with localcontext(Context(prec=32, rounding=ROUND_HALF_UP)):
        for value, code, message in (
            (subtotal, 'INVALID_SUBTOTAL', 'Subtotal must be a valid nonnegative Decimal amount.'),
            (tax_amount, 'INVALID_TAX_AMOUNT', 'Tax amount must be a valid nonnegative Decimal amount.'),
            (discount_value, 'INVALID_DISCOUNT', 'Discount value must be a valid nonnegative Decimal amount.'),
        ):
            try:
                _MONEY_INPUT.validate_python(value)
            except ValidationError:
                raise DomainError(code, message, status_code=422) from None
        if not isinstance(discount_type, DiscountType):
            raise DomainError('INVALID_DISCOUNT', 'A valid DiscountType is required.', status_code=422)
        if discount_type == DiscountType.NONE:
            if discount_value != 0:
                raise DomainError('INVALID_DISCOUNT', 'NONE requires a zero discount value.', status_code=422)
            amount = Decimal('0.00')
        elif discount_type == DiscountType.PERCENTAGE:
            if discount_value > 100:
                raise DomainError('INVALID_DISCOUNT', 'Percentage discount cannot exceed 100.', status_code=422)
            amount = (subtotal * discount_value / Decimal('100')).quantize(MONEY_QUANTUM)
        else:
            amount = discount_value.quantize(MONEY_QUANTUM)
        if amount > subtotal + tax_amount:
            raise DomainError('INVALID_DISCOUNT', 'Discount cannot make the final total negative.', status_code=422)
        return amount.copy_abs()


def calculate_tax_amount(subtotal: Decimal, tax_rate: Decimal = Decimal('0')) -> Decimal:
    """Apply a percentage rate to a backend-derived subtotal, rounding once."""
    with localcontext(Context(prec=32, rounding=ROUND_HALF_UP)):
        try:
            subtotal = _MONEY_INPUT.validate_python(subtotal)
        except ValidationError:
            raise DomainError('INVALID_SUBTOTAL', 'Subtotal must be a valid nonnegative Decimal amount.',
                              status_code=422) from None
        try:
            tax_rate = _TAX_RATE_INPUT.validate_python(tax_rate)
        except ValidationError:
            raise DomainError('INVALID_TAX_RATE', 'Tax rate must be a valid nonnegative Decimal percentage.',
                              status_code=422) from None
        amount = (subtotal * tax_rate / Decimal('100')).quantize(MONEY_QUANTUM)
    if amount > MAX_MONEY:
        raise DomainError('TAX_AMOUNT_OUT_OF_RANGE', 'Tax amount exceeds the supported monetary range.',
                          status_code=422)
    return amount.copy_abs()


def calculate_subtotal(items: Iterable[LineItemInput]) -> Decimal:
    """Sum authoritative rounded line totals, checking the monetary range as we go."""
    return _sum_line_totals(calculate_line_total(item) for item in items)


def _sum_line_totals(line_totals: Iterable[Decimal]) -> Decimal:
    """Internal sum of backend-calculated, nonnegative monetary amounts."""
    with localcontext(Context(prec=32, rounding=ROUND_HALF_UP)):
        subtotal = Decimal('0.00')
        for line_total in line_totals:
            subtotal += line_total
            # Nonnegative line totals mean an overflow cannot be undone later.
            if subtotal > MAX_MONEY:
                raise DomainError(
                    'SUBTOTAL_OUT_OF_RANGE', 'Subtotal exceeds the supported monetary range.',
                    status_code=422,
                )
        return subtotal


def calculate_line_total(item: LineItemInput) -> Decimal:
    """Multiply validated inputs and round once to the persisted monetary scale."""
    # Valid inputs have at most 12 and 14 significant digits respectively.
    # An explicit context isolates precision, rounding, and traps from callers.
    with localcontext(Context(prec=32, rounding=ROUND_HALF_UP)):
        total = (item.quantity * item.unit_price).quantize(MONEY_QUANTUM)
    if total > MAX_MONEY:
        raise DomainError(
            'LINE_TOTAL_OUT_OF_RANGE', 'Line total exceeds the supported monetary range.',
            status_code=422,
        )
    return total.copy_abs()  # Canonicalize signed zero from a zero unit price.
