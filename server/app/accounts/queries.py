"""Account persistence using the existing PostgreSQL users table."""

from psycopg import Connection
from psycopg.rows import class_row

from app.accounts.models import User


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
