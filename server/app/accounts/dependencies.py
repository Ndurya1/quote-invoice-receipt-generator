"""Reusable bearer authentication for user-owned API resources."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Connection

from app.accounts.models import User
from app.accounts.queries import get_user_by_id
from app.accounts.tokens import (
    TokenSettings, authentication_required, get_token_settings, verify_access_token,
)
from app.common.dependencies import get_database_connection

bearer = HTTPBearer(auto_error=False)


def get_authenticated_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[TokenSettings, Depends(get_token_settings)],
) -> UUID:
    if credentials is None:
        raise authentication_required()
    return verify_access_token(credentials.credentials, settings)


def get_current_user(
    user_id: Annotated[UUID, Depends(get_authenticated_user_id)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> User:
    user = get_user_by_id(connection, user_id)
    if user is None:
        raise authentication_required()
    return user
