# Task 10: Invoice persistence and direct creation

Invoice and InvoiceItem map the existing tables in migration 001; migration 003
already supplies transactional invoice numbering and number immutability.
No schema migration is required. The nullable unique source_quote_id preserves
the one-invoice-per-quote relationship and restricts deletion of linked history.

POST /api/v1/invoices requires an access bearer token. The request mirrors quote
creation with nullable due_date instead of expiry_date. Client, issue_date,
currency, and at least one item are required. Due date cannot precede issue date.
Shared currency, item, decimal, tax, and discount validation applies.
Ownership, source_quote_id (including null), numbers, status, timestamps, and
computed fields cannot be submitted. Missing or foreign clients return 404
CLIENT_NOT_FOUND; invalid input returns 422.

create_invoice validates client ownership and calculates authoritative totals,
allocates an INV number, and inserts the invoice and all items in one transaction.
Direct invoices have source_quote_id null and DRAFT status. Any failure rolls
back the parent, items, and allocation, including within an enclosing transaction.

Success returns 201 with persisted invoice fields and items in the data envelope,
decimal amounts serialized as strings, and Cache-Control: no-store. Unexpected
database failures return the existing safe 500 error envelope.

Verification (requires TEST_DATABASE_URL for PostgreSQL integration tests):

```sh
python -m unittest tests.test_invoices tests.test_invoice_items tests.test_invoice_validation tests.test_invoice_creation tests.test_invoice_endpoint tests.test_invoice_numbering -v
```
