# Task 8: Quote read, update, and delete

## Plan recorded before implementation

1. **8.1** Add `app/quotes/queries.py` and query tests: owner-scoped reads,
   deterministic ordering, batched clients/items, and bounded pagination.
2. **8.2** Extend router/schemas and add list tests: authenticated GET collection,
   page metadata, default 20 and maximum 100 rows, newest first.
3. **8.3** Extend router and add detail tests: persisted values and ordered items;
   missing and foreign quotes share QUOTE_NOT_FOUND (404).
4. **8.4** Extend schemas/service and add update tests: partial input merged with
   stored state, full validation, authoritative recalculation, transactional row
   locking and optional full item replacement. Preserve item IDs when omitted.
5. **8.5** Extend router and add PATCH tests: authenticated edits and standard
   errors; owner, number, status, timestamps and computed fields remain read-only.
6. **8.6** Extend service/router and add deletion tests: atomic draft deletion,
   cascading only its items, with status and invoice-reference protection.

Each numbered subtask receives its own tested commit. Update README and API
contract alongside exposed behavior. Existing schema suffices; no migration.

## Explicit edit/deletion policy

| Status | Edit | Delete |
|---|---|---|
| DRAFT | Yes, unless invoice-linked | Yes, unless invoice-linked |
| SENT | No | No |
| ACCEPTED | No | No |
| REJECTED | No | No |
| EXPIRED | No | No |
| CONVERTED | No | No |

Disallowed operations return 409 INVALID_QUOTE_STATUS. This conservative MVP
policy preserves issued history. Status transitions belong to Task 9.
Expiry, notes and terms accept null to clear; other fields reject explicit null.
Empty PATCH is a no-op after ownership/state checks. Supplied items replace the
entire collection atomically; omitted items retain their identities. No invoice
or receipt is updated. Conversion and filtering remain separate planned tasks.

## Validation strategy

Use real PostgreSQL integration tests for isolation, pagination, persisted
decimal values, merged validation, recalculation, rollback, status restrictions,
and deletion cascades. Run each relevant subset before its commit, inspect the
diff, then run the complete backend suite after Task 8.
