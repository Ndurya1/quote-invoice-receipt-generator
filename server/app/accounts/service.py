"""Account operations; request validation and HTTP routes are separate tasks."""

from psycopg import Connection

from app.accounts.models import User
from app.accounts.passwords import hash_password
from app.accounts.queries import insert_user


def create_user(
    connection: Connection,
    *,
    name: str,
    email: str,
    password: str,
    phone: str | None = None,
) -> User:
    """Hash before opening a transaction; persist using database-generated defaults."""
    password_hash = hash_password(password)
    with connection.transaction():
        return insert_user(
            connection, name=name, email=email,
            phone=phone, password_hash=password_hash,
        )
