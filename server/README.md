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
| APP_DEBUG | false | true, false; retained in settings, never enables HTTP tracebacks |

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

## API response helpers

Feature routers use `app.common.responses` to return the contract's JSON shapes:

```python
resource_response({"id": public_id}, status_code=201)
collection_response(records, page=1, page_size=20, total=matching_count)
error_response("CLIENT_NOT_FOUND", "Client not found.", status_code=404)
```

The helpers return `JSONResponse` objects. Resource responses default to HTTP 200;
collections use HTTP 200; errors require an explicit status code and default to
empty `details`. Optional error headers support HTTP requirements such as
`WWW-Authenticate`. UUIDs and dates serialize as strings, and Decimal values remain
strings with their precision preserved, including nested item values.

Callers must supply public response data: these helpers do not remove passwords
or perform authorization. Collection data must already be paginated; `total`
means all matching records, not the length of the current page. HTTP 204 deletes
should return an empty `Response(status_code=204)` rather than a JSON envelope.
PDF endpoints will return PDF responses separately.

`GET /api/v1` now returns `{"data": {"version": "v1"}}`. `/health` retains its
existing health-check shape.

## Global error handling

`create_app()` registers the handlers from `app.common.errors`. Services can raise
an expected business error instead of constructing an HTTP response:

```python
raise DomainError(
    "CLIENT_NOT_FOUND",
    "Client not found.",
    status_code=404,
)
```

`DomainError` accepts public codes/messages, optional details and HTTP headers,
and a 4xx status (default 400). Services must never include credentials, private
database details, or internal exception text in these public fields. Domain rules
and their specific error codes are implemented with the relevant feature tasks.

Framework HTTP exceptions use stable generic mappings: `BAD_REQUEST` (400),
`AUTHENTICATION_REQUIRED` (401), `FORBIDDEN_RESOURCE` (403), `RESOURCE_NOT_FOUND`
(404), `METHOD_NOT_ALLOWED` (405), `STATE_CONFLICT` (409), `VALIDATION_ERROR` (422),
and `TOO_MANY_REQUESTS` (429). Other client statuses use `HTTP_ERROR`. Their raw
`detail` is not exposed; use `DomainError` for intentional public messages.
Headers such as `WWW-Authenticate`, `Allow`, and `Retry-After` are preserved.

Request validation returns HTTP 422 with `VALIDATION_ERROR`. The
`details.errors` list contains each error's `loc`, `type`, and a safe generic
message. Submitted values, validator messages, and exception context are omitted.
Malformed JSON uses the same envelope. Invalid server response data is a server
failure, not a client validation error.

Unexpected exceptions return HTTP 500 with `INTERNAL_SERVER_ERROR`, a generic
message, and empty details. HTTP exceptions with a 5xx status also hide internal
details while preserving the status. Framework debug traceback responses remain
disabled even when `APP_DEBUG=true`; the setting is still available on
`app.state.settings.debug`. Exceptions remain available to the server's error
handling; no new logging configuration is introduced here. Once a streaming
response has begun, its status/body cannot be replaced with a JSON error.

## User persistence

`app.accounts.models.User` represents a persisted `users` row as a frozen Pydantic
model. It contains the documented UUID, name, email, nullable phone, password hash,
and timestamps. `password_hash` is excluded from standard model serialization and
representations, while remaining available internally for password verification.
This is a database-row model; registration requests use `accounts.schemas.UserCreate`.

`app.accounts.service.create_user(connection, name=..., email=..., password=...,
phone=...)` hashes the password before opening a transaction, then calls
`accounts.queries.insert_user()`. The insert binds SQL parameters and returns the
database-generated UUID and timestamps. The query accepts an already-generated
hash; application callers should use the service for raw passwords. No new schema
migration is needed because Task 1.2 created the `users` table.

Password hashing and verification use `pwdlib` with its recommended Argon2 hasher,
following [FastAPI's hashing guidance](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#install-pwdlib).
The library manages salts and encoded hash parameters. Plaintext passwords are
not persisted. These synchronous functions should run in synchronous routes or a
worker thread when called from future asynchronous endpoints.

PostgreSQL enforces unique email values. The service maps the `users_email_key`
constraint failure to `EMAIL_ALREADY_REGISTERED` (409), after transaction rollback.
Other database failures are not misclassified as duplicate emails. The service
respects enclosing transactions, so a caller can roll back user creation along
with another operation.

## Registration endpoint

`POST /api/v1/auth/register` accepts an unauthenticated JSON request:

```json
{
  "name": "Owner",
  "email": "owner@example.com",
  "password": "Example123",
  "phone": "0712345678"
}
```

`UserCreate` trims names, lowercases and trims email, and checks required fields
and password strength. Phone is optional and accepts digits with an optional
leading `+`. Passwords retain their exact characters; they are passed explicitly
to the service because schema serialization excludes them. Extra fields cannot
override the generated UUID, timestamps, or password hash.

The accounts router is mounted by `api/v1.py`. The synchronous route uses
`common.dependencies.get_database_connection`, which opens and closes a connection
per request. It reads process environment settings and uses `TEST_DATABASE_URL`
when the app environment is `test`, without falling back to the application DB.
Start the server with the documented `--env-file .env` option to load credentials.

Successful registration returns HTTP 201:

```json
{"data": {"id": "<generated UUID>", "name": "Owner", "email": "owner@example.com", "phone": "0712345678"}}
```

`UserResponse` selects only these public fields. `RegistrationResponse` documents
the envelope in OpenAPI. Invalid or missing fields return HTTP 422 with
`VALIDATION_ERROR`; duplicate normalized emails return HTTP 409 with
`EMAIL_ALREADY_REGISTERED`. No tokens are returned. Login and JWT handling belong
to Task 2.4. Tests exercise this HTTP flow against isolated test-database schemas;
they do not register users in the application database.
