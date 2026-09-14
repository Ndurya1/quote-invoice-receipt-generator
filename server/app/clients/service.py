"""Transactional Client operations."""

from uuid import UUID

from psycopg import Connection, sql
from psycopg.rows import class_row

from app.clients.models import Client
from app.clients.queries import get_client_for_user
from app.clients.schemas import ClientCreate, ClientPatch
from app.common.errors import DomainError


def update_client(
    connection: Connection, *, user_id: UUID, client_id: UUID, payload: ClientPatch,
) -> Client:
    changes = payload.model_dump(exclude_unset=True, mode='json')
    with connection.transaction():
        if not changes:
            client = get_client_for_user(connection, user_id=user_id, client_id=client_id)
        else:
            # Only schema-declared editable columns enter the statement.
            fields = [field for field in ('name', 'email', 'phone', 'address') if field in changes]
            assignments = sql.SQL(', ').join(
                sql.SQL('{} = %s').format(sql.Identifier(field)) for field in fields
            )
            with connection.cursor(row_factory=class_row(Client)) as cursor:
                cursor.execute(
                    sql.SQL('UPDATE clients SET {} WHERE user_id = %s AND id = %s '
                            'RETURNING id, user_id, name, email, phone, address, created_at, updated_at')
                    .format(assignments),
                    (*[changes[field] for field in fields], user_id, client_id),
                )
                client = cursor.fetchone()
        if client is None:
            raise DomainError('CLIENT_NOT_FOUND', 'Client not found.', status_code=404)
        return client


def create_client(connection: Connection, *, user_id: UUID, payload: ClientCreate) -> Client:
    """Persist validated input for the owner resolved from authentication."""
    with connection.transaction():
        with connection.cursor(row_factory=class_row(Client)) as cursor:
            cursor.execute(
                'INSERT INTO clients (user_id, name, email, phone, address) '
                'VALUES (%s, %s, %s, %s, %s) '
                'RETURNING id, user_id, name, email, phone, address, created_at, updated_at',
                (user_id, payload.name, str(payload.email) if payload.email is not None else None,
                 payload.phone, payload.address),
            )
            client = cursor.fetchone()
            if client is None:
                raise RuntimeError('Client insertion returned no row')
            return client
