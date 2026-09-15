"""Atomic Quote persistence using shared validation, totals, and numbering."""

from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.common.numbering import next_quote_number
from app.quotes.models import Quote, QuoteItem
from app.quotes.schemas import QuoteCreate
from app.quotes.validation import validate_quote_create


@dataclass(frozen=True)
class CreatedQuote:
    quote: Quote
    items: tuple[QuoteItem, ...]


def create_quote(connection: Connection, *, user_id: UUID, payload: QuoteCreate) -> CreatedQuote:
    """Persist a parsed request for an authenticated owner, or roll everything back."""
    with connection.transaction():
        totals = validate_quote_create(connection, user_id=user_id, payload=payload)
        number = next_quote_number(connection, user_id=user_id)
        with connection.cursor(row_factory=class_row(Quote)) as cursor:
            cursor.execute(
                '''INSERT INTO quotes
                   (user_id, client_id, quote_number, issue_date, expiry_date, currency,
                    subtotal, tax_rate, tax_amount, discount_type, discount_value,
                    discount_amount, total, notes, terms)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *''',
                (user_id, payload.client_id, number, payload.issue_date, payload.expiry_date,
                 payload.currency, totals.subtotal, totals.tax_rate, totals.tax_amount,
                 totals.discount_type.value, totals.discount_value, totals.discount_amount,
                 totals.total, payload.notes, payload.terms),
            )
            quote = cursor.fetchone()
            if quote is None:
                raise RuntimeError('Quote insertion returned no row')
        items = []
        with connection.cursor(row_factory=class_row(QuoteItem)) as cursor:
            for line in totals.items:
                cursor.execute(
                    '''INSERT INTO quote_items
                       (quote_id, description, quantity, unit_price, line_total, position)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING *''',
                    (quote.id, line.description, line.quantity, line.unit_price, line.line_total, line.position),
                )
                item = cursor.fetchone()
                if item is None:
                    raise RuntimeError('Quote item insertion returned no row')
                items.append(item)
        return CreatedQuote(quote=quote, items=tuple(items))
