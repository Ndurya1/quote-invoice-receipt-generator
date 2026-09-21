"""Invoice-to-Receipt conversion validation and persistence primitives."""

from uuid import UUID

from psycopg import Connection

from app.common.errors import DomainError
from app.invoices.models import InvoiceStatus
from app.invoices.queries import LoadedInvoice, get_invoice_for_user


def validate_invoice_conversion_eligibility(
    connection: Connection, *, user_id: UUID, invoice_id: UUID,
) -> LoadedInvoice:
    """Load an owned Invoice and enforce Invoice-to-Receipt preconditions."""
    loaded = get_invoice_for_user(connection, user_id=user_id, invoice_id=invoice_id, for_update=True)
    if loaded is None:
        raise DomainError('INVOICE_NOT_FOUND', 'Invoice not found.', status_code=404)
    if loaded.invoice.status == InvoiceStatus.CANCELLED:
        raise DomainError('INVALID_INVOICE_STATUS', 'Cancelled invoices cannot be converted to receipts.',
                          status_code=409)
    return loaded
