from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.clients.models import Client
from app.receipts.models import Receipt, ReceiptItem


@dataclass(frozen=True)
class LoadedReceipt:
    receipt: Receipt
    items: tuple[ReceiptItem, ...]
    client: Client


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
) -> tuple[list[LoadedReceipt], int]:
    if not 1 <= page <= 2147483647 or not 1 <= page_size <= 100:
        raise ValueError('Invalid receipt pagination bounds')
    total = connection.execute('SELECT count(*) FROM receipts WHERE user_id = %s',
                               (user_id,)).fetchone()[0]
    with connection.transaction():
        with connection.cursor(row_factory=class_row(Receipt)) as cursor:
            cursor.execute(
                'SELECT * FROM receipts WHERE user_id = %s '
                'ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s FOR SHARE',
                (user_id, page_size, (page - 1) * page_size),
            )
            receipts = cursor.fetchall()
        return _load_related(connection, user_id=user_id, receipts=receipts), total
