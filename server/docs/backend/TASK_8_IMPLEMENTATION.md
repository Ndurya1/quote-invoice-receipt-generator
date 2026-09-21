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

## Final implementation notes

Read queries take shared row locks until the selected parents and their items
are loaded; updates/deletes take exclusive row locks through commit. This keeps
each returned quote's fields and items consistent during concurrent mutations.
Related clients/items remain batched. Page counts and page selection are separate
statements, so collection metadata can change during concurrent creation/deletion.

No schema migration or dependency change was required. Client data is loaded for
internal callers; HTTP responses retain the existing client_id representation.
Currency edits relabel values without FX conversion. A shared item-insertion
helper serves both creation and replacement; creation keeps request item order,
while reads and updates order items by position and UUID.

## Explaining the finished change

### In everyday terms

Users can browse their saved quotes, open one, correct an unfinished draft, or
delete that draft. The server calculates the money and prevents access to other
users' quotes. Once a quote leaves DRAFT, this MVP preserves it as history.
If saving replacement items fails, the original quote and items remain intact.

### Code walkthrough

1. `app/quotes/router.py` exposes GET collection/detail, PATCH and DELETE beside
   the existing POST. Authentication supplies the user ID; the request cannot
   select ownership. Routes return the existing resource/collection envelopes.
2. `app/quotes/schemas.py` describes responses and the writable PATCH fields.
   `exclude_unset=True` distinguishes an omitted value from an explicit null.
   Extra fields are forbidden, including computed totals and lifecycle status.
3. `app/quotes/queries.py` applies ownership before selecting records. It fetches
   related clients/items in batches, so fetching more quotes does not create a
   separate query for every quote. Shared locks keep each quote and its items
   consistent while loading.
4. `app/quotes/service.py` owns mutations. It locks the quote, checks DRAFT and
   invoice linkage, merges saved and submitted fields, validates the complete
   document, invokes the existing calculator, and writes within one transaction.
   An exclusive lock serializes competing mutations to the same quote.
5. Existing database triggers update timestamps; foreign keys cascade quote
   items and restrict invoice-linked deletion. No migration is needed.

### Examples and decisions

- A quote with subtotal 100, tax 16%, and fixed discount 10 totals 106. PATCHing
  only tax_rate to 10 recalculates its total to 100 using the saved items.
- `{"notes": null}` clears notes. `{}` preserves everything after access/state
  checks. `{"tax_rate": null}` is invalid.
- `items` means full replacement with new item UUIDs; omitting it preserves
  saved item UUIDs. There is no separate per-item edit API in this task.
- DRAFT-only editing/deletion is an explicit conservative policy because the
  source plan left the other statuses undecided. All five other statuses return
  409 INVALID_QUOTE_STATUS. Invoice-linked drafts are protected too.
- Missing and foreign quote IDs share 404 QUOTE_NOT_FOUND to avoid disclosing
  another user's documents. Status cannot be changed through PATCH.
- Shared read locks may briefly delay writes, and mutations may briefly delay
  reads of the same quote. Locks last only for the database operation.
- Pagination defaults to 20, caps at 100, and orders newest first with a UUID
  tie-breaker. Search/filter/sort choices belong to Task 18.3.
- Lifecycle actions and conversion remain their separate planned tasks. The
  history checks here protect existing records/links; they do not implement or
  claim end-to-end coverage of future conversion workflows.

## Completion and verification

- [x] 8.1 User-scoped queries and batched related rows.
- [x] 8.2 Paginated list endpoint.
- [x] 8.3 Detail endpoint with persisted items and totals.
- [x] 8.4 Atomic draft edit service and explicit edit policy.
- [x] 8.5 PATCH endpoint with protected fields and recalculation.
- [x] 8.6 Safe deletion with explicit status policy and consistent concurrent reads.

Added 31 Task 8 tests across six test modules. Relevant subsets passed before
their commits. Final verification on 2026-09-19:

```text
.venv\Scripts\python.exe -m unittest discover -s tests -q
Ran 239 tests in 225.802s
OK
```

The run included real PostgreSQL integration tests, with no skips. `git diff
--check` also passed. The suite emits an existing Starlette/httpx deprecation
warning; no dependency changes were made for it.
