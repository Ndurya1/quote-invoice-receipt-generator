"""Atomic Invoice persistence using shared validation, totals, and numbering."""

from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.common.numbering import next_invoice_number
from app.invoices.models import Invoice, InvoiceItem
from app.invoices.schemas import InvoiceCreate
from app.invoices.validation import validate_invoice_create


@dataclass(frozen=True)
class CreatedInvoice:
    invoice: Invoice
    items: tuple[InvoiceItem, ...]


def create_invoice(connection: Connection, *, user_id: UUID, payload: InvoiceCreate) -> CreatedInvoice:
    """Persist a parsed request for an authenticated owner, or roll everything back."""
    with connection.transaction():
        totals = validate_invoice_create(connection, user_id=user_id, payload=payload)
        number = next_invoice_number(connection, user_id=user_id)
        with connection.cursor(row_factory=class_row(Invoice)) as cursor:
            cursor.execute(
                '''INSERT INTO invoices
                   (user_id, client_id, invoice_number, issue_date, due_date, currency,
                    subtotal, tax_rate, tax_amount, discount_type, discount_value,
                    discount_amount, total, notes, terms)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *''',
                (user_id, payload.client_id, number, payload.issue_date, payload.due_date,
                 payload.currency, totals.subtotal, totals.tax_rate, totals.tax_amount,
                 totals.discount_type.value, totals.discount_value, totals.discount_amount,
                 totals.total, payload.notes, payload.terms),
            )
            invoice = cursor.fetchone()
            if invoice is None:
                raise RuntimeError('Invoice insertion returned no row')
        items = []
        with connection.cursor(row_factory=class_row(InvoiceItem)) as cursor:
            for line in totals.items:
                cursor.execute(
                    '''INSERT INTO invoice_items
                       (invoice_id, description, quantity, unit_price, line_total, position)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING *''',
                    (invoice.id, line.description, line.quantity, line.unit_price, line.line_total, line.position),
                )
                item = cursor.fetchone()
                if item is None:
                    raise RuntimeError('Invoice item insertion returned no row')
                items.append(item)
        return CreatedInvoice(invoice=invoice, items=tuple(items))
