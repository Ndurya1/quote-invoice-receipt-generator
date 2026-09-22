"""Owner-scoped Invoice reads with batched line-item loading."""

from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.invoices.models import Invoice, InvoiceItem
from app.common.pagination import validate_pagination
from app.common.errors import DomainError


@dataclass(frozen=True)
class LoadedInvoice:
    invoice: Invoice
    items: tuple[InvoiceItem, ...]


INVOICE_SORTS = {
    'created_at': 'v.created_at',
    'issue_date': 'v.issue_date',
    'due_date': 'v.due_date',
    'invoice_number': 'v.invoice_number',
    'total': 'v.total',
    'status': 'v.status',
    'id': 'v.id',
}


def _invoice_order(sort: str | None) -> str:
    requested = sort or '-created_at'
    descending = requested.startswith('-')
    field = requested[1:] if descending else requested
    if field not in INVOICE_SORTS:
        raise DomainError('VALIDATION_ERROR', 'Request validation failed.', status_code=422)
    direction = 'DESC' if descending else 'ASC'
    tie_direction = 'DESC' if descending else 'ASC'
    return f'{INVOICE_SORTS[field]} {direction}, v.id {tie_direction}'


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
    status: str | None = None, client_id: UUID | None = None,
    search: str | None = None, sort: str | None = None,
) -> tuple[list[LoadedInvoice], int]:
    pagination = validate_pagination(page, page_size)
    order_by = _invoice_order(sort)
    conditions = ['v.user_id = %s']
    parameters: list[object] = [user_id]
    if status is not None:
        conditions.append('v.status = %s')
        parameters.append(status)
    if client_id is not None:
        conditions.append('v.client_id = %s')
        parameters.append(client_id)
    if search:
        conditions.append(
            '(v.invoice_number ILIKE %s OR c.name ILIKE %s OR v.notes ILIKE %s OR v.terms ILIKE %s)'
        )
        pattern = f'%{search}%'
        parameters.extend([pattern] * 4)
    where = ' AND '.join(conditions)
    total = connection.execute(
        f'SELECT count(*) FROM invoices v JOIN clients c ON c.id = v.client_id '
        f'WHERE {where}', tuple(parameters),
    ).fetchone()[0]
    with connection.transaction():
        with connection.cursor(row_factory=class_row(Invoice)) as cursor:
            cursor.execute(
                f'SELECT v.* FROM invoices v JOIN clients c ON c.id = v.client_id '
                f'WHERE {where} ORDER BY {order_by} LIMIT %s OFFSET %s FOR SHARE',
                (*parameters, pagination.page_size, pagination.offset),
            )
            invoices = cursor.fetchall()
        return _load_related(connection, user_id=user_id, invoices=invoices), total
