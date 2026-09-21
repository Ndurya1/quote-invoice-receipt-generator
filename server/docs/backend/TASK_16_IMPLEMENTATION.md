# Task 16 — Invoice to Receipt Conversion

Implemented on `feature/invoice-receipt-conversion` through four independently
committed subtasks:

- `feat(conversion): validate invoice conversion eligibility`
- `feat(conversion): implement invoice to receipt transaction`
- `feat(conversion): expose invoice to receipt endpoint`
- `test(conversion): cover invoice to receipt workflow`

`POST /api/v1/invoices/{invoice_id}/convert` accepts an `issue_date` and
creates a Receipt linked through `source_invoice_id`. The operation is
owner-scoped, copies the Invoice client, currency, tax, discount, notes, and
line items, then recalculates Receipt totals through the existing validation
logic.

Only `CANCELLED` invoices are ineligible. DRAFT, SENT, PAID, and OVERDUE
invoices can be converted. Multiple Receipts may be created from one Invoice;
each receives the next shared Receipt number. The source Invoice is never
mutated and conversion does not mark it paid.

Receipt creation, line-item insertion, and number allocation run in one
transaction. Any failure rolls back the Receipt, ReceiptItems, and number
counter, while the source Invoice remains unchanged. Missing and foreign
invoices are intentionally reported as `INVOICE_NOT_FOUND`.

Coverage includes service validation, metadata and lineage, repeated
conversions, shared numbering, request validation, authentication, ownership
isolation, OpenAPI documentation, source immutability, and rollback behavior.
