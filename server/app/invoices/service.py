"""Atomic Invoice persistence using shared validation, totals, and numbering."""

from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row
from pydantic import ValidationError

from app.common.errors import DomainError
from app.common.numbering import next_invoice_number
from app.invoices.models import Invoice, InvoiceItem, InvoiceStatus
from app.invoices.queries import LoadedInvoice, get_invoice_for_user
from app.invoices.schemas import InvoiceCreate, InvoicePatch
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


def _get_mutable_invoice(connection: Connection, *, user_id: UUID, invoice_id: UUID) -> LoadedInvoice:
    loaded = get_invoice_for_user(connection, user_id=user_id, invoice_id=invoice_id, for_update=True)
    if loaded is None:
        raise DomainError('INVOICE_NOT_FOUND', 'Invoice not found.', status_code=404)
    if loaded.invoice.status != InvoiceStatus.DRAFT or loaded.invoice.source_quote_id is not None:
        raise DomainError('INVALID_INVOICE_STATUS', 'Only unlinked draft invoices can be changed or deleted.',
                          status_code=409)
    return loaded


def _insert_items(connection: Connection, *, invoice_id: UUID, totals) -> tuple[InvoiceItem, ...]:
    items = []
    with connection.cursor(row_factory=class_row(InvoiceItem)) as cursor:
        for line in totals.items:
            cursor.execute(
                '''INSERT INTO invoice_items
                   (invoice_id, description, quantity, unit_price, line_total, position)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING *''',
                (invoice_id, line.description, line.quantity, line.unit_price, line.line_total, line.position),
            )
            item = cursor.fetchone()
            if item is None:
                raise RuntimeError('Invoice item insertion returned no row')
            items.append(item)
    return tuple(items)


def update_invoice(
    connection: Connection, *, user_id: UUID, invoice_id: UUID, payload: InvoicePatch,
) -> CreatedInvoice:
    """Merge, validate and persist an unlinked draft invoice atomically."""
    with connection.transaction():
        loaded = _get_mutable_invoice(connection, user_id=user_id, invoice_id=invoice_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return CreatedInvoice(loaded.invoice, loaded.items)
        values = {field: getattr(loaded.invoice, field) for field in InvoiceCreate.model_fields if field != 'items'}
        values['items'] = [item.model_dump(include={'description', 'quantity', 'unit_price', 'position'})
                           for item in loaded.items]
        try:
            merged = InvoiceCreate.model_validate({**values, **changes})
        except ValidationError as exc:
            raise DomainError('VALIDATION_ERROR', 'Request validation failed.', status_code=422,
                              details={'errors': [{'loc': ['body', *error['loc']],
                                                   'type': error['type'], 'message': 'Invalid value.'}
                                                  for error in exc.errors()]}) from None
        totals = validate_invoice_create(connection, user_id=user_id, payload=merged)
        with connection.cursor(row_factory=class_row(Invoice)) as cursor:
            cursor.execute(
                '''UPDATE invoices SET client_id = %s, issue_date = %s, due_date = %s,
                   currency = %s, subtotal = %s, tax_rate = %s, tax_amount = %s,
                   discount_type = %s, discount_value = %s, discount_amount = %s,
                   total = %s, notes = %s, terms = %s
                   WHERE user_id = %s AND id = %s RETURNING *''',
                (merged.client_id, merged.issue_date, merged.due_date, merged.currency,
                 totals.subtotal, totals.tax_rate, totals.tax_amount, totals.discount_type.value,
                 totals.discount_value, totals.discount_amount, totals.total, merged.notes,
                 merged.terms, user_id, invoice_id),
            )
            invoice = cursor.fetchone()
            if invoice is None:
                raise RuntimeError('Invoice update returned no row')
        items = loaded.items
        if 'items' in changes:
            connection.execute('DELETE FROM invoice_items WHERE invoice_id = %s', (invoice_id,))
            items = _insert_items(connection, invoice_id=invoice_id, totals=totals)
        return CreatedInvoice(invoice, tuple(sorted(items, key=lambda item: (item.position, item.id))))


def delete_invoice(connection: Connection, *, user_id: UUID, invoice_id: UUID) -> None:
    """Delete only an owned, unlinked draft invoice with no receipt references."""
    with connection.transaction():
        _get_mutable_invoice(connection, user_id=user_id, invoice_id=invoice_id)
        if connection.execute(
            'SELECT 1 FROM receipts WHERE source_invoice_id = %s LIMIT 1', (invoice_id,),
        ).fetchone():
            raise DomainError('INVALID_INVOICE_STATUS', 'Receipt-linked invoices cannot be deleted.',
                              status_code=409)
        deleted = connection.execute(
            'DELETE FROM invoices WHERE user_id = %s AND id = %s RETURNING id',
            (user_id, invoice_id),
        ).fetchone()
        if deleted is None:
            raise RuntimeError('Invoice deletion returned no row')
