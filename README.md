# DocuFlow

DocuFlow helps freelancers and small businesses create quotations, invoices, and receipts in one connected workspace. Save business and client details, reuse them across documents, track document states, and download PDFs.

The core workflow is **Account → Business setup → Client → Quotation → Invoice → Receipt → PDF**. Invoices and receipts can also be created directly.

## Features

- Account registration, login, access-token refresh, and protected workspace routes.
- Two-step business onboarding and editable business settings.
- Client creation, search, editing, and deletion subject to document-reference rules.
- Quotation, invoice, and receipt forms with line items, tax, discounts, and decimal-based total previews.
- Quotation acceptance/rejection, invoice status changes, and linked document conversion.
- Unified document search, filtering, sorting, and pagination.
- Dashboard counts, recent documents, and overdue attention.
- Authenticated PDF downloads with server-calculated totals.
- Responsive layouts and development-only preview fixtures.
- Public Privacy Policy and Terms of Service pages.

Payment statuses are recorded by the business. DocuFlow does not process or verify payments. **Mark as sent** updates a document's status; users download and deliver PDFs through their own tools.

## Technology

| Layer | Tools |
| --- | --- |
| Frontend | React 19, React Router 7, Vite 8, Tailwind CSS 4, Lucide |
| Backend | Python 3.13+, FastAPI, Pydantic, Psycopg |
| Database | PostgreSQL with versioned SQL migrations |
| Authentication | Signed JWT access/refresh tokens and Argon2 password hashing |
| PDFs | ReportLab |
| Tests | Node test runner, Python unittest, FastAPI TestClient |

The browser calls the FastAPI API under `/api/v1`. Only the backend accesses PostgreSQL. The backend enforces record ownership, document lifecycle rules, numbering, and financial calculations.

## Repository structure

```text
client/
  invoice-client/        React application, package scripts, and frontend tests
    src/                Pages, layouts, API adapters, and feature modules
    test/               Node test suites
  docs/                 Frontend direction, implementation plan, and QA guidance
server/
  app/                  FastAPI application and domain services
  migrations/           Ordered SQL migrations
  tests/                Backend unit and PostgreSQL integration tests
  docs/backend/         API contract, database models, and implementation notes
  Dockerfile            Backend container image
```

## Prerequisites

- Node.js compatible with the installed Vite package: `^20.19.0` or `>=22.12.0`, plus npm.
- Python 3.13 or later and [uv](https://docs.astral.sh/uv/).
- A running PostgreSQL instance with an application database and a role allowed to apply migrations.
- A separate PostgreSQL database for integration tests.

Commands below use PowerShell and start from the repository root unless stated otherwise. Use `npm.cmd` instead of `npm` if PowerShell blocks npm scripts.

## Run locally

### 1. Configure the backend

```powershell
cd server
uv sync --frozen
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `server/.env` with your local database credentials and a private signing key. The example credentials are placeholders; the application database must already exist.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Application PostgreSQL connection URL |
| `TEST_DATABASE_URL` | Separate test database URL; database name must end in `_test` |
| `JWT_SECRET_KEY` | Private random signing key of at least 32 bytes; required for authentication |
| `JWT_ACCESS_TOKEN_MINUTES` | Access-token lifetime; defaults to `15` |
| `JWT_REFRESH_TOKEN_DAYS` | Refresh-token lifetime; defaults to `7` |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origins, including `http://localhost:5173` locally |
| `APP_ENV` | `development`, `test`, or `production` |

Generate a signing key locally and copy it into `JWT_SECRET_KEY`:

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep the key and database credentials private. Percent-encode reserved characters in database URL credentials, such as `@` as `%40`.

### 2. Apply migrations and start the API

From `server`:

```powershell
uv run python -m app.db check
uv run python -m app.db migrate
uv run python -m uvicorn app.main:app --env-file .env --reload
```

- API: `http://localhost:8000/api/v1`
- Interactive API documentation: `http://localhost:8000/docs`
- Health endpoint: `http://localhost:8000/health`

The health endpoint checks application availability, not database connectivity. The development server does not apply migrations automatically; the database commands load `server/.env` themselves.

### 3. Configure and start the frontend

Open another terminal at the repository root:

```powershell
cd client/invoice-client
npm ci
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
```

Set these values in `client/invoice-client/.env.local`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_AUTH_PREVIEW=false
```

Then start Vite:

```powershell
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`. Create an account, complete business onboarding, add a client, and create your first document.

The default API base URL is `/api/v1`, but the current Vite configuration has no development proxy. Use the absolute API URL above for separate local servers. If Vite selects another port, add its exact origin to the backend CORS configuration. Restart the relevant server after changing environment settings.

## Developer preview

To explore the frontend without a backend session, set `VITE_AUTH_PREVIEW=true` in the frontend's `.env.local` and restart `npm run dev`.

Preview mode provides a marked fixture session and sample data for implemented workspace pages. It is enabled only during Vite development, is not a production administrator role, and does not grant backend privileges. Fixture changes are not production database writes; PDF generation still needs the backend for a real end-to-end check.

Set `VITE_AUTH_PREVIEW=false` and restart Vite when testing real registration, authentication, and persistence.

| Area | Routes |
| --- | --- |
| Public | `/`, `/privacy`, `/terms` |
| Authentication | `/register`, `/login` |
| Onboarding | `/onboarding/business`, `/onboarding/defaults`, `/onboarding/complete` |
| Workspace | `/dashboard`, `/documents` |
| Clients | `/clients`, `/clients/new`, `/clients/:clientId`, `/clients/:clientId/edit` |
| Quotations | `/documents/quotations/new`, `/documents/quotations/:quoteId`, `/documents/quotations/:quoteId/edit` |
| Invoices | `/documents/invoices/new`, `/documents/invoices/:invoiceId`, `/documents/invoices/:invoiceId/edit` |
| Receipts | `/documents/receipts/new`, `/documents/receipts/:receiptId`, `/documents/receipts/:receiptId/edit` |
| Settings | `/settings/business`, `/settings/account` |

Example fixture detail routes:

- `/clients/client-001`
- `/documents/quotations/quote-preview-001`
- `/documents/invoices/invoice-preview-001`
- `/documents/receipts/receipt-preview-001`

Outside developer preview, workspace routes require authentication and a completed business profile. Document editing and deletion depend on status and source links; converted documents have stricter protections.

## Testing

From `client/invoice-client`:

```powershell
npm run lint
npm test
npm run test:coverage
npm run build
```

Frontend tests use the Node test runner and include data, API, session, calculation, and mocked workflow checks. They do not replace browser-based responsive and accessibility QA. See the [release QA checklist](client/docs/RELEASE_QA.md) for remaining manual checks.

From `server`, configure `TEST_DATABASE_URL` for a separate database before running integration tests:

```powershell
uv run python -m app.db create-test-db
uv run python -m app.db migrate --test
uv run python -m unittest discover -s tests -v
```

The test database creation helper requires the same host, port, and user as the application connection and a role with `CREATEDB`. If the role lacks that permission, have a database administrator create the test database first. PostgreSQL integration tests use isolated schemas in that database. Database tests skip when no test URL is configured; an invalid configured test database fails rather than falling back to application data.

## Build and deployment

The frontend build is written to `client/invoice-client/dist`. Serve it with a static host configured to return `index.html` for application routes such as `/documents` and `/privacy`. Configure `VITE_API_BASE_URL` before building: use `/api/v1` behind a same-origin reverse proxy or the deployed API origin. Vite variables are exposed to the browser and must not contain secrets.

The backend includes a Dockerfile. From `server`:

```powershell
docker build -t docuflow-api .
docker run --rm -p 8000:8000 --env-file .env docuflow-api
```

The container applies pending migrations before starting Uvicorn. Its PostgreSQL host must be reachable from the container; `localhost` inside a container refers to that container. For production, configure `APP_ENV=production`, `APP_DEBUG=false`, `DATABASE_URL`, `JWT_SECRET_KEY`, explicit `CORS_ALLOWED_ORIGINS`, and `ALLOWED_HOSTS`. Configure HTTPS and trusted proxy addresses for the deployment. See the [backend README](server/README.md) for deployment settings.

## Current limits

- Logout clears the local session; issued refresh tokens are not currently revoked server-side.
- Account settings are read-only. Password recovery and password changes are deferred.
- Onboarding progress is stored locally; profile existence signals completion.
- Products/services, logo uploads, extended branding defaults, document duplication, pre-save conversion review, and native email/WhatsApp delivery are deferred.
- Dashboard totals are counts, not currency-grouped outstanding balances. There is no foreign-exchange conversion.
- Privacy and terms pages are implemented; business-specific legal and operational details are tracked in the [legal page review](client/docs/LEGAL_PAGE_REVIEW.md).

See the [backend follow-up contracts](client/docs/BACKEND_FOLLOW_UP_CONTRACTS.md) for dependencies and acceptance criteria.

## Documentation

- [Frontend setup and scope](client/invoice-client/README.md)
- [Frontend product and architecture direction](client/docs/FRONTEND_DIRECTION.md)
- [Frontend implementation plan](client/docs/FRONTEND_IMPLEMENTATION_PLAN.md)
- [Backend setup and development](server/README.md)
- [API contract](server/docs/backend/API_CONTRACT.md)
- [Database models](server/docs/backend/DB_MODELS.md)
- [Domain invariants](server/docs/backend/INVARIANTS.md)
