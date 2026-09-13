"""Run with python -m app.db {check,create-test-db,migrate} [--test]."""

import argparse
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg import sql

from app.common.database import (
    DatabaseConfigurationError,
    DatabaseSettings,
    connect_database,
    parse_database_url,
)
from app.common.migrations import MigrationError, apply_migrations


def create_test_database(settings: DatabaseSettings) -> bool:
    target = parse_database_url(settings.connection_url(test=True), "TEST_DATABASE_URL")
    primary = parse_database_url(settings.connection_url(), "DATABASE_URL")
    if any(target.get(key, default) != primary.get(key, default)
           for key, default in (("host", ""), ("port", "5432"), ("user", ""))):
        raise DatabaseConfigurationError("Test database creation requires the same host, port, and user")
    with connect_database(settings) as connection:
        if connection.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target["dbname"],)).fetchone():
            return False
        connection.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(target["dbname"])))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "create-test-db", "migrate"))
    parser.add_argument("--test", action="store_true", help="Use TEST_DATABASE_URL")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    settings = DatabaseSettings.from_environment()
    try:
        if args.command == "create-test-db":
            created = create_test_database(settings)
            print("Test database created" if created else "Test database already exists")
        else:
            with connect_database(settings, test=args.test) as connection:
                if args.command == "check":
                    connection.execute("SELECT 1").fetchone()
                    print("PostgreSQL connection OK; timezone=" + connection.execute("SHOW timezone").fetchone()[0])
                else:
                    applied = apply_migrations(connection)
                    print("Applied: " + ", ".join(applied) if applied else "Migrations already up to date")
    except (DatabaseConfigurationError, MigrationError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except psycopg.Error as exc:
        # Driver errors can contain connection details or SQL values: do not echo them.
        print(f"Database operation failed ({type(exc).__name__}, SQLSTATE {exc.sqlstate or 'unavailable'})", file=sys.stderr)
        if args.command == "create-test-db" and isinstance(exc, psycopg.errors.InsufficientPrivilege):
            print("Have a PostgreSQL administrator create the test database with the application role as owner.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
