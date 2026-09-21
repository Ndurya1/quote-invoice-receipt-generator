# Task 15 — Receipt Read/Update/Delete

Implemented on `feature/receipt-crud` through six independently committed
subtasks:

- `feat(receipts): add user scoped receipt queries`
- `feat(receipts): add receipt list endpoint`
- `feat(receipts): add receipt detail endpoint`
- `feat(receipts): add receipt update service`
- `feat(receipts): add receipt update endpoint`
- `feat(receipts): enforce receipt deletion rules`

Receipt reads are owner-scoped, use consistent transactional snapshots, and
load line items in batched queries. The API now exposes paginated collection
reads, detail reads, PATCH, and DELETE with the standard response envelopes
and `Cache-Control: no-store` headers.

Receipt edits are restricted to direct Receipts with no source Invoice.
PATCH merges editable fields into the persisted document, validates the
complete request through the shared client and totals logic, and protects
receipt number, owner, source Invoice, timestamps, and computed values.
Replacing items is atomic and does not affect any source document.

Direct Receipts may be hard-deleted. Invoice-linked Receipts cannot be
edited or deleted and return `INVALID_RECEIPT_STATUS`. Deletion cascades
ReceiptItems and does not reuse the deleted receipt number. Missing and
foreign resources return `RECEIPT_NOT_FOUND`.

Coverage includes pagination, tenant isolation, detail reads, partial
recalculation, item replacement, server-managed field rejection, foreign
clients, source-link protection, deletion behavior, rollback, and number
preservation.
