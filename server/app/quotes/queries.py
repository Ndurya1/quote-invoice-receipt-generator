"""Owner-scoped Quote reads with batched related rows."""

from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.clients.models import Client
from app.quotes.models import Quote, QuoteItem


@dataclass(frozen=True)
class LoadedQuote:
    quote: Quote
    items: tuple[QuoteItem, ...]
    client: Client


def _load_related(
    connection: Connection, *, user_id: UUID, quotes: list[Quote],
) -> list[LoadedQuote]:
    if not quotes:
        return []
    with connection.cursor(row_factory=class_row(Client)) as cursor:
        cursor.execute('SELECT * FROM clients WHERE user_id = %s AND id = ANY(%s)',
                       (user_id, list({q.client_id for q in quotes})))
        clients = {client.id: client for client in cursor.fetchall()}
    items = {q.id: [] for q in quotes}
    with connection.cursor(row_factory=class_row(QuoteItem)) as cursor:
        cursor.execute('SELECT i.* FROM quote_items i JOIN quotes q ON q.id = i.quote_id '
                       'WHERE q.user_id = %s AND q.id = ANY(%s) '
                       'ORDER BY i.position, i.id', (user_id, list(items)))
        for item in cursor.fetchall():
            items[item.quote_id].append(item)
    return [LoadedQuote(q, tuple(items[q.id]), clients[q.client_id]) for q in quotes]


def get_quote_for_user(
    connection: Connection, *, user_id: UUID, quote_id: UUID, for_update: bool = False,
) -> LoadedQuote | None:
    """Use for_update only inside the caller's mutation transaction."""
    with connection.cursor(row_factory=class_row(Quote)) as cursor:
        cursor.execute('SELECT * FROM quotes WHERE user_id = %s AND id = %s'
                       + (' FOR UPDATE' if for_update else ''), (user_id, quote_id))
        quote = cursor.fetchone()
    return _load_related(connection, user_id=user_id, quotes=[quote])[0] if quote else None


def paginate_quotes_for_user(
    connection: Connection, *, user_id: UUID, page: int, page_size: int,
) -> tuple[list[LoadedQuote], int]:
    if not 1 <= page <= 2147483647 or not 1 <= page_size <= 100:
        raise ValueError('Invalid quote pagination bounds')
    total = connection.execute('SELECT count(*) FROM quotes WHERE user_id = %s',
                               (user_id,)).fetchone()[0]
    with connection.cursor(row_factory=class_row(Quote)) as cursor:
        cursor.execute('SELECT * FROM quotes WHERE user_id = %s '
                       'ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s',
                       (user_id, page_size, (page - 1) * page_size))
        quotes = cursor.fetchall()
    return _load_related(connection, user_id=user_id, quotes=quotes), total
