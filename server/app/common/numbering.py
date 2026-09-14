"""Transactional per-user document-number allocation."""

from uuid import UUID

from psycopg import Connection

from app.common.errors import DomainError


def next_quote_number(connection: Connection, *, user_id: UUID) -> str:
    """Call inside quote creation's transaction to roll back allocation with it."""
    with connection.transaction():
        row = connection.execute(
            '''INSERT INTO quote_number_counters (user_id, last_number) VALUES (%s, 1)
               ON CONFLICT (user_id) DO UPDATE
               SET last_number = quote_number_counters.last_number + 1
               WHERE quote_number_counters.last_number < 9223372036854775807
               RETURNING last_number''',
            (user_id,),
        ).fetchone()
        if row is None:
            raise DomainError('QUOTE_NUMBER_EXHAUSTED', 'Quote number range is exhausted.', status_code=409)
        return f'QT-{row[0]:04d}'


def next_invoice_number(connection: Connection, *, user_id: UUID) -> str:
    """Call inside invoice creation's transaction to roll back allocation with it."""
    with connection.transaction():
        row = connection.execute(
            '''INSERT INTO invoice_number_counters (user_id, last_number) VALUES (%s, 1)
               ON CONFLICT (user_id) DO UPDATE
               SET last_number = invoice_number_counters.last_number + 1
               WHERE invoice_number_counters.last_number < 9223372036854775807
               RETURNING last_number''',
            (user_id,),
        ).fetchone()
        if row is None:
            raise DomainError('INVOICE_NUMBER_EXHAUSTED', 'Invoice number range is exhausted.', status_code=409)
        return f'INV-{row[0]:04d}'
