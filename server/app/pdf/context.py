"""Build PDF contexts from owner-scoped persisted records."""

from uuid import UUID

from psycopg import Connection

from app.business.models import BusinessProfile
from app.business.queries import get_profile_for_user
from app.common.errors import DomainError
from app.pdf.models import DocumentRenderContext, RenderItem
from app.invoices.queries import get_invoice_for_user
from app.quotes.queries import get_quote_for_user
from app.receipts.queries import get_receipt_for_user


def _render_items(items) -> tuple[RenderItem, ...]:
    return tuple(RenderItem(
        description=item.description,
        quantity=item.quantity,
        unit_price=item.unit_price,
        line_total=item.line_total,
    ) for item in items)


def _business(connection: Connection, *, user_id: UUID) -> BusinessProfile | None:
    return get_profile_for_user(connection, user_id)


def build_quote_context(
    connection: Connection, *, user_id: UUID, quote_id: UUID,
) -> DocumentRenderContext:
    loaded = get_quote_for_user(connection, user_id=user_id, quote_id=quote_id)
    if loaded is None:
        raise DomainError('QUOTE_NOT_FOUND', 'Quote not found.', status_code=404)
    quote = loaded.quote
    return DocumentRenderContext(
        document_type='quote', document_id=quote.id, document_number=quote.quote_number,
        issue_date=quote.issue_date, secondary_date=quote.expiry_date,
        currency=quote.currency, subtotal=quote.subtotal, tax_rate=quote.tax_rate,
        tax_amount=quote.tax_amount, discount_type=quote.discount_type,
        discount_value=quote.discount_value, discount_amount=quote.discount_amount,
        total=quote.total, status=quote.status.value, notes=quote.notes, terms=quote.terms,
        client=loaded.client, business=_business(connection, user_id=user_id),
        items=_render_items(loaded.items),
        created_at=quote.created_at,
    )


def build_invoice_context(
    connection: Connection, *, user_id: UUID, invoice_id: UUID,
) -> DocumentRenderContext:
    loaded = get_invoice_for_user(connection, user_id=user_id, invoice_id=invoice_id)
    if loaded is None:
        raise DomainError('INVOICE_NOT_FOUND', 'Invoice not found.', status_code=404)
    invoice = loaded.invoice
    return DocumentRenderContext(
        document_type='invoice', document_id=invoice.id, document_number=invoice.invoice_number,
        issue_date=invoice.issue_date, secondary_date=invoice.due_date,
        currency=invoice.currency, subtotal=invoice.subtotal, tax_rate=invoice.tax_rate,
        tax_amount=invoice.tax_amount, discount_type=invoice.discount_type,
        discount_value=invoice.discount_value, discount_amount=invoice.discount_amount,
        total=invoice.total, status=invoice.status.value, notes=invoice.notes, terms=invoice.terms,
        client=_client_from_invoice(connection, user_id=user_id, client_id=invoice.client_id),
        business=_business(connection, user_id=user_id),
        items=_render_items(loaded.items),
        created_at=invoice.created_at,
    )


def build_receipt_context(
    connection: Connection, *, user_id: UUID, receipt_id: UUID,
) -> DocumentRenderContext:
    loaded = get_receipt_for_user(connection, user_id=user_id, receipt_id=receipt_id)
    if loaded is None:
        raise DomainError('RECEIPT_NOT_FOUND', 'Receipt not found.', status_code=404)
    receipt = loaded.receipt
    return DocumentRenderContext(
        document_type='receipt', document_id=receipt.id, document_number=receipt.receipt_number,
        issue_date=receipt.issue_date, secondary_date=None,
        currency=receipt.currency, subtotal=receipt.subtotal, tax_rate=receipt.tax_rate,
        tax_amount=receipt.tax_amount, discount_type=receipt.discount_type,
        discount_value=receipt.discount_value, discount_amount=receipt.discount_amount,
        total=receipt.total, status=None, notes=receipt.notes, terms=None,
        client=loaded.client, business=_business(connection, user_id=user_id),
        items=_render_items(loaded.items),
        created_at=receipt.created_at,
    )


def _client_from_invoice(connection: Connection, *, user_id: UUID, client_id: UUID):
    from app.clients.queries import get_client_for_user

    client = get_client_for_user(connection, user_id=user_id, client_id=client_id)
    if client is None:
        raise DomainError('INVOICE_NOT_FOUND', 'Invoice not found.', status_code=404)
    return client
