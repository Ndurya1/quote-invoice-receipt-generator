# Plug-and-Send Billing backend

Python 3.13+ and FastAPI. Run commands from the `server` directory with the
project virtual environment activated. Dependencies are declared in
`pyproject.toml` and locked in `uv.lock`; use `uv sync` to install them.

Copy `.env.example` to `.env` only when no local `.env` exists. Keep credentials
in the ignored local file. The development server loads it explicitly:

```powershell
python -m uvicorn app.main:app --env-file .env --reload
```

The FastAPI CLI also resolves `app.main:app` through `pyproject.toml`.
Settings read process environment variables; `.env` loading is handled by the
server command, not by importing the application.

| Variable | Default | Accepted values |
| --- | --- | --- |
| APP_NAME | quote-invoice-receipt generator API | Non-empty title |
| APP_ENV | development | development, test, production |
| APP_DEBUG | false | true, false |

`GET /health` reports application health. `GET /api/v1` resolves the API
namespace. Neither endpoint checks database connectivity. Starting the API never
applies migrations.

## PostgreSQL and migrations

Set `DATABASE_URL` to the existing application database and `TEST_DATABASE_URL`
to a separate database whose name ends in `_test`. Both URLs must explicitly
specify host, user, and database; port defaults to PostgreSQL's 5432. Passwords
and optional connection parameters are supplied through the URLs. Percent-encode
reserved characters inside credentials, for example `@` as `%40` and `#` as `%23`.
URLs are not logged or included in settings representations.

```powershell
python -m app.db check
python -m app.db create-test-db
python -m app.db migrate --test
python -m unittest discover -s tests -v
python -m app.db migrate
```

These commands load the local `.env` without overriding process environment
variables. `create-test-db` requires the application role to have `CREATEDB`,
and the test URL to use the same host, port, and user. It leaves an existing test
database intact. If that privilege is unavailable, have the database administrator
create the test database and grant the test role schema-creation permission.

Connections use Psycopg with a five-second connection timeout and UTC session
timezone. Connections are autocommit by default; services must wrap related writes
in `with connection.transaction():` to commit or roll back together. See the
[Psycopg transaction documentation](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).

SQL migrations live in `migrations/NNN_description.sql`. The runner serializes
execution with a PostgreSQL transaction advisory lock, applies each pending batch
atomically, and records SHA-256 checksums in `schema_migrations`. Repeat runs skip
applied files. Missing, reordered, or edited applied migrations fail; add a new
file for future schema changes. Line endings are normalized for checksums. SQL
files must not manage transactions themselves or contain statements that require
execution outside a transaction. There is no automatic down/reset command.

The initial migration establishes the nine documented tables, UUID defaults,
fixed-precision numeric columns, enums, constraints, indexes, and UTC-aware
timestamps. Update triggers maintain `updated_at`. Foreign keys restrict deletion
of referenced users, clients, and source documents; deleting a permitted parent
document cascades only to its own items. The unique source-quote constraint already
provides its lookup index. Model services, tenant checks, calculations, and
lifecycle rules are implemented in their later tasks.

## Tests

The foundation uses standard-library unittest discovery and FastAPI's TestClient.
Foundation/configuration tests require no database. PostgreSQL migration tests
load `TEST_DATABASE_URL` from the environment or `.env`; without it they explicitly
skip. An invalid or unavailable configured test database fails rather than silently
skipping or falling back to the application database. Each integration test creates
and removes its own randomly named schema within the separate test database.

```powershell
python -m unittest discover -s tests -v
```

## Structure

- `app/main.py`: application factory and ASGI entry point
- `app/api/`: versioned router composition
- `app/common/`: settings and shared infrastructure
- `app/accounts/`, `business/`, `clients/`, `quotes/`, `invoices/`, `receipts/`:
  domain packages, populated by subsequent implementation tasks
- `tests/`: automated tests
- `migrations/`: database migration work
- `docs/backend/BACKEND_IMPLEMENTATION_PLAN.md`: task scope and commit sequence

Response envelopes, authentication, persistence, and domain endpoints are added
by their respective later tasks.
