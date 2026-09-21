# Task 9: Quote lifecycle actions

## 9.1 Transition service

The allowed edges are DRAFT -> SENT, DRAFT -> ACCEPTED, SENT -> ACCEPTED,
SENT -> REJECTED, SENT -> EXPIRED, and ACCEPTED -> CONVERTED. All other
transitions, including repeats, return 409 INVALID_QUOTE_STATUS.

`transition_quote` scopes by authenticated owner and locks the quote before
validating status. Missing and foreign quotes return 404 QUOTE_NOT_FOUND.
Only status is written; the existing database trigger updates updated_at.
Items, totals, numbering, ownership and other document fields are preserved.
The transaction composes with an outer transaction and rolls back on failure.

CONVERTED requires an invoice linked to the quote and its owner. Task 13 will
create that invoice and call this service within one outer transaction; this
task does not implement invoice conversion. EXPIRED has service support but
no scheduler or public expire action. Dates do not implicitly change status.

## 9.2 Mark sent

POST /api/v1/quotes/{quote_id}/send marks DRAFT as SENT and returns the saved
quote and items. Auth, ownership, every disallowed source status, response
integrity and OpenAPI are tested. No message delivery is performed.

## 9.3 Accept

POST /api/v1/quotes/{quote_id}/accept accepts either DRAFT or SENT. Repeated
acceptance and all other source states are conflicts. Tests cover both valid
paths, all invalid states, ownership, authentication and response integrity.

## 9.4 Reject

POST /api/v1/quotes/{quote_id}/reject changes SENT to REJECTED. Drafts cannot
be rejected directly. Tests cover send-then-reject, all invalid source states,
authentication, ownership and the API contract.

## 9.5 Lifecycle verification

The tests cover all 36 source/target pairs against PostgreSQL, including all
six valid transitions, terminal statuses and repeated requests. They assert
that failures leave the complete quote unchanged and successes preserve every
field except status and updated_at, including item IDs and financial values.

Two-connection tests exercise duplicate send and competing accept/reject.
Exactly one request wins; the other sees the committed status and returns a
conflict. A simulated database failure returns a generic 500 without leaking
internal details and rolls back the status/timestamp update.

Conversion integration here is limited to the transition primitive: a fixture
invoice and CONVERTED status both roll back when their outer transaction fails,
and both persist when it succeeds. Full conversion and copying remain Task 13.

HTTP tests cover every invalid source state for each action, missing/foreign
quotes, malformed IDs, missing/invalid/refresh tokens, OpenAPI, response data,
and forged body/query fields. Actions declare no request body; extra body/query
fields are ignored and never control stored fields or the action's target.
Real send/accept/reject flows also verify existing draft-only edit/delete rules.

## Code walkthrough

- `app/quotes/service.py`: one explicit allowed-transition set, a reusable
  validator, and a transactional transition function. The existing owner-scoped
  query takes a row lock before checking status. Existing timestamp triggers
  handle updated_at. No schema changes are required.
- `app/quotes/router.py`: three authenticated routes select fixed target statuses
  and serialize the returned persisted quote/items through QuoteResponse.
- `tests/test_quote_transitions.py`: service rules, persistence, authorization,
  transaction composition and concurrent status changes.
- `tests/test_quote_actions.py`: API access, response and failure behavior.
- `docs/backend/API_CONTRACT.md` and `README.md`: supported actions and policies.

## Completion and verification

- [x] 9.1 Central transition service and transaction safety.
- [x] 9.2 Mark-sent endpoint.
- [x] 9.3 Accept endpoint.
- [x] 9.4 Reject endpoint.
- [x] 9.5 Complete transition matrix and lifecycle regression coverage.

Verification on 2026-09-21:

- Task 9 subset: 22 tests passed in 94.884s, with no skips.
- Full backend discovery: 315 tests passed in 366.236s, with no skips.
- `git diff --check` passed.

Tests used the existing Python virtual environment and PostgreSQL test database
configuration from the primary workspace, loaded without copying or exposing
credentials. Test discovery ran from C:/backend/server, so it exercised this
worktree's code. Equivalent commands with the test environment configured:

```text
python -m unittest tests.test_quote_transitions tests.test_quote_actions
python -m unittest discover -s tests
```

An earlier run was interrupted by a full local disk. After space was freed,
the focused tests and full regression suite both completed successfully.
The existing Starlette/httpx deprecation warning remains; dependencies were
not changed as part of this task.
