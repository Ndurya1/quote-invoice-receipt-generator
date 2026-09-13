"""Account persistence using the existing PostgreSQL users table."""

from psycopg import Connection
from psycopg.rows import class_row
from uuid import UUID

from app.accounts.models import User


def get_user_by_id(connection: Connection, user_id: UUID) -> User | None:
    with connection.cursor(row_factory=class_row(User)) as cursor:
        cursor.execute(
            "SELECT id, name, email, phone, password_hash, created_at, updated_at "
            "FROM users WHERE id = %s",
            (user_id,),
        )
        return cursor.fetchone()


def get_user_by_email(connection: Connection, email: str) -> User | None:
    """Look up the normalized email supplied by the account request schema."""
    with connection.cursor(row_factory=class_row(User)) as cursor:
        cursor.execute(
            "SELECT id, name, email, phone, password_hash, created_at, updated_at "
            "FROM users WHERE email = %s",
            (email,),
        )
        return cursor.fetchone()


def insert_user(
    connection: Connection,
    *,
    name: str,
    email: str,
    password_hash: str,
    phone: str | None = None,
) -> User:
    """Insert a hash, never a raw password; transaction ownership is the caller's."""
    with connection.cursor(row_factory=class_row(User)) as cursor:
        cursor.execute(
            """
            INSERT INTO users (name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, email, phone, password_hash, created_at, updated_at
            """,
            (name, email, phone, password_hash),
        )
        user = cursor.fetchone()
    if user is None:
        raise RuntimeError("User insertion returned no row")
    return user
