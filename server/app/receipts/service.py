from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row
from pydantic import ValidationError

from app.common.errors import DomainError
from app.common.numbering import next_receipt_number
from app.receipts.models import Receipt, ReceiptItem
from app.receipts.queries import LoadedReceipt, get_receipt_for_user
from app.receipts.schemas import ReceiptCreate, ReceiptPatch
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
        return CreatedReceipt(receipt=receipt, items=_insert_items(
            connection, receipt_id=receipt.id, totals=totals,
        ))


def _insert_items(connection: Connection, *, receipt_id: UUID, totals) -> tuple[ReceiptItem, ...]:
    items = []
    with connection.cursor(row_factory=class_row(ReceiptItem)) as cursor:
        for line in totals.items:
            cursor.execute(
                '''INSERT INTO receipt_items
                   (receipt_id, description, quantity, unit_price, line_total, position)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING *''',
                (receipt_id, line.description, line.quantity, line.unit_price, line.line_total, line.position),
            )
            item = cursor.fetchone()
            if item is None:
                raise RuntimeError('Receipt item insertion returned no row')
            items.append(item)
    return tuple(items)


def _get_mutable_receipt(connection: Connection, *, user_id: UUID, receipt_id: UUID) -> LoadedReceipt:
    loaded = get_receipt_for_user(connection, user_id=user_id, receipt_id=receipt_id, for_update=True)
    if loaded is None:
        raise DomainError('RECEIPT_NOT_FOUND', 'Receipt not found.', status_code=404)
    if loaded.receipt.source_invoice_id is not None:
        raise DomainError('INVALID_RECEIPT_STATUS', 'Invoice-linked receipts cannot be changed or deleted.',
                          status_code=409)
    return loaded


def update_receipt(
    connection: Connection, *, user_id: UUID, receipt_id: UUID, payload: ReceiptPatch,
) -> CreatedReceipt:
    """Merge and persist a direct Receipt atomically under its row lock."""
    with connection.transaction():
        loaded = _get_mutable_receipt(connection, user_id=user_id, receipt_id=receipt_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return CreatedReceipt(loaded.receipt, loaded.items)
        values = {field: getattr(loaded.receipt, field) for field in ReceiptCreate.model_fields if field != 'items'}
        values['items'] = [item.model_dump(include={'description', 'quantity', 'unit_price', 'position'})
                           for item in loaded.items]
        try:
            merged = ReceiptCreate.model_validate({**values, **changes})
        except ValidationError as exc:
            raise DomainError('VALIDATION_ERROR', 'Request validation failed.', status_code=422,
                              details={'errors': [{'loc': ['body', *error['loc']],
                                                   'type': error['type'], 'message': 'Invalid value.'}
                                                  for error in exc.errors()]}) from None
        totals = validate_receipt_create(connection, user_id=user_id, payload=merged)
        with connection.cursor(row_factory=class_row(Receipt)) as cursor:
            cursor.execute(
                '''UPDATE receipts SET client_id = %s, issue_date = %s, currency = %s,
                   subtotal = %s, tax_rate = %s, tax_amount = %s,
                   discount_type = %s, discount_value = %s, discount_amount = %s,
                   total = %s, notes = %s
                   WHERE user_id = %s AND id = %s RETURNING *''',
                (merged.client_id, merged.issue_date, merged.currency, totals.subtotal,
                 totals.tax_rate, totals.tax_amount, totals.discount_type.value,
                 totals.discount_value, totals.discount_amount, totals.total, merged.notes,
                 user_id, receipt_id),
            )
            receipt = cursor.fetchone()
            if receipt is None:
                raise RuntimeError('Receipt update returned no row')
        items = loaded.items
        if 'items' in changes:
            connection.execute('DELETE FROM receipt_items WHERE receipt_id = %s', (receipt_id,))
            items = _insert_items(connection, receipt_id=receipt_id, totals=totals)
        return CreatedReceipt(receipt, tuple(sorted(items, key=lambda item: (item.position, item.id))))


def delete_receipt(connection: Connection, *, user_id: UUID, receipt_id: UUID) -> None:
    """Delete only an owned, direct Receipt; its items cascade transactionally."""
    with connection.transaction():
        _get_mutable_receipt(connection, user_id=user_id, receipt_id=receipt_id)
        deleted = connection.execute(
            'DELETE FROM receipts WHERE user_id = %s AND id = %s RETURNING id',
            (user_id, receipt_id),
        ).fetchone()
        if deleted is None:
            raise RuntimeError('Receipt deletion returned no row')
