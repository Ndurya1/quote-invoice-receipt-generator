"""Client reads; callers must supply the owner ID from authentication."""

from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.clients.models import Client


def get_client_for_user(
    connection: Connection, *, user_id: UUID, client_id: UUID,
) -> Client | None:
    """Missing and foreign-owned clients are indistinguishable to callers."""
    with connection.cursor(row_factory=class_row(Client)) as cursor:
        cursor.execute(
            'SELECT id, user_id, name, email, phone, address, created_at, updated_at '
            'FROM clients WHERE user_id = %s AND id = %s',
            (user_id, client_id),
        )
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
) -> tuple[list[Client], int]:
    """Count and fetch only the authenticated owner's requested page."""
    if not 1 <= page <= 2147483647 or not 1 <= page_size <= 100:
        raise ValueError('Invalid client pagination bounds')
    total = connection.execute(
        'SELECT count(*) FROM clients WHERE user_id = %s', (user_id,),
    ).fetchone()[0]
    with connection.cursor(row_factory=class_row(Client)) as cursor:
        cursor.execute(
            'SELECT id, user_id, name, email, phone, address, created_at, updated_at '
            'FROM clients WHERE user_id = %s ORDER BY created_at, id LIMIT %s OFFSET %s',
            (user_id, page_size, (page - 1) * page_size),
        )
        return cursor.fetchall(), total
