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
namespace. Neither endpoint checks database connectivity. PostgreSQL setup and
migrations belong to Task 1.2; do not apply the current SQL draft yet.

## Tests

The foundation uses standard-library unittest discovery and FastAPI's TestClient.
No database is required for these tests.

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
