"""Invoice-to-Receipt conversion validation and persistence primitives."""

from datetime import date
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row
from psycopg.rows import class_row

from app.common.errors import DomainError
from app.common.numbering import next_receipt_number
from app.invoices.models import InvoiceStatus
from app.invoices.queries import LoadedInvoice, get_invoice_for_user
from app.receipts.models import Receipt
from app.receipts.schemas import ReceiptCreate
from app.receipts.service import CreatedReceipt, _insert_items
from app.receipts.validation import validate_receipt_create


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


def convert_invoice_to_receipt(
    connection: Connection, *, user_id: UUID, invoice_id: UUID, issue_date: date,
) -> CreatedReceipt:
    """Convert an eligible Invoice to an independent Receipt atomically."""
    with connection.transaction():
        loaded = validate_invoice_conversion_eligibility(
            connection, user_id=user_id, invoice_id=invoice_id,
        )
        receipt_payload = ReceiptCreate(
            client_id=loaded.invoice.client_id,
            issue_date=issue_date,
            currency=loaded.invoice.currency,
            tax_rate=loaded.invoice.tax_rate,
            discount_type=loaded.invoice.discount_type,
            discount_value=loaded.invoice.discount_value,
            notes=loaded.invoice.notes,
            items=[{
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'position': item.position,
            } for item in loaded.items],
        )
        totals = validate_receipt_create(connection, user_id=user_id, payload=receipt_payload)
        number = next_receipt_number(connection, user_id=user_id)
        with connection.cursor(row_factory=class_row(Receipt)) as cursor:
            cursor.execute(
                '''INSERT INTO receipts
                   (user_id, client_id, source_invoice_id, receipt_number, issue_date, currency,
                    subtotal, tax_rate, tax_amount, discount_type, discount_value,
                    discount_amount, total, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *''',
                (user_id, receipt_payload.client_id, invoice_id, number, receipt_payload.issue_date,
                 receipt_payload.currency, totals.subtotal, totals.tax_rate, totals.tax_amount,
                 totals.discount_type.value, totals.discount_value, totals.discount_amount,
                 totals.total, receipt_payload.notes),
            )
            receipt = cursor.fetchone()
            if receipt is None:
                raise RuntimeError('Converted receipt insertion returned no row')
        items = _insert_items(connection, receipt_id=receipt.id, totals=totals)
        return CreatedReceipt(receipt=receipt, items=items)
