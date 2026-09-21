# Task 12 — Invoice Lifecycle Actions

Implemented on `feature/invoice-app` through five independently committed
subtasks:

- `feat(invoices): add invoice status transition service`
- `feat(invoices): add mark sent action`
- `feat(invoices): add mark paid action`
- `feat(invoices): add cancel invoice action`
- `test(invoices): cover invoice status actions`

The transition service locks an owned Invoice, validates the explicit status
matrix, updates only the status and database-managed `updated_at`, and returns
the persisted invoice with its items. Missing or foreign invoices return
`INVOICE_NOT_FOUND`; invalid and repeated transitions return
`INVALID_INVOICE_STATUS`.

The supported matrix is:

```text
DRAFT   -> SENT, CANCELLED
SENT    -> PAID, CANCELLED
OVERDUE -> PAID, CANCELLED
PAID    -> terminal
CANCELLED -> terminal
```

The action endpoints are authenticated and owner-scoped:

- `POST /api/v1/invoices/{invoice_id}/send`
- `POST /api/v1/invoices/{invoice_id}/mark-paid`
- `POST /api/v1/invoices/{invoice_id}/cancel`

No payment transaction or Payment row is created by `mark-paid`. OVERDUE is
documented as a future date-based status; no scheduler or automatic status
assignment is included in this task.
