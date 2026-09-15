from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.common.numbering import next_receipt_number
from app.receipts.models import Receipt, ReceiptItem
from app.receipts.schemas import ReceiptCreate
from app.receipts.validation import validate_receipt_create


@dataclass(frozen=True)
class CreatedReceipt:
    receipt: Receipt
    items: tuple[ReceiptItem, ...]


def create_receipt(connection: Connection, *, user_id: UUID, payload: ReceiptCreate) -> CreatedReceipt:
    """Persist a parsed request for an authenticated owner, or roll everything back."""
    with connection.transaction():
        totals = validate_receipt_create(connection, user_id=user_id, payload=payload)
        number = next_receipt_number(connection, user_id=user_id)
        with connection.cursor(row_factory=class_row(Receipt)) as cursor:
            cursor.execute(
                '''INSERT INTO receipts
                   (user_id, client_id, receipt_number, issue_date, currency,
                    subtotal, tax_rate, tax_amount, discount_type, discount_value,
                    discount_amount, total, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *''',
                (user_id, payload.client_id, number, payload.issue_date,
                 payload.currency, totals.subtotal, totals.tax_rate, totals.tax_amount,
                 totals.discount_type.value, totals.discount_value, totals.discount_amount,
                 totals.total, payload.notes),
            )
            receipt = cursor.fetchone()
            if receipt is None:
                raise RuntimeError('Receipt insertion returned no row')
        items = []
        with connection.cursor(row_factory=class_row(ReceiptItem)) as cursor:
            for line in totals.items:
                cursor.execute(
                    '''INSERT INTO receipt_items
                       (receipt_id, description, quantity, unit_price, line_total, position)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING *''',
                    (receipt.id, line.description, line.quantity, line.unit_price, line.line_total, line.position),
                )
                item = cursor.fetchone()
                if item is None:
                    raise RuntimeError('Receipt item insertion returned no row')
                items.append(item)
        return CreatedReceipt(receipt=receipt, items=tuple(items))
