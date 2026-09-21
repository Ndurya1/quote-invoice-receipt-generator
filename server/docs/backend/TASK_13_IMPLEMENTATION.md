# Task 13 — Quote to Invoice Conversion

Implemented on `feature/quote-invoice-conversion` through four independently
committed subtasks:

- `feat(conversion): validate quote conversion eligibility`
- `feat(conversion): implement quote to invoice transaction`
- `feat(conversion): expose quote to invoice endpoint`
- `test(conversion): cover quote to invoice workflow`

`POST /api/v1/quotes/{quote_id}/convert` accepts an issue date and optional
due date. It requires an authenticated owner and an `ACCEPTED` Quote. The
conversion validator locks the Quote, rejects foreign/missing records,
invalid statuses, and duplicate source invoices.

The conversion service creates an independent `DRAFT` Invoice and new
InvoiceItems using the shared financial validation and totals engine. It
copies owner, client, currency, notes, and terms, links
`source_quote_id`, allocates a separate Invoice number, and transitions the
Quote to `CONVERTED` in the same transaction.

Failures roll back the Invoice, items, number allocation, and Quote status.
The original QuoteItems remain independent and unchanged. Tests cover
successful conversion, metadata and totals, lineage, independent numbering,
invalid states, duplicate conversion, ownership, request validation, and
database-failure rollback.
