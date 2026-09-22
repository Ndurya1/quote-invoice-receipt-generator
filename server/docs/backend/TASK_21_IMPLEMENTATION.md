# Task 21 — Tenant Isolation Security Pass

Implemented on `feature/tenant-isolation` through five independently committed
security test subtasks:

- `test(security): cover client tenant isolation`
- `test(security): cover quote tenant isolation`
- `test(security): cover invoice tenant isolation`
- `test(security): cover receipt tenant isolation`
- `test(security): reject foreign client references`

Coverage verifies that cross-tenant resources are indistinguishable from
missing resources and cannot be read, changed, deleted, transitioned,
converted, or downloaded. Direct Quote, Invoice, and Receipt creation also
rejects foreign client UUIDs before creating documents, items, or allocating
document numbers.

No production code or database migration was required; the existing
authenticated-owner query and service boundaries satisfy the documented
isolation rules.
