# Task 20 — PDF Generation

Implemented on `feature/PDF-generation` through four independently committed
subtasks:

- `feat(pdf): add document render context`
- `feat(pdf): add document PDF renderers`
- `feat(pdf): add document PDF endpoints`
- `test(pdf): cover PDF integrity and authorization`

PDFs are generated from owner-scoped persisted business, client, document, and
line-item records. Quote, Invoice, and Receipt renderers share the same
ReportLab layout primitives while preserving document-specific metadata.

The three PDF routes return `application/pdf`, a persisted-number filename, and
`Cache-Control: no-store`. Missing or foreign documents use the existing
resource-specific not-found errors. Query parameters are ignored and cannot
override persisted totals or document fields.
