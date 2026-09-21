"""Quote-to-Invoice conversion validation and persistence primitives."""

from uuid import UUID

from psycopg import Connection

from app.common.errors import DomainError
from app.quotes.models import QuoteStatus
from app.quotes.queries import LoadedQuote, get_quote_for_user


def validate_quote_conversion_eligibility(
    connection: Connection, *, user_id: UUID, quote_id: UUID,
) -> LoadedQuote:
    """Load an owned quote and enforce the one-way conversion preconditions."""
    loaded = get_quote_for_user(connection, user_id=user_id, quote_id=quote_id, for_update=True)
    if loaded is None:
        raise DomainError('QUOTE_NOT_FOUND', 'Quote not found.', status_code=404)
    if connection.execute(
        'SELECT 1 FROM invoices WHERE user_id = %s AND source_quote_id = %s LIMIT 1',
        (user_id, quote_id),
    ).fetchone():
        raise DomainError('QUOTE_ALREADY_CONVERTED', 'This quote has already been converted to an invoice.',
                          status_code=409)
    if loaded.quote.status != QuoteStatus.ACCEPTED:
        raise DomainError('INVALID_QUOTE_STATUS', 'Only accepted quotes can be converted to invoices.',
                          status_code=409)
    return loaded
