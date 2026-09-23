"""Client reads; callers must supply the owner ID from authentication."""

from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.clients.models import Client
from app.common.pagination import validate_pagination
from app.common.errors import DomainError


CLIENT_SORTS = {
    'name': 'name',
    'created_at': 'created_at',
    'id': 'id',
}


def _client_order(sort: str | None) -> str:
    requested = sort or 'created_at'
    descending = requested.startswith('-')
    field = requested[1:] if descending else requested
    if field not in CLIENT_SORTS:
        raise DomainError('VALIDATION_ERROR', 'Request validation failed.', status_code=422)
    direction = 'DESC' if descending else 'ASC'
    return f'{CLIENT_SORTS[field]} {direction}, id ASC'


def get_client_for_user(
    connection: Connection, *, user_id: UUID, client_id: UUID, for_update: bool = False,
) -> Client | None:
    """Missing and foreign-owned clients are indistinguishable to callers."""
    with connection.cursor(row_factory=class_row(Client)) as cursor:
        query = ('SELECT id, user_id, name, email, phone, address, created_at, updated_at '
                 'FROM clients WHERE user_id = %s AND id = %s')
        if for_update:
            query += ' FOR SHARE'
        cursor.execute(query, (user_id, client_id))
        return cursor.fetchone()


def list_clients_for_user(connection: Connection, *, user_id: UUID) -> list[Client]:
    """Return only this owner's clients, oldest first with a UUID tie-breaker."""
    with connection.cursor(row_factory=class_row(Client)) as cursor:
        cursor.execute(
            'SELECT id, user_id, name, email, phone, address, created_at, updated_at '
            'FROM clients WHERE user_id = %s ORDER BY created_at, id',
            (user_id,),
        )
        return cursor.fetchall()


def paginate_clients_for_user(
    connection: Connection, *, user_id: UUID, page: int, page_size: int,
    search: str | None = None, sort: str | None = None,
) -> tuple[list[Client], int]:
    """Count and fetch only the authenticated owner's requested page."""
    pagination = validate_pagination(page, page_size)
    order_by = _client_order(sort)
    conditions = ['user_id = %s']
    parameters: list[object] = [user_id]
    if search:
        conditions.append('(name ILIKE %s OR email ILIKE %s OR phone ILIKE %s)')
        pattern = f'%{search}%'
        parameters.extend([pattern, pattern, pattern])
    where = ' AND '.join(conditions)
    total = connection.execute(
        f'SELECT count(*) FROM clients WHERE {where}', tuple(parameters),
    ).fetchone()[0]
    with connection.cursor(row_factory=class_row(Client)) as cursor:
        cursor.execute(
            'SELECT id, user_id, name, email, phone, address, created_at, updated_at '
            f'FROM clients WHERE {where} ORDER BY {order_by} LIMIT %s OFFSET %s',
            (*parameters, pagination.page_size, pagination.offset),
        )
        return cursor.fetchall(), total
