"""Read-only ownership and financial checks before Quote creation."""

from uuid import UUID

from psycopg import Connection

from app.clients.queries import get_client_for_user
from app.common.errors import DomainError
from app.common.totals import DocumentTotals, calculate_document_totals
from app.quotes.schemas import QuoteCreate


def validate_quote_create(
    connection: Connection, *, user_id: UUID, payload: QuoteCreate,
) -> DocumentTotals:
    """Use an authenticated owner ID and parsed request; allocate or persist nothing."""
    client = get_client_for_user(connection, user_id=user_id, client_id=payload.client_id, for_update=True)
    if client is None:
        raise DomainError('CLIENT_NOT_FOUND', 'Client not found.', status_code=404)
    return calculate_document_totals(
        payload.items, tax_rate=payload.tax_rate, discount_type=payload.discount_type,
        discount_value=payload.discount_value,
    )
