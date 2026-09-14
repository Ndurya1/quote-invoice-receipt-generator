"""Authoritative Decimal calculations for billing documents."""

from collections.abc import Iterable
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext

from app.common.errors import DomainError
from app.common.line_items import LineItemInput

MONEY_QUANTUM = Decimal('0.01')
MAX_MONEY = Decimal('999999999999.99')


def calculate_subtotal(items: Iterable[LineItemInput]) -> Decimal:
    """Sum authoritative rounded line totals, checking the monetary range as we go."""
    with localcontext(Context(prec=32, rounding=ROUND_HALF_UP)):
        subtotal = Decimal('0.00')
        for item in items:
            subtotal += calculate_line_total(item)
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
