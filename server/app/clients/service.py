"""Transactional Client operations."""

from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.clients.models import Client
from app.clients.schemas import ClientCreate


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
