"""Owner-scoped Quote reads with batched related rows."""

from dataclasses import dataclass
from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.clients.models import Client
from app.common.pagination import validate_pagination
from app.common.errors import DomainError
from app.quotes.models import Quote, QuoteItem


@dataclass(frozen=True)
class LoadedQuote:
    quote: Quote
    items: tuple[QuoteItem, ...]
    client: Client


QUOTE_SORTS = {
    'created_at': 'q.created_at',
    'issue_date': 'q.issue_date',
    'expiry_date': 'q.expiry_date',
    'quote_number': 'q.quote_number',
    'total': 'q.total',
    'status': 'q.status',
    'id': 'q.id',
}


def _quote_order(sort: str | None) -> str:
    requested = sort or '-created_at'
    descending = requested.startswith('-')
    field = requested[1:] if descending else requested
    if field not in QUOTE_SORTS:
        raise DomainError('VALIDATION_ERROR', 'Request validation failed.', status_code=422)
    direction = 'DESC' if descending else 'ASC'
    tie_direction = 'DESC' if descending else 'ASC'
    return f'{QUOTE_SORTS[field]} {direction}, q.id {tie_direction}'


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
    # Keep parent fields and items from the same version while edits/deletes run.
    with connection.transaction():
        with connection.cursor(row_factory=class_row(Quote)) as cursor:
            cursor.execute('SELECT * FROM quotes WHERE user_id = %s AND id = %s'
                           + (' FOR UPDATE' if for_update else ' FOR SHARE'), (user_id, quote_id))
            quote = cursor.fetchone()
        return _load_related(connection, user_id=user_id, quotes=[quote])[0] if quote else None


def paginate_quotes_for_user(
    connection: Connection, *, user_id: UUID, page: int, page_size: int,
    status: str | None = None, client_id: UUID | None = None,
    search: str | None = None, sort: str | None = None,
) -> tuple[list[LoadedQuote], int]:
    pagination = validate_pagination(page, page_size)
    order_by = _quote_order(sort)
    conditions = ['q.user_id = %s']
    parameters: list[object] = [user_id]
    if status is not None:
        conditions.append('q.status = %s')
        parameters.append(status)
    if client_id is not None:
        conditions.append('q.client_id = %s')
        parameters.append(client_id)
    if search:
        conditions.append(
            '(q.quote_number ILIKE %s OR c.name ILIKE %s OR q.notes ILIKE %s OR q.terms ILIKE %s)'
        )
        pattern = f'%{search}%'
        parameters.extend([pattern] * 4)
    where = ' AND '.join(conditions)
    total = connection.execute(
        f'SELECT count(*) FROM quotes q JOIN clients c ON c.id = q.client_id '
        f'WHERE {where}', tuple(parameters),
    ).fetchone()[0]
    with connection.transaction():
        with connection.cursor(row_factory=class_row(Quote)) as cursor:
            cursor.execute(
                f'SELECT q.* FROM quotes q JOIN clients c ON c.id = q.client_id '
                f'WHERE {where} ORDER BY {order_by} LIMIT %s OFFSET %s FOR SHARE',
                (*parameters, pagination.page_size, pagination.offset),
            )
            quotes = cursor.fetchall()
        return _load_related(connection, user_id=user_id, quotes=quotes), total
