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
