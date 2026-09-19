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

## Client creation

Task 4.3 adds `POST /api/v1/clients` with access bearer authentication. Supply a
required `name` and optional nullable `email`, `phone`, and `address`. Name is
trimmed and limited to 1–160 characters; email is validated and limited to 255
characters; phone is text limited to 30 characters. Duplicate emails are allowed.
Unknown and server-managed fields are rejected with 422 `VALIDATION_ERROR`.

The route passes the verified user's ID and `ClientCreate` input to
`create_client()`. The service inserts the row in a transaction using parameterized
SQL; PostgreSQL generates the UUID and timestamps. Success returns HTTP 201 with
the stored client inside `data` and `Cache-Control: no-store`. Missing or invalid
authentication returns 401. A business profile is not required to create clients.

Run `python -m unittest tests.test_client_creation tests.test_client_queries -v`
for PostgreSQL-backed creation, validation, duplicate-email, ownership, authentication,
and transaction rollback checks.

## Client listing

Task 4.4 adds authenticated `GET /api/v1/clients?page=1&page_size=20`. It returns
`data` and `meta` (`page`, `page_size`, `total`) using the collection envelope.
Both the count and page queries filter by the verified owner ID. SQL applies
`LIMIT` and `OFFSET`, ordered by creation time and UUID. The list endpoint does
not load all clients into Python to paginate them.

Page defaults to 1 (maximum 2147483647); page size defaults to 20 and is limited
to 1–100. Invalid values return 422. Empty and out-of-range pages return an empty
list with the owner's total count. Successful responses use `Cache-Control:
no-store`. Count and page are separate queries, so concurrent writes may change
the dataset between them. Search and configurable sorting remain later tasks.

Run `python -m unittest tests.test_client_list tests.test_client_creation tests.test_client_queries -v`
for pagination, ownership isolation, validation, and Client regression tests.

## Client detail

Task 4.5 adds authenticated `GET /api/v1/clients/{client_id}`. The route validates
the UUID, resolves the current user, and calls `get_client_for_user()` with both
IDs. Success returns HTTP 200 with the stored client in `data` and
`Cache-Control: no-store`. Missing and foreign-owned clients receive the same
404 `CLIENT_NOT_FOUND` response, so the endpoint does not disclose another
account's client records. Invalid UUIDs return 422; invalid authentication returns
401. Run `python -m unittest tests.test_client_detail -v` for endpoint checks.

## Client partial updates

Task 4.6 adds authenticated `PATCH /api/v1/clients/{client_id}`. Send only the
editable fields to change: name, email, phone, or address. Omitted fields stay
unchanged; null clears a contact field but cannot clear name. Validation reuses
the creation schema's field rules and rejection of unknown/server-managed fields.

`ClientPatch` tracks supplied fields; `update_client()` uses `exclude_unset=True`
and a fixed allowlist of column names to construct a parameterized SQL update.
Both owner and client UUID constrain the update. ID, owner, and creation time
are preserved; the database maintains `updated_at`. Empty `{}` reads the owned
client without writing. Missing and foreign clients return 404 `CLIENT_NOT_FOUND`.
Success returns HTTP 200 with the stored client in `data`.

Run `python -m unittest tests.test_client_patch -v` for partial-update, null,
validation, ownership, authentication, and rollback checks.

## Safe Client deletion

Task 4.7 adds authenticated `DELETE /api/v1/clients/{client_id}`. Unreferenced
owned clients are hard-deleted with an empty HTTP 204 response. Any referencing
Quote, Invoice, or Receipt blocks deletion, regardless of document status, and
returns 409 `CLIENT_IN_USE`. The existing `ON DELETE RESTRICT` foreign keys
preserve all document history; no migration is needed.

`delete_client()` runs an owner-and-UUID-scoped DELETE inside a transaction.
It maps only the three documented document/client foreign-key failures after
rollback; unrelated database failures retain their normal error handling.
Missing and foreign clients both return 404 `CLIENT_NOT_FOUND`. The SQL delete
and database constraints enforce the policy without a separate reference-count
check that could become stale before deletion.

Run `python -m unittest tests.test_client_delete -v` to check successful deletion,
each document relationship, ownership, authentication, and rollback behavior.

## Shared discount types

Task 5.1 adds `DiscountType` in `app/common/enums.py`, a string enum with the
exact values `NONE`, `FIXED`, and `PERCENTAGE`. Future document schemas can use
`discount_type: DiscountType` to validate input and serialize the documented
string values. Unknown and lowercase values are rejected rather than normalized.

The Python values match the existing PostgreSQL `discount_type` enum, so no
migration is needed. This task defines the allowed types; amount validation and
discount calculations belong to later tasks. Run
`python -m unittest tests.test_discount_type -v` to check Pydantic/JSON behavior
and agreement with PostgreSQL.

## Shared line-item validation

Task 5.2 adds `LineItemInput` in `app/common/line_items.py` for future Quote,
Invoice, and Receipt request schemas. Description is required, trimmed, and
nonblank. Quantity is a positive `Decimal` fitting `NUMERIC(12,3)` (up to nine
integer digits); unit price is a nonnegative `Decimal` fitting `NUMERIC(14,2)`
(up to twelve integer digits). Excess significant decimal places are rejected,
not rounded. Non-finite values are rejected.

Decimal strings are recommended for exact amounts. Integer and JSON numeric
inputs are also accepted and converted to Decimal; validation cannot recover
precision already lost in a caller's floating-point value. Position defaults to
0 and must be an integer within PostgreSQL's signed 32-bit range; the current
schema does not impose a nonnegative-position constraint. Null position is invalid.
Unknown fields, including caller-supplied totals, are rejected. No totals are
calculated in this task.

Run `python -m unittest tests.test_line_items -v` to verify required fields,
numeric boundaries, precision, non-finite values, JSON input, and position rules.

## Line-total calculation

Task 5.3 adds `calculate_line_total(item)` in `app/common/calculations.py`.
Pass a validated `LineItemInput`; the function multiplies its Decimal quantity
and unit price and returns a Decimal with two fractional digits. It never accepts
a caller-supplied total or modifies the input. Validate requests before calling
it; do not bypass the input schema using unchecked model construction.

The rounding policy is `ROUND_HALF_UP`, applied once after multiplication to
match the monetary scale: `1.005` becomes `1.01`. A result exceeding
`999999999999.99` after rounding raises `LINE_TOTAL_OUT_OF_RANGE` (422). Tiny
positive products may round to `0.00`; a zero unit price is valid. An explicit
local Decimal context prevents caller precision, rounding, or trap settings
from changing the result. Subtotals, tax, and discounts are later tasks.

Run `python -m unittest tests.test_line_total tests.test_line_items -v` for exact
arithmetic, rounding, zero-price, range, and context-isolation checks.

## Subtotal calculation

Task 5.4 adds `calculate_subtotal(items)` to `app/common/calculations.py`.
It accepts an iterable of validated `LineItemInput` objects, derives each line
total with `calculate_line_total()`, and sums those rounded values using Decimal.
For example, two lines that each round from `0.005` to `0.01` produce a subtotal
of `0.02`. The helper does not sum unrounded products or accept submitted totals.

An empty iterable returns `Decimal('0.00')`; requiring nonempty document items
belongs to later request-validation tasks. A subtotal above `999999999999.99`
raises `SUBTOTAL_OUT_OF_RANGE` (422), while an overflowing individual line retains
`LINE_TOTAL_OUT_OF_RANGE`. The local Decimal context isolates arithmetic from
caller settings. Run `python -m unittest tests.test_subtotal tests.test_line_total -v`
for rounding consistency, exact sums, empty/generator input, and overflow checks.

## Tax calculation

Task 5.5 adds `calculate_tax_amount(subtotal, tax_rate=Decimal('0'))`. It applies
`subtotal * tax_rate / 100` using an isolated Decimal context and rounds once to
two places with `ROUND_HALF_UP`. The subtotal must come from backend calculations.
Both arguments must be finite Decimal values: subtotal must fit nonnegative
`NUMERIC(14,2)` and tax rate must fit nonnegative `NUMERIC(6,3)` (up to `999.999`).
Rates above 100 are permitted by the existing schema. Omission means zero tax;
explicit null is invalid. Parsing API strings/numbers belongs to request schemas.

Invalid inputs raise `INVALID_SUBTOTAL` or `INVALID_TAX_RATE` (422). A rounded tax
amount exceeding `999999999999.99` raises `TAX_AMOUNT_OUT_OF_RANGE` (422).
Zero tax returns `Decimal('0.00')`. Run `python -m unittest tests.test_tax -v` for
percentage arithmetic, precision, rounding, defaults, and overflow checks.

## Discount calculation

Task 5.6 adds `calculate_discount_amount(subtotal, discount_type=DiscountType.NONE,
discount_value=Decimal('0'), *, tax_amount=Decimal('0'))`. Supply backend-derived
subtotal and tax amounts, an actual `DiscountType` enum, and Decimal values.
All amounts and the discount value must fit nonnegative `NUMERIC(14,2)`.

NONE requires a zero value and returns `0.00`. PERCENTAGE accepts 0–100 inclusive
and applies to the subtotal, rounding once to two places with `ROUND_HALF_UP`.
FIXED uses the supplied value. A discount may equal subtotal plus tax but may not
exceed it; violations return `INVALID_DISCOUNT` (422). Fixed discounts may exceed
the subtotal when tax covers the difference. Invalid subtotal/tax inputs return
`INVALID_SUBTOTAL`/`INVALID_TAX_AMOUNT` (422). The helper isolates Decimal settings
and returns a two-place Decimal. Final-total orchestration remains task 5.7.

Run `python -m unittest tests.test_discount -v` for modes, precision, rounding,
percentage limits, nonnegative-final-total enforcement, and context isolation.

## Authoritative document totals

Task 5.7 adds `calculate_document_totals()` in `app/common/totals.py`. Pass an
iterable of validated `LineItemInput` values and optional Decimal tax rate,
`DiscountType`, and Decimal discount value. The service consumes items once,
calculates each line once, sums the rounded line totals, calculates tax and
discount, then derives `total = subtotal + tax_amount - discount_amount`.
It shares the existing arithmetic helpers and their rounding/range rules.

The result is an immutable `DocumentTotals` with a tuple of immutable calculated
line items and all financial fields needed for persistence. No submitted totals,
owner IDs, or document-specific state enter this service, so Quote, Invoice,
Receipt, and conversion services can reuse it. It does not write to the database.
Inputs must be validated before calling; do not use unchecked model construction.

Empty items raise `EMPTY_LINE_ITEMS` (422). A final total outside NUMERIC(14,2)
raises `TOTAL_OUT_OF_RANGE` (422); errors from individual helpers propagate.
Tax rate is returned at three decimal places; discount value and monetary amounts
use two. A temporary subtotal-plus-tax sum may exceed the range if discount brings
the final stored total back into range. Run
`python -m unittest tests.test_document_totals -v` for complete-document checks.

## Computed-field tampering tests

Task 5.8 adds `tests/test_financial_tampering.py`. JSON arrays validated through
`LineItemInput` reject injected `line_total`, `subtotal`, `tax_amount`,
`discount_amount`, and `total` fields, including null and structured values.
The totals service refuses these fields as keyword arguments; a valid input
still produces all five expected backend-derived amounts after rejected attempts.

These tests cover the existing shared validation and calculation boundaries.
They do not claim coverage of future Quote, Invoice, or Receipt HTTP endpoints;
those request schemas and routes must preserve these rules when implemented.
Run `python -m unittest tests.test_financial_tampering -v` for the focused checks.

## Quote numbering

Task 6.1 adds `next_quote_number(connection, *, user_id)` in
`app/common/numbering.py`. Each user starts at `QT-0001`; four digits are a minimum
width, so allocation continues as `QT-10000` and beyond. An atomic PostgreSQL
upsert increments that user's persistent counter. Concurrent allocations for the
same user serialize on the counter row; other users have independent sequences.

Migration `002_quote_numbering.sql` adds the internal counter table, seeds it from
the largest existing numeric `QT-` suffix per user, and adds a trigger preventing
changes to stored quote numbers. The existing `(user_id, quote_number)` uniqueness
constraint remains the final duplicate safeguard. Deleting a quote does not reset
the counter. Legacy nonnumeric numbers are preserved and excluded from seeding.

Call the allocator inside the same transaction that creates the quote and items;
rollback then restores the allocation too. A standalone call commits its allocation
and can leave a gap if unused. Always allocate through this helper for new quotes;
manual inserts do not advance counters. Exhausting the signed BIGINT sequence
returns `QUOTE_NUMBER_EXHAUSTED` (409). Apply pending migrations with
`python -m app.db migrate` before using the allocator in the application database.

Run `python -m unittest tests.test_quote_numbering tests.test_database -v` for
concurrency, independent users, rollback, deletion, immutability, and upgrade tests.

## Invoice numbering

Task 6.2 adds `next_invoice_number(connection, *, user_id)` alongside Quote
numbering. Each user has an independent sequence beginning at `INV-0001`, with
minimum four-digit padding. Invoice allocations do not advance Quote counters.
Atomic counter upserts serialize concurrent allocations for the same user.

Migration `003_invoice_numbering.sql` creates `invoice_number_counters`, seeds
it from existing numeric `INV-` suffixes, and prevents changes to persisted invoice
numbers. Deleting invoices does not reuse committed allocations. Call the helper
inside invoice creation's transaction so failures roll back both document and
allocation; standalone allocations commit and may leave gaps if unused. Manual
inserts do not advance counters. Sequence exhaustion returns
`INVOICE_NUMBER_EXHAUSTED` (409).

Apply pending migrations with `python -m app.db migrate` before using this helper
in the application database. Run
`python -m unittest tests.test_invoice_numbering tests.test_quote_numbering tests.test_database -v`
for concurrency, rollback, upgrades, immutability, and independent-sequence checks.

## Receipt numbering

Task 6.3 adds `next_receipt_number(connection, *, user_id)`, allocating an
independent per-user sequence from `RCT-0001`. Atomic counter upserts serialize
concurrent allocations, and numbering expands beyond four digits as needed.
Quote and Invoice counters are unaffected.

Migration `004_receipt_numbering.sql` adds `receipt_number_counters`, seeds it
from existing numeric `RCT-` suffixes, and prevents changes to stored receipt
numbers. Deleting a receipt does not reset its counter. Call the helper inside
the receipt-creation transaction to roll back allocation with failed creation;
standalone allocations commit and can leave gaps. Manual inserts do not advance
counters. Exhaustion returns `RECEIPT_NUMBER_EXHAUSTED` (409).

Apply pending migrations with `python -m app.db migrate` before using the helper
in the application database. The deletion test proves allocation state survives
row removal; it does not decide or implement the deferred Receipt deletion API.
Run `python -m unittest tests.test_receipt_numbering tests.test_invoice_numbering tests.test_quote_numbering tests.test_database -v`
for all numbering and database checks.

## Quote model

Task 7.1 adds `Quote` and `QuoteStatus` in `app/quotes/models.py`. The immutable
row model includes UUID ownership/client references, number, dates, currency,
Decimal financial fields, status, notes/terms, and timestamps. It reuses the
shared `DiscountType` enum. Quote statuses are DRAFT, SENT, ACCEPTED, REJECTED,
EXPIRED, and CONVERTED, matching PostgreSQL.

The existing table supplies defaults and enforces foreign keys, per-user number
uniqueness, nonnegative financial values, and expiry on or after issue date.
Documented indexes already exist, so this task needs no migration. This row model
does not authorize client ownership, compute totals, or enforce status transitions;
those rules belong to later request/service tasks. QuoteItem is task 7.2.
Run `python -m unittest tests.test_quotes -v` for PostgreSQL mapping and constraints.

## Quote item model

Task 7.2 adds immutable `QuoteItem` rows in `app/quotes/models.py`, containing
UUID, quote UUID, description, Decimal quantity/unit price/line total, and position.
The existing table enforces positive quantity, nonnegative prices/totals, required
fields, and a valid parent. Quantity uses NUMERIC(12,3); price and total use
NUMERIC(14,2). Position defaults to zero. The parent index and ON DELETE CASCADE
already exist, so no migration is needed.

Deleting a quote removes its own items, leaving other quotes and items intact.
The model does not authorize parent deletion or calculate amounts. Later creation
services must use shared input validation and authoritative totals before storage.
Run `python -m unittest tests.test_quote_items tests.test_quotes -v` for row mapping,
database constraints, precision, scoped cascade behavior, and rollback checks.

## Quote creation validation

Task 7.3 adds `QuoteCreate` in `app/quotes/schemas.py`. Client UUID, issue date,
currency, and a nonempty item list are required. Expiry is nullable and cannot
precede issue date. Notes and terms are nullable; tax defaults to zero, discount
type to NONE, and discount value to zero. Currency and nested items reuse shared
validators. Tax fits NUMERIC(6,3); discount value fits NUMERIC(14,2). NONE requires
zero value, and percentage discounts cannot exceed 100.

Unknown/server-managed fields are rejected, including owner, number, status,
timestamps, and all computed totals. `validate_quote_create()` in
`app/quotes/validation.py` accepts the parsed request and authenticated owner ID,
checks the user-scoped client query, and derives validated totals using the shared
service. Missing and foreign clients return `CLIENT_NOT_FOUND` (404); financial
errors propagate from the shared calculator. The function returns `DocumentTotals`
without allocating numbers or writing rows. Creation and HTTP routing remain
tasks 7.4 and 7.5. Run `python -m unittest tests.test_quote_validation -v`.

## Atomic Quote creation

Task 7.4 adds `create_quote(connection, *, user_id, payload)` in
`app/quotes/service.py`. Pass the authenticated user's UUID and a parsed
`QuoteCreate`. One transaction validates client ownership and derives shared
totals, allocates the Quote number, inserts the Quote, and inserts every item.
The database supplies UUIDs, timestamps, and DRAFT status. Calculated amounts
are persisted from `DocumentTotals`; supplied item positions are retained.

The immutable `CreatedQuote` result contains the stored `Quote` and a tuple of
stored `QuoteItem` objects in request order. A failure rolls back the parent,
all items, and number allocation. The service respects an enclosing transaction,
so outer rollback also undoes creation. It adds no HTTP route or migration;
the creation endpoint remains task 7.5. Callers must use validated input rather
than unchecked model construction or mutation.

Run `python -m unittest tests.test_quote_creation -v` for persistence, rejected
ownership/finances, forced later-item failure, outer rollback, and concurrent creation.

## Quote detail endpoint

Task 8.3 adds `GET /api/v1/quotes/{quote_id}`. It returns the saved quote and
items in position/UUID order. Missing and foreign-owned IDs both produce
`QUOTE_NOT_FOUND` (404). Reads return persisted totals without recalculating them.
Run `python -m unittest tests.test_quote_detail -v`.

## Quote list endpoint

Task 8.2 exposes authenticated `GET /api/v1/quotes?page=1&page_size=20`.
The query layer limits and counts only your quotes, newest first (UUID breaks
timestamp ties), and batch-loads clients and items. The response contains stored
quote fields/items plus page metadata; amounts remain decimal strings. Maximum
page size is 100. Run `python -m unittest tests.test_quote_list tests.test_quote_queries -v`.

## Quote creation endpoint

Task 7.5 exposes `POST /api/v1/quotes` with access bearer authentication. The route
parses `QuoteCreate`, obtains ownership from `get_current_user()`, and calls the
atomic creation service. Success returns HTTP 201 with `data` containing the
stored Quote fields and an `items` array of stored QuoteItems in request order.
UUIDs/dates are JSON strings, financial Decimals remain strings, status is DRAFT,
and the number is generated server-side. Responses use `Cache-Control: no-store`.

Invalid input and submitted computed/server-managed fields return 422; missing
or foreign clients return 404 `CLIENT_NOT_FOUND`; invalid authentication returns
401. Unexpected persistence failures return a generic 500 after rollback. The
endpoint adds no migration. Quote read/update endpoints remain later tasks.
Run `python -m unittest tests.test_quote_endpoint tests.test_quote_creation -v`
for HTTP behavior and transactional persistence tests.

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
