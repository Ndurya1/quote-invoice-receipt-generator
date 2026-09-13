"""Transactional, append-only numbered SQL migrations."""

import hashlib
import re
from pathlib import Path

import psycopg

MIGRATIONS_DIRECTORY = Path(__file__).resolve().parents[2] / "migrations"
MIGRATION_LOCK = 781426590


class MigrationError(ValueError):
    """Migration history no longer matches the checked-in migration files."""


def apply_migrations(
    connection: psycopg.Connection, directory: Path = MIGRATIONS_DIRECTORY
) -> list[str]:
    if not connection.autocommit:
        raise MigrationError("Migration connections must use autocommit")
    files = sorted(directory.glob("*.sql"))
    if not files or any(not re.fullmatch(r"\d{3}_[a-z0-9_]+\.sql", p.name) for p in files):
        raise MigrationError("Expected numbered SQL files such as 001_initial.sql")
    if len({p.name[:3] for p in files}) != len(files):
        raise MigrationError("Migration numbers must be unique")
    scripts = [(p.name, p.read_text(encoding="utf-8-sig")) for p in files]
    checksums = {name: hashlib.sha256(body.encode("utf-8")).hexdigest() for name, body in scripts}
    applied = []
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK,))
        connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                checksum CHAR(64) NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        history = connection.execute(
            "SELECT name, checksum FROM schema_migrations ORDER BY name"
        ).fetchall()
        if [name for name, _ in history] != [name for name, _ in scripts[:len(history)]]:
            raise MigrationError("Applied migrations must be an unchanged prefix of migration files")
        if any(checksums[name] != checksum for name, checksum in history):
            raise MigrationError("An applied migration was edited; add a new migration instead")
        for name, body in scripts[len(history):]:
            connection.execute(body, prepare=False)
            connection.execute(
                "INSERT INTO schema_migrations (name, checksum) VALUES (%s, %s)",
                (name, checksums[name]),
            )
            applied.append(name)
    return applied
