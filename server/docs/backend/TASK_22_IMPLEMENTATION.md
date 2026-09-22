# Task 22 — Database Constraint Verification

Implemented on `feature/db-constraints-verification` through four
independently committed database test subtasks:

- `test(database): cover document number uniqueness`
- `test(database): cover document date constraints`
- `test(database): cover monetary constraints`
- `test(database): cover document source constraints`

The tests execute direct PostgreSQL inserts against isolated schemas, proving
that the database itself rejects duplicate same-owner document numbers,
invalid document date ranges, negative monetary values, and duplicate Quote to
Invoice links. They also verify that the same document number can be reused by
another owner and that multiple Receipts can reference one Invoice.

No schema or production-code changes were required.
