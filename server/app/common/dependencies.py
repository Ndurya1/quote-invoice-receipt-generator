"""Shared dependencies for HTTP routes."""

from collections.abc import Iterator

from fastapi import Request
from psycopg import Connection

from app.common.database import DatabaseSettings, connect_database


def get_database_connection(request: Request) -> Iterator[Connection]:
    """Provide one connection per request and close it on success or failure."""
    settings = DatabaseSettings.from_environment()
    use_test_database = request.app.state.settings.environment == "test"
    with connect_database(settings, test=use_test_database) as connection:
        yield connection
