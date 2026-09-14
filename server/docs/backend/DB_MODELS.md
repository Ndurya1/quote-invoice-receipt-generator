# Invoice Generator — Database Models

## Overview

The MVP uses a relational database such as PostgreSQL.

Core models:

1. User
2. BusinessProfile
3. Client
4. Quote
5. QuoteItem
6. Invoice
7. InvoiceItem
8. Receipt
9. ReceiptItem

The system does **not** require a Payment model for the MVP because it does not process payments.

---

## Conventions

- Primary keys: UUID
- Timestamps: `TIMESTAMPTZ`
- Money: `NUMERIC`
- Currency: `CHAR(3)`
- Ownership is user-scoped.
- Document numbers are unique per user and document type.
- Computed monetary fields are persisted for stable rendering and querying but recalculated by the backend.

---

## 1. User

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(120) | NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| phone | VARCHAR(30) | NULL |
| password_hash | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Indexes:
- `UNIQUE(email)`

Relationships:
- User `1:1` BusinessProfile
- User `1:N` Client
- User `1:N` Quote
- User `1:N` Invoice
- User `1:N` Receipt

---

## 2. BusinessProfile

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, UNIQUE, NOT NULL |
| business_name | VARCHAR(160) | NOT NULL |
| logo_url | TEXT | NULL |
| email | VARCHAR(255) | NULL |
| phone | VARCHAR(30) | NULL |
| address | TEXT | NULL |
| tax_number | VARCHAR(100) | NULL |
| default_currency | CHAR(3) | NOT NULL, DEFAULT `KES` |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Constraints:
- `UNIQUE(user_id)`

---

## 3. Client

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| name | VARCHAR(160) | NOT NULL |
| email | VARCHAR(255) | NULL |
| phone | VARCHAR(30) | NULL |
| address | TEXT | NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Indexes:
- `INDEX(user_id)`
- `INDEX(user_id, name)`

Notes:
- Client email is not globally unique.
- Client reuse prevents repetitive data entry.

---

## 4. Quote

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| client_id | UUID | FK → clients.id, NOT NULL |
| quote_number | VARCHAR(40) | NOT NULL |
| issue_date | DATE | NOT NULL |
| expiry_date | DATE | NULL |
| currency | CHAR(3) | NOT NULL |
| subtotal | NUMERIC(14,2) | NOT NULL |
| tax_rate | NUMERIC(6,3) | NOT NULL, DEFAULT 0 |
| tax_amount | NUMERIC(14,2) | NOT NULL, DEFAULT 0 |
| discount_type | ENUM | NOT NULL, DEFAULT `NONE` |
| discount_value | NUMERIC(14,2) | NOT NULL, DEFAULT 0 |
| discount_amount | NUMERIC(14,2) | NOT NULL, DEFAULT 0 |
| total | NUMERIC(14,2) | NOT NULL |
| status | ENUM | NOT NULL, DEFAULT `DRAFT` |
| notes | TEXT | NULL |
| terms | TEXT | NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Suggested status enum:
- `DRAFT`
- `SENT`
- `ACCEPTED`
- `REJECTED`
- `EXPIRED`
- `CONVERTED`

Suggested discount enum:
- `NONE`
- `FIXED`
- `PERCENTAGE`

Constraints:
- `UNIQUE(user_id, quote_number)`
- `CHECK(subtotal >= 0)`
- `CHECK(tax_rate >= 0)`
- `CHECK(tax_amount >= 0)`
- `CHECK(discount_value >= 0)`
- `CHECK(discount_amount >= 0)`
- `CHECK(total >= 0)`
- `CHECK(expiry_date IS NULL OR expiry_date >= issue_date)`

Indexes:
- `INDEX(user_id)`
- `INDEX(user_id, status)`
- `INDEX(client_id)`
- `INDEX(created_at)`

---

## 5. QuoteItem

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| quote_id | UUID | FK → quotes.id ON DELETE CASCADE, NOT NULL |
| description | TEXT | NOT NULL |
| quantity | NUMERIC(12,3) | NOT NULL |
| unit_price | NUMERIC(14,2) | NOT NULL |
| line_total | NUMERIC(14,2) | NOT NULL |
| position | INTEGER | NOT NULL, DEFAULT 0 |

Constraints:
- `CHECK(quantity > 0)`
- `CHECK(unit_price >= 0)`
- `CHECK(line_total >= 0)`

Indexes:
- `INDEX(quote_id)`

Calculation:
- `line_total = quantity × unit_price`

---

## 6. Invoice

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| client_id | UUID | FK → clients.id, NOT NULL |
| source_quote_id | UUID | FK → quotes.id, NULL, UNIQUE |
| invoice_number | VARCHAR(40) | NOT NULL |
| issue_date | DATE | NOT NULL |
| due_date | DATE | NULL |
| currency | CHAR(3) | NOT NULL |
| subtotal | NUMERIC(14,2) | NOT NULL |
| tax_rate | NUMERIC(6,3) | NOT NULL, DEFAULT 0 |
| tax_amount | NUMERIC(14,2) | NOT NULL, DEFAULT 0 |
| discount_type | ENUM | NOT NULL, DEFAULT `NONE` |
| discount_value | NUMERIC(14,2) | NOT NULL, DEFAULT 0 |
| discount_amount | NUMERIC(14,2) | NOT NULL, DEFAULT 0 |
| total | NUMERIC(14,2) | NOT NULL |
| status | ENUM | NOT NULL, DEFAULT `DRAFT` |
| notes | TEXT | NULL |
| terms | TEXT | NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Suggested status enum:
- `DRAFT`
- `SENT`
- `PAID`
- `OVERDUE`
- `CANCELLED`

Constraints:
- `UNIQUE(user_id, invoice_number)`
- `UNIQUE(source_quote_id)`
- `CHECK(subtotal >= 0)`
- `CHECK(tax_rate >= 0)`
- `CHECK(tax_amount >= 0)`
- `CHECK(discount_value >= 0)`
- `CHECK(discount_amount >= 0)`
- `CHECK(total >= 0)`
- `CHECK(due_date IS NULL OR due_date >= issue_date)`

Indexes:
- `INDEX(user_id)`
- `INDEX(user_id, status)`
- `INDEX(client_id)`
- `INDEX(source_quote_id)`
- `INDEX(created_at)`

---

## 7. InvoiceItem

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| invoice_id | UUID | FK → invoices.id ON DELETE CASCADE, NOT NULL |
| description | TEXT | NOT NULL |
| quantity | NUMERIC(12,3) | NOT NULL |
| unit_price | NUMERIC(14,2) | NOT NULL |
| line_total | NUMERIC(14,2) | NOT NULL |
| position | INTEGER | NOT NULL, DEFAULT 0 |

Constraints:
- `CHECK(quantity > 0)`
- `CHECK(unit_price >= 0)`
- `CHECK(line_total >= 0)`

Indexes:
- `INDEX(invoice_id)`

---

## 8. Receipt

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| client_id | UUID | FK → clients.id, NOT NULL |
| source_invoice_id | UUID | FK → invoices.id, NULL |
| receipt_number | VARCHAR(40) | NOT NULL |
| issue_date | DATE | NOT NULL |
| currency | CHAR(3) | NOT NULL |
| subtotal | NUMERIC(14,2) | NOT NULL |
| tax_rate | NUMERIC(6,3) | NOT NULL, DEFAULT 0 |
| tax_amount | NUMERIC(14,2) | NOT NULL, DEFAULT 0 |
| discount_type | ENUM | NOT NULL, DEFAULT `NONE` |
| discount_value | NUMERIC(14,2) | NOT NULL, DEFAULT 0 |
| discount_amount | NUMERIC(14,2) | NOT NULL, DEFAULT 0 |
| total | NUMERIC(14,2) | NOT NULL |
| notes | TEXT | NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Constraints:
- `UNIQUE(user_id, receipt_number)`
- `CHECK(subtotal >= 0)`
- `CHECK(tax_rate >= 0)`
- `CHECK(tax_amount >= 0)`
- `CHECK(discount_value >= 0)`
- `CHECK(discount_amount >= 0)`
- `CHECK(total >= 0)`

Indexes:
- `INDEX(user_id)`
- `INDEX(client_id)`
- `INDEX(source_invoice_id)`
- `INDEX(created_at)`

Design note:
- `source_invoice_id` is nullable because users can create Receipts directly.
- Do not make it UNIQUE unless the product explicitly limits one Receipt per Invoice.

---

## 9. ReceiptItem

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| receipt_id | UUID | FK → receipts.id ON DELETE CASCADE, NOT NULL |
| description | TEXT | NOT NULL |
| quantity | NUMERIC(12,3) | NOT NULL |
| unit_price | NUMERIC(14,2) | NOT NULL |
| line_total | NUMERIC(14,2) | NOT NULL |
| position | INTEGER | NOT NULL, DEFAULT 0 |

Constraints:
- `CHECK(quantity > 0)`
- `CHECK(unit_price >= 0)`
- `CHECK(line_total >= 0)`

Indexes:
- `INDEX(receipt_id)`

---

## Relationship Summary

```text
User
 ├── 1:1 BusinessProfile
 ├── 1:N Client
 ├── 1:N Quote
 │       └── 1:N QuoteItem
 ├── 1:N Invoice
 │       └── 1:N InvoiceItem
 └── 1:N Receipt
         └── 1:N ReceiptItem

Quote 0..1 ─── 0..1 Invoice
Invoice 0..1 ─── N Receipt   (MVP-safe default)
```

---

## Conversion Semantics

### Quote → Invoice

Copy:
- `client_id`
- `currency`
- applicable notes/terms
- items

Recalculate:
- line totals
- subtotal
- tax amount
- discount amount
- total

Set:
- `Invoice.source_quote_id`
- `Quote.status = CONVERTED`

Do not copy:
- Quote number as Invoice number

---

### Invoice → Receipt

Copy:
- `client_id`
- `currency`
- applicable notes
- items

Recalculate:
- line totals
- subtotal
- tax amount
- discount amount
- total

Set:
- `Receipt.source_invoice_id`

Do not copy:
- Invoice number as Receipt number

---

## Deferred Features

Not part of the MVP schema:
- Payment gateway transactions
- M-Pesa callbacks
- Payment reconciliation
- Multi-user business teams
- Recurring invoices
- Inventory
- Accounting ledger
- Tax filing
- Multi-branch support
- Object-storage document snapshots

## Internal Quote Number Allocation (Task 6.1)

Migration `002_quote_numbering.sql` adds `quote_number_counters`:

| Field | Type | Constraints |
|---|---|---|
| user_id | UUID | PK, FK to users.id, ON DELETE RESTRICT |
| last_number | BIGINT | NOT NULL, CHECK > 0 |

This internal table stores the last allocated quote suffix per user. Atomic
upserts serialize allocations; counters survive quote deletion and roll back
with enclosing quote-creation transactions. The migration seeds counters from
existing numeric `QT-` suffixes. New quotes must use the allocator; arbitrary
manual inserts do not advance allocation state. The migration also installs a
trigger rejecting changes to persisted `quotes.quote_number` values.
