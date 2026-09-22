# Task 24 — Query Performance

Task 24 is implemented through two commits:

- `perf(documents): optimize document queries`
- `perf(database): verify MVP indexes`

The document query audit confirms that quote and receipt reads batch-load
clients and line items, while invoice reads batch-load line items. Regression
tests verify that list reads use a fixed number of database cursors regardless
of the number of returned documents, preventing N+1 query regressions.

The database verification covers the documented ownership, status, client,
source-document, creation-time, and client `(user_id, name)` indexes.
