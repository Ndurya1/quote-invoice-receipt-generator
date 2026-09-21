# Task 11 — Invoice Read/Update/Delete Implementation

Implemented on `feature/invoice-app` through six independently committed
subtasks:

- `feat(invoices): add user scoped invoice queries`
- `feat(invoices): add invoice list endpoint`
- `feat(invoices): add invoice detail endpoint`
- `feat(invoices): add invoice update service`
- `feat(invoices): add invoice update endpoint`
- `feat(invoices): enforce invoice deletion rules`

The Invoice query layer scopes every read by `user_id`, loads line items in a
batched query, preserves newest-first pagination, and supports row locks for
mutations. The API now exposes list, detail, PATCH, and DELETE endpoints with
the standard response envelopes and `Cache-Control: no-store` headers.

Invoice edits are restricted to unlinked drafts. PATCH input is merged with
the persisted document, validated as a complete InvoiceCreate payload, and
passed through the shared client and totals validation. Number, owner, source
quote, status, timestamps, and computed values cannot be supplied by callers.
Replacing items deletes and recreates only the invoice's item rows inside the
same transaction.

Deletion is restricted to unlinked drafts, cascades invoice items, and is
blocked when a Receipt references the invoice. Missing and foreign invoices
are deliberately indistinguishable through `INVOICE_NOT_FOUND`.

Coverage includes query isolation and pagination, list/detail authorization,
partial updates, financial recalculation, forged-field rejection, foreign
clients, status conflicts, deletion behavior, receipt references, rollback,
and numbering preservation.
