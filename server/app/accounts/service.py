"""Account operations; request validation and HTTP routes are separate tasks."""

from psycopg import Connection, errors

from app.accounts.models import User
from app.accounts.passwords import hash_password
from app.accounts.queries import insert_user
from app.common.errors import DomainError


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
    try:
        with connection.transaction():
            return insert_user(
                connection, name=name, email=email,
                phone=phone, password_hash=password_hash,
            )
    except errors.UniqueViolation as exc:
        # Translate only the email constraint, after the transaction has rolled back.
        if exc.diag.constraint_name != "users_email_key":
            raise
        raise DomainError(
            "EMAIL_ALREADY_REGISTERED", "An account with this email already exists.",
            status_code=409,
        ) from None
