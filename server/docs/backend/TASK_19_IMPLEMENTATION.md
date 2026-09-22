# Task 19 — Dashboard

Implemented on `feature/dashboard` through two independently committed
subtasks:

- `feat(dashboard): add dashboard summary aggregation service`
- `feat(dashboard): add summary endpoint`

`GET /api/v1/dashboard/summary` returns owner-scoped quote, invoice, and
receipt counts plus the five most recent documents across all three resources.
The aggregation is built inside one database transaction so counts and recent
documents come from one consistent snapshot. No payment aggregates are
included because the MVP has no Payment model.

Recent documents include their resource type, UUID, document number, client,
issue date, currency, total, status where supported, and creation timestamp.
All dashboard responses use the standard data envelope and `Cache-Control:
no-store`.
