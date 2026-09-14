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
`EMAIL_ALREADY_REGISTERED`. Registration does not return tokens. Tests exercise this HTTP flow against isolated test-database schemas;
they do not register users in the application database.

## JWT login

`POST /api/v1/auth/login` accepts JSON `email` and `password`. `LoginRequest`
uses registration's email normalization but preserves the password exactly and
does not enforce registration strength rules. Missing/malformed fields return
422. Unknown email and incorrect password both return 401 `INVALID_CREDENTIALS`
with the same message and `WWW-Authenticate: Bearer`. Unknown emails still incur
an Argon2 verification against a process-local dummy hash; this avoids skipping
the expensive verification step, without claiming perfectly identical timings.

Success returns HTTP 200 with `data.access_token`, `data.refresh_token`, and
`data.token_type` set to `bearer`. Cache headers prevent caching the token response.
The synchronous route calls `authenticate_user()`, then `issue_token_pair()`.
Login does not modify the user or issue tokens on a failed password check.

Configure the following in the process environment or the ignored `.env`:

| Variable | Default | Meaning |
| --- | --- | --- |
| JWT_SECRET_KEY | Required; no fallback | Random private signing key of at least 32 bytes |
| JWT_ACCESS_TOKEN_MINUTES | 15 | Positive integer access-token lifetime |
| JWT_REFRESH_TOKEN_DAYS | 7 | Positive integer refresh-token lifetime; must outlive access |

Use Python's `secrets.token_urlsafe(48)` to generate a signing key. Keep it stable
across workers/restarts and private; changing it invalidates tokens signed with
the old key once token verification is implemented. The example environment file
intentionally leaves the key blank. `TokenSettings` excludes the key from repr;
invalid configuration produces a generic 500 response and no tokens. Configuration
is loaded by the login dependency, so health/registration can run without a JWT key.

`accounts/tokens.py` uses [PyJWT](https://pyjwt.readthedocs.io/en/stable/usage.html)
with fixed HS256 signing. Claims are `sub` (user UUID), `type` (`access` or
`refresh`), `iat`, `exp`, `jti` (unique per token), `iss` (`plug-and-send-billing`),
and `aud` (`billing-api`). No passwords, hashes, email addresses, or caller-supplied
claims enter tokens. JWTs are signed, not encrypted; their claims are readable.
The refresh endpoint (Task 2.5) verifies the refresh token type, signature, expiry,
issuer, and audience. The current-user endpoint (Task 2.6) applies the same checks
while requiring an access token.

## JWT refresh

`POST /api/v1/auth/refresh` accepts `{"refresh_token": "..."}` and returns HTTP
200 with `{"data": {"access_token": "...", "token_type": "bearer"}}`.
The response includes `Cache-Control: no-store` and `Pragma: no-cache`.

`RefreshRequest` validates the input and excludes the token from model dumps and
repr. The route calls `refresh_access_token()`, which verifies the signed claims,
looks up the user by the verified UUID, and issues a fresh access token. It does
not rotate or extend the refresh token: that token remains reusable until expiry.
There is no token revocation store in this task.

Invalid or expired tokens, access tokens submitted as refresh tokens, and tokens
for deleted users return 401 `INVALID_REFRESH_TOKEN` with the same generic message.
Missing or malformed request fields return 422 `VALIDATION_ERROR` without echoing
the input. Verification requires all issued claims and uses a fixed HS256 algorithm.

Run the login and refresh integration tests against the separate PostgreSQL test
database with `python -m unittest tests.test_login tests.test_refresh -v`.

## Business profile model

Task 3.1 defines `app/business/models.py` as the typed representation of a stored
`business_profiles` row. It includes the owner `user_id`, business name, optional
logo/email/phone/address/tax number, default currency, UUID, and timestamps.
Like `User`, it is an immutable row model rather than an API request schema.

The existing initial migration supplies the UUID and UTC timestamps, defaults
currency to `KES`, and enforces one profile per existing user with a unique
foreign key. Optional contact and tax fields may be null. An explicit currency
can be stored; the reusable currency validator is described below. Profile
retrieval is Task 3.3 and upsert/update is Task 3.4. No additional migration is needed.

Run `python -m unittest tests.test_business_profile -v` to verify the model against
PostgreSQL, including defaults, full-field persistence, updated timestamps, and
database ownership/required-field constraints.

## Business profile retrieval

Task 3.3 adds `GET /api/v1/business-profile`. Send
`Authorization: Bearer <access_token>` to retrieve the authenticated user's
profile in the standard `data` envelope, including its UUID, owner UUID,
business/contact/tax fields, currency, and timestamps. Optional fields remain
null. Successful responses include `Cache-Control: no-store`.

The route reuses `get_current_user()` and calls `get_profile_for_user()` with
the verified user's ID. The parameterized query always filters by `user_id`;
caller-supplied IDs cannot select another account's profile. Authentication and
profile retrieval share the request's database connection, which closes after
the response. Missing profiles return 404 `BUSINESS_PROFILE_NOT_FOUND` without
creating a row. Invalid authentication returns 401 `AUTHENTICATION_REQUIRED`.

Run `python -m unittest tests.test_business_profile_read -v` for PostgreSQL-backed
retrieval, authentication, missing-profile, and cross-user isolation tests.

## Business profile upsert/update

Task 3.4 adds `PUT /api/v1/business-profile`, authenticated with an access bearer
token. Both creation and update return HTTP 200 with the stored profile in `data`.
PUT replaces all editable fields: `business_name` is required, omitted optional
fields become null, and omitted currency becomes `KES`. Send every value you want
to retain. Explicit null is rejected for name and currency.

`BusinessProfilePut` trims and validates the name, validates email and HTTP(S)
logo URLs, enforces database field lengths, and uses `CurrencyCode`. Unknown and
server-managed fields are rejected with 422 `VALIDATION_ERROR`. Phone is optional
text limited to 30 characters; no additional phone-format rule is imposed here.

The route passes the verified user's ID to `upsert_profile()`. Its transaction
uses `INSERT ... ON CONFLICT (user_id) DO UPDATE`, so concurrent saves use the
database's one-profile-per-user constraint. Updates preserve ID, owner, and
creation time. Repeated requests retain the same editable state; the database
refreshes `updated_at` on each update. No profile selection comes from the body.

Run `python -m unittest tests.test_business_profile_put tests.test_business_profile_read -v`
for creation, replacement, validation, ownership, authentication, and rollback checks.

## Client model and user-scoped queries

`app/clients/models.py` represents persisted client rows with UUIDs, owner ID,
name, nullable contact fields, and timestamps. The existing initial migration
supplies the table, constraints, and indexes; no new migration is needed.

Task 4.2 adds `get_client_for_user(connection, *, user_id, client_id)` and
`list_clients_for_user(connection, *, user_id)` in `app/clients/queries.py`.
Callers must pass `user_id` from authentication. Both parameterized SQL queries
filter by owner in the database. Detail retrieval also filters by client UUID
and returns `None` for missing or foreign-owned clients. Lists return `Client`
objects ordered by `created_at`, then UUID, or an empty list when none match.
These internal queries do not authenticate callers themselves. HTTP endpoints
and pagination will be added in their respective tasks.

Run `python -m unittest tests.test_client_queries -v` for PostgreSQL-backed
ownership isolation, row mapping, list ordering, and missing-client checks.

## Currency-code validation

Task 3.2 adds `validate_currency_code(value)` and the Pydantic `CurrencyCode` type
in `app/common/currency.py`. The function returns an unchanged string containing
exactly three uppercase ASCII letters, or raises `ValueError`. Request schemas
can declare `currency: CurrencyCode` (or `default_currency: CurrencyCode`) to use
the same rule through Pydantic validation.

Lowercase, whitespace, digits, Unicode lookalikes, and non-string inputs are
rejected rather than normalized or coerced. This is an ISO-style format check,
not validation against a current ISO 4217 registry. It performs no FX conversion
and does not choose a default. Future request-schema tasks will apply this type
to their currency fields.

Run `python -m unittest tests.test_currency -v` for standalone and Pydantic/JSON
validation tests; no database is required.

## Current user

`GET /api/v1/auth/me` requires `Authorization: Bearer <access_token>` and returns
HTTP 200 with `data` containing only `id`, `name`, `email`, and `phone`. The
response uses `Cache-Control: no-store`. Passwords, password hashes, and internal
timestamps are excluded by the public `UserResponse` schema.

`accounts/dependencies.py` provides `get_current_user()` for protected routes.
It first verifies the bearer access token, then loads the user from PostgreSQL
using the verified subject UUID. Profile values therefore reflect the current
database row. Query parameters and headers cannot choose a different user.
Missing, malformed, expired, or invalid credentials, refresh tokens, and deleted
users all return 401 `AUTHENTICATION_REQUIRED` with `WWW-Authenticate: Bearer`.
The OpenAPI schema declares HTTP bearer authentication for this endpoint.

Run the authentication checks with
`python -m unittest tests.test_current_user tests.test_refresh tests.test_login -v`.
