"""Account operations; request validation and HTTP routes are separate tasks."""

from psycopg import Connection, errors

from app.accounts.models import User
from app.accounts.passwords import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.accounts.queries import get_user_by_email, get_user_by_id, insert_user
from app.accounts.schemas import AccessToken
from app.accounts.tokens import TokenSettings, invalid_refresh_token, issue_access_token, verify_refresh_token
from app.common.errors import DomainError


def refresh_access_token(
    connection: Connection, *, refresh_token: str, settings: TokenSettings,
) -> AccessToken:
    user_id = verify_refresh_token(refresh_token, settings)
    user = get_user_by_id(connection, user_id)
    if user is None:
        raise invalid_refresh_token()
    return issue_access_token(user.id, settings)


def authenticate_user(connection: Connection, *, email: str, password: str) -> User:
    user = get_user_by_email(connection, email)
    matches = verify_password(password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if user is None or not matches:
        raise DomainError(
            "INVALID_CREDENTIALS", "Invalid email or password.", status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


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
