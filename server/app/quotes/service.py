"""Atomic Quote persistence using shared validation, totals, and numbering."""

from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection, errors
from psycopg.rows import class_row
from pydantic import ValidationError

from app.common.errors import DomainError
from app.common.numbering import next_quote_number
from app.common.totals import DocumentTotals
from app.quotes.models import Quote, QuoteItem, QuoteStatus
from app.quotes.queries import LoadedQuote, get_quote_for_user
from app.quotes.schemas import QuoteCreate, QuotePatch
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
        return CreatedQuote(quote=quote, items=_insert_items(connection, quote_id=quote.id, totals=totals))


def _insert_items(connection: Connection, *, quote_id: UUID, totals: DocumentTotals) -> tuple[QuoteItem, ...]:
    """Insert calculated items inside the caller's transaction."""
    items = []
    with connection.cursor(row_factory=class_row(QuoteItem)) as cursor:
        for line in totals.items:
            cursor.execute(
                '''INSERT INTO quote_items
                   (quote_id, description, quantity, unit_price, line_total, position)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING *''',
                (quote_id, line.description, line.quantity, line.unit_price, line.line_total, line.position),
            )
            item = cursor.fetchone()
            if item is None:
                raise RuntimeError('Quote item insertion returned no row')
            items.append(item)
    return tuple(items)


def _get_mutable_quote(connection: Connection, *, user_id: UUID, quote_id: UUID) -> LoadedQuote:
    """Lock before checking status or lineage; only unlinked drafts are mutable."""
    loaded = get_quote_for_user(connection, user_id=user_id, quote_id=quote_id, for_update=True)
    if loaded is None:
        raise DomainError('QUOTE_NOT_FOUND', 'Quote not found.', status_code=404)
    if loaded.quote.status != QuoteStatus.DRAFT or connection.execute(
        'SELECT 1 FROM invoices WHERE source_quote_id = %s', (quote_id,),
    ).fetchone():
        raise DomainError('INVALID_QUOTE_STATUS', 'Only unlinked draft quotes can be changed or deleted.',
                          status_code=409)
    return loaded


def update_quote(
    connection: Connection, *, user_id: UUID, quote_id: UUID, payload: QuotePatch,
) -> CreatedQuote:
    """Merge, validate and persist a complete draft atomically under its row lock."""
    with connection.transaction():
        loaded = _get_mutable_quote(connection, user_id=user_id, quote_id=quote_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return CreatedQuote(loaded.quote, loaded.items)
        values = {field: getattr(loaded.quote, field) for field in QuoteCreate.model_fields if field != 'items'}
        values['items'] = [item.model_dump(include={'description', 'quantity', 'unit_price', 'position'})
                           for item in loaded.items]
        try:
            merged = QuoteCreate.model_validate({**values, **changes})
        except ValidationError as exc:
            # Match request validation semantics without leaking stored/raw input.
            raise DomainError('VALIDATION_ERROR', 'Request validation failed.', status_code=422,
                              details={'errors': [{'loc': ['body', *error['loc']],
                                                   'type': error['type'], 'message': 'Invalid value.'}
                                                  for error in exc.errors()]}) from None
        totals = validate_quote_create(connection, user_id=user_id, payload=merged)
        with connection.cursor(row_factory=class_row(Quote)) as cursor:
            cursor.execute(
                '''UPDATE quotes SET client_id = %s, issue_date = %s, expiry_date = %s,
                   currency = %s, subtotal = %s, tax_rate = %s, tax_amount = %s,
                   discount_type = %s, discount_value = %s, discount_amount = %s,
                   total = %s, notes = %s, terms = %s
                   WHERE user_id = %s AND id = %s RETURNING *''',
                (merged.client_id, merged.issue_date, merged.expiry_date, merged.currency,
                 totals.subtotal, totals.tax_rate, totals.tax_amount, totals.discount_type.value,
                 totals.discount_value, totals.discount_amount, totals.total, merged.notes,
                 merged.terms, user_id, quote_id),
            )
            quote = cursor.fetchone()
            if quote is None:
                raise RuntimeError('Quote update returned no row')
        items = loaded.items
        if 'items' in changes:
            connection.execute('DELETE FROM quote_items WHERE quote_id = %s', (quote_id,))
            items = _insert_items(connection, quote_id=quote_id, totals=totals)
        return CreatedQuote(quote, tuple(sorted(items, key=lambda item: (item.position, item.id))))


def delete_quote(connection: Connection, *, user_id: UUID, quote_id: UUID) -> None:
    """Delete only an owned, unlinked draft; its own items cascade in the transaction."""
    try:
        with connection.transaction():
            _get_mutable_quote(connection, user_id=user_id, quote_id=quote_id)
            deleted = connection.execute(
                'DELETE FROM quotes WHERE user_id = %s AND id = %s RETURNING id',
                (user_id, quote_id),
            ).fetchone()
            if deleted is None:
                raise RuntimeError('Quote deletion returned no row')
    except (errors.ForeignKeyViolation, errors.RestrictViolation) as exc:
        if exc.diag.constraint_name != 'invoices_source_quote_id_fkey':
            raise
        raise DomainError('INVALID_QUOTE_STATUS', 'Invoice-linked quotes cannot be deleted.',
                          status_code=409) from None
