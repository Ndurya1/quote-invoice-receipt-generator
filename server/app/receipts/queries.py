from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.clients.models import Client
from app.common.errors import DomainError
from app.common.pagination import validate_pagination
from app.receipts.models import Receipt, ReceiptItem


@dataclass(frozen=True)
class LoadedReceipt:
    receipt: Receipt
    items: tuple[ReceiptItem, ...]
    client: Client


RECEIPT_SORTS = {
    'created_at': 'r.created_at',
    'issue_date': 'r.issue_date',
    'receipt_number': 'r.receipt_number',
    'total': 'r.total',
    'id': 'r.id',
}


def _receipt_order(sort: str | None) -> str:
    requested = sort or '-created_at'
    descending = requested.startswith('-')
    field = requested[1:] if descending else requested
    if field not in RECEIPT_SORTS:
        raise DomainError('VALIDATION_ERROR', 'Request validation failed.', status_code=422)
    direction = 'DESC' if descending else 'ASC'
    tie_direction = 'DESC' if descending else 'ASC'
    return f'{RECEIPT_SORTS[field]} {direction}, r.id {tie_direction}'


def _load_related(
    connection: Connection, *, user_id: UUID, receipts: list[Receipt],
) -> list[LoadedReceipt]:
    if not receipts:
        return []
    with connection.cursor(row_factory=class_row(Client)) as cursor:
        cursor.execute('SELECT * FROM clients WHERE user_id = %s AND id = ANY(%s)',
                       (user_id, list({r.client_id for r in receipts})))
        clients = {client.id: client for client in cursor.fetchall()}
    items = {r.id: [] for r in receipts}
    with connection.cursor(row_factory=class_row(ReceiptItem)) as cursor:
        cursor.execute('SELECT i.* FROM receipt_items i JOIN receipts r ON r.id = i.receipt_id '
                       'WHERE r.user_id = %s AND r.id = ANY(%s) '
                       'ORDER BY i.position, i.id', (user_id, list(items)))
        for item in cursor.fetchall():
            items[item.receipt_id].append(item)
    return [LoadedReceipt(r, tuple(items[r.id]), clients[r.client_id]) for r in receipts]


def get_receipt_for_user(
    connection: Connection, *, user_id: UUID, receipt_id: UUID, for_update: bool = False,
) -> LoadedReceipt | None:
    """Load one owned receipt and its items from one consistent snapshot."""
    with connection.transaction():
        with connection.cursor(row_factory=class_row(Receipt)) as cursor:
            cursor.execute(
                'SELECT * FROM receipts WHERE user_id = %s AND id = %s'
                + (' FOR UPDATE' if for_update else ' FOR SHARE'),
                (user_id, receipt_id),
            )
            receipt = cursor.fetchone()
        return _load_related(connection, user_id=user_id, receipts=[receipt])[0] if receipt else None


def paginate_receipts_for_user(
    connection: Connection, *, user_id: UUID, page: int, page_size: int,
    client_id: UUID | None = None, search: str | None = None,
    sort: str | None = None,
) -> tuple[list[LoadedReceipt], int]:
    pagination = validate_pagination(page, page_size)
    order_by = _receipt_order(sort)
    conditions = ['r.user_id = %s']
    parameters: list[object] = [user_id]
    if client_id is not None:
        conditions.append('r.client_id = %s')
        parameters.append(client_id)
    if search:
        conditions.append(
            '(r.receipt_number ILIKE %s OR c.name ILIKE %s OR r.notes ILIKE %s)'
        )
        pattern = f'%{search}%'
        parameters.extend([pattern] * 3)
    where = ' AND '.join(conditions)
    total = connection.execute(
        f'SELECT count(*) FROM receipts r JOIN clients c ON c.id = r.client_id '
        f'WHERE {where}', tuple(parameters),
    ).fetchone()[0]
    with connection.transaction():
        with connection.cursor(row_factory=class_row(Receipt)) as cursor:
            cursor.execute(
                f'SELECT r.* FROM receipts r JOIN clients c ON c.id = r.client_id '
                f'WHERE {where} ORDER BY {order_by} LIMIT %s OFFSET %s FOR SHARE',
                (*parameters, pagination.page_size, pagination.offset),
            )
            receipts = cursor.fetchall()
        return _load_related(connection, user_id=user_id, receipts=receipts), total
