# Task 18 — Filtering, Search, Sorting, Pagination

Implemented on `feature/filtering-searching` through five independently
committed subtasks:

- `feat(api): add collection pagination`
- `feat(clients): add client search and sorting`
- `feat(quotes): add quote filters and sorting`
- `feat(invoices): add invoice filters and sorting`
- `feat(receipts): add receipt filters and sorting`

All collection filters are applied after authenticated-owner scoping and before
the filtered total is calculated or pagination is applied. Sorting uses explicit
SQL field whitelists and UUID tie-breakers, so request values cannot become SQL
identifiers.

Search is case-insensitive. Client search covers name, email, and phone.
Document search covers document number, client name, and persisted free-text
fields where available. Quotes and invoices support status and client filters;
quotes, invoices, and receipts support their documented resource-specific sort
fields.

The existing response envelope, pagination metadata, default ordering, maximum
page size, authentication, and `Cache-Control: no-store` behavior remain intact.
