"""Quote-to-Invoice conversion validation and persistence primitives."""

from datetime import date
from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.common.errors import DomainError
from app.common.numbering import next_invoice_number
from app.invoices.models import Invoice, InvoiceItem
from app.invoices.schemas import InvoiceCreate
from app.invoices.service import CreatedInvoice, _insert_items
from app.invoices.validation import validate_invoice_create
from app.quotes.models import QuoteStatus
from app.quotes.queries import LoadedQuote, get_quote_for_user
from app.quotes.service import transition_quote


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


def convert_quote_to_invoice(
    connection: Connection, *, user_id: UUID, quote_id: UUID,
    issue_date: date, due_date: date | None,
) -> CreatedInvoice:
    """Convert an accepted Quote to an independent Invoice atomically."""
    with connection.transaction():
        loaded = validate_quote_conversion_eligibility(
            connection, user_id=user_id, quote_id=quote_id,
        )
        invoice_payload = InvoiceCreate(
            client_id=loaded.quote.client_id,
            issue_date=issue_date,
            due_date=due_date,
            currency=loaded.quote.currency,
            tax_rate=loaded.quote.tax_rate,
            discount_type=loaded.quote.discount_type,
            discount_value=loaded.quote.discount_value,
            notes=loaded.quote.notes,
            terms=loaded.quote.terms,
            items=[{
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'position': item.position,
            } for item in loaded.items],
        )
        totals = validate_invoice_create(connection, user_id=user_id, payload=invoice_payload)
        number = next_invoice_number(connection, user_id=user_id)
        with connection.cursor(row_factory=class_row(Invoice)) as cursor:
            cursor.execute(
                '''INSERT INTO invoices
                   (user_id, client_id, source_quote_id, invoice_number, issue_date, due_date,
                    currency, subtotal, tax_rate, tax_amount, discount_type, discount_value,
                    discount_amount, total, notes, terms)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *''',
                (user_id, invoice_payload.client_id, quote_id, number, invoice_payload.issue_date,
                 invoice_payload.due_date, invoice_payload.currency, totals.subtotal, totals.tax_rate,
                 totals.tax_amount, totals.discount_type.value, totals.discount_value,
                 totals.discount_amount, totals.total, invoice_payload.notes, invoice_payload.terms),
            )
            invoice = cursor.fetchone()
            if invoice is None:
                raise RuntimeError('Converted invoice insertion returned no row')
        items = _insert_items(connection, invoice_id=invoice.id, totals=totals)
        transition_quote(connection, user_id=user_id, quote_id=quote_id, target=QuoteStatus.CONVERTED)
        return CreatedInvoice(invoice=invoice, items=items)
