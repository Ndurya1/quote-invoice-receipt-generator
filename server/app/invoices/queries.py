"""Owner-scoped Invoice reads with batched line-item loading."""

from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.invoices.models import Invoice, InvoiceItem
from app.common.pagination import validate_pagination


@dataclass(frozen=True)
class LoadedInvoice:
    invoice: Invoice
    items: tuple[InvoiceItem, ...]


def _load_related(
    connection: Connection, *, user_id: UUID, invoices: list[Invoice],
) -> list[LoadedInvoice]:
    if not invoices:
        return []
    items = {invoice.id: [] for invoice in invoices}
    with connection.cursor(row_factory=class_row(InvoiceItem)) as cursor:
        cursor.execute(
            'SELECT i.* FROM invoice_items i JOIN invoices v ON v.id = i.invoice_id '
            'WHERE v.user_id = %s AND v.id = ANY(%s) '
            'ORDER BY i.position, i.id',
            (user_id, list(items)),
        )
        for item in cursor.fetchall():
            items[item.invoice_id].append(item)
    return [LoadedInvoice(invoice, tuple(items[invoice.id])) for invoice in invoices]


def get_invoice_for_user(
    connection: Connection, *, user_id: UUID, invoice_id: UUID, for_update: bool = False,
) -> LoadedInvoice | None:
    """Load one owned invoice and its items; lock it when mutating."""
    with connection.transaction():
        with connection.cursor(row_factory=class_row(Invoice)) as cursor:
            cursor.execute(
                'SELECT * FROM invoices WHERE user_id = %s AND id = %s'
                + (' FOR UPDATE' if for_update else ' FOR SHARE'),
                (user_id, invoice_id),
            )
            invoice = cursor.fetchone()
        return _load_related(connection, user_id=user_id, invoices=[invoice])[0] if invoice else None


def paginate_invoices_for_user(
    connection: Connection, *, user_id: UUID, page: int, page_size: int,
) -> tuple[list[LoadedInvoice], int]:
    pagination = validate_pagination(page, page_size)
    total = connection.execute(
        'SELECT count(*) FROM invoices WHERE user_id = %s', (user_id,)
    ).fetchone()[0]
    with connection.transaction():
        with connection.cursor(row_factory=class_row(Invoice)) as cursor:
            cursor.execute(
                'SELECT * FROM invoices WHERE user_id = %s '
                'ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s FOR SHARE',
                (user_id, pagination.page_size, pagination.offset),
            )
            invoices = cursor.fetchall()
        return _load_related(connection, user_id=user_id, invoices=invoices), total
