"""PostgreSQL connection configuration, independent of application startup."""

import os
from dataclasses import dataclass, field

import psycopg
from psycopg.conninfo import conninfo_to_dict


class DatabaseConfigurationError(ValueError):
    """A safe-to-display configuration error that never includes a DSN."""


def parse_database_url(value: str, variable: str) -> dict[str, str]:
    if not value or not value.startswith(("postgresql://", "postgres://")):
        raise DatabaseConfigurationError(f"{variable} must be a PostgreSQL URL")
    if any(c in value for c in "\r\n\t") or value.count("@") > 1 or "#" in value:
        raise DatabaseConfigurationError(f"{variable}: percent-encode reserved credential characters")
    try:
        parameters = conninfo_to_dict(value)
    except psycopg.Error:
        raise DatabaseConfigurationError(f"{variable} is not a valid PostgreSQL URL") from None
    if not all(parameters.get(key) for key in ("host", "dbname", "user")):
        raise DatabaseConfigurationError(f"{variable} must specify host, database, and user")
    return parameters


@dataclass(frozen=True)
class DatabaseSettings:
    database_url: str = field(repr=False)
    test_database_url: str = field(default="", repr=False)

    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        return cls(os.getenv("DATABASE_URL", ""), os.getenv("TEST_DATABASE_URL", ""))

    def connection_url(self, *, test: bool = False) -> str:
        primary = parse_database_url(self.database_url, "DATABASE_URL")
        if not test:
            return self.database_url
        target = parse_database_url(self.test_database_url, "TEST_DATABASE_URL")
        if target["dbname"] == primary["dbname"] or not target["dbname"].endswith("_test"):
            raise DatabaseConfigurationError(
                "TEST_DATABASE_URL must use a different database name ending in _test"
            )
        return self.test_database_url


def connect_database(settings: DatabaseSettings, *, test: bool = False) -> psycopg.Connection:
    """Open an autocommit connection; callers use explicit transaction blocks."""
    return psycopg.connect(
        settings.connection_url(test=test),
        autocommit=True,
        connect_timeout=5,
        options="-c timezone=UTC",
        application_name="plug_and_send_billing",
    )
