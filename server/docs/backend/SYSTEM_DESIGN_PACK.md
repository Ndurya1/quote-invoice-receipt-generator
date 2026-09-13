# Invoice Generator — System Design Pack



---

<!-- INVARIANTS.md -->

# Invoice Generator — Domain Invariants

## Purpose

This document defines the business rules that must always remain true in the Invoice Generator system.

The product is a document-generation and document-lifecycle tool for freelancers and small-scale service providers. It does **not** process or settle payments. Users manually enter document data and line-item prices, while the platform calculates totals and supports the workflow:

**Quote → Invoice → Receipt**

Users may also create an Invoice or Receipt directly when they do not need the full conversion flow.

---

## 1. Ownership and Tenant Isolation

- Every `BusinessProfile` belongs to exactly one `User`.
- Every `Client` belongs to exactly one `User`.
- Every `Quote` belongs to exactly one `User`.
- Every `Invoice` belongs to exactly one `User`.
- Every `Receipt` belongs to exactly one `User`.
- Every document item belongs to exactly one parent document.
- A user must never read, modify, delete, convert, or download another user's resources.
- Any `Client` referenced by a document must belong to the same user as the document.

Enforcement:
- Foreign keys
- Authentication
- Ownership checks in the service/data-access layer
- Authorization tests

---

## 2. Business Profile

- A user may have at most one active `BusinessProfile` in the MVP.
- Business details are reusable defaults so the user does not repeatedly enter the same data.
- The default currency belongs to the business profile but may be overridden per document.
- Business profile changes must not break existing documents.

Recommended future refinement:
- Snapshot business details into finalized documents so historical documents remain unchanged after profile edits.

---

## 3. Clients

- Clients are reusable records.
- A client belongs to one user.
- A user may reuse the same client across multiple Quotes, Invoices, and Receipts.
- Client email is not globally unique.
- Client details may be partially optional, but `name` is required.

---

## 4. Money and Precision

- Persisted monetary values must use fixed-precision decimal types.
- Binary floating-point types must not be used for persisted monetary values.
- `quantity > 0`.
- `unit_price >= 0`.
- `tax_rate >= 0`.
- `discount_value >= 0`.
- `line_total >= 0`.
- `subtotal >= 0`.
- `tax_amount >= 0`.
- `discount_amount >= 0`.
- `total >= 0`.

For every line item:

`line_total = quantity × unit_price`

For every document:

`subtotal = SUM(line_total)`

Tax:

`tax_amount = subtotal × tax_rate / 100`

Discount:
- if percentage: `discount_amount = subtotal × discount_value / 100`
- if fixed: `discount_amount = discount_value`

Final total:

`total = subtotal + tax_amount - discount_amount`

Rules:
- The frontend may calculate values live for user experience.
- The backend is authoritative and must independently recalculate totals before persistence.
- Client-submitted computed totals are never trusted.
- A discount must never reduce the final total below zero.

---

## 5. Tax and Discount Configuration

For the MVP:

### Tax
- Tax is optional.
- Tax is percentage-based.
- `tax_rate` defaults to `0`.

### Discount
Supported types:
- `NONE`
- `FIXED`
- `PERCENTAGE`

Rules:
- When type is `NONE`, discount value and amount are `0`.
- When type is `PERCENTAGE`, `discount_value` should be between `0` and `100`.
- When type is `FIXED`, the calculated discount must not exceed the permitted document amount.
- The backend derives `discount_amount`.

---

## 6. Currency

- Every Quote, Invoice, and Receipt has exactly one currency.
- Currency is represented using an ISO 4217 code such as `KES`, `USD`, or `EUR`.
- All line items in a document use the document's currency.
- Quote → Invoice conversion preserves currency.
- Invoice → Receipt conversion preserves currency.

---

## 7. Document Numbering

Every document has its own number:
- Quote: `quote_number`
- Invoice: `invoice_number`
- Receipt: `receipt_number`

Examples:
- `QT-0001`
- `INV-0001`
- `RCT-0001`

Rules:
- Numbers are generated server-side.
- Numbers are unique per user and per document type.
- Two different users may both have `QT-0001`.
- Document numbers are immutable after creation.

---

## 8. Quote Lifecycle

Suggested statuses:
- `DRAFT`
- `SENT`
- `ACCEPTED`
- `REJECTED`
- `EXPIRED`
- `CONVERTED`

Allowed transitions:

- `DRAFT → SENT`
- `DRAFT → ACCEPTED`
- `SENT → ACCEPTED`
- `SENT → REJECTED`
- `SENT → EXPIRED`
- `ACCEPTED → CONVERTED`

Rules:
- A converted Quote cannot be converted again.
- A rejected Quote cannot be converted.
- An expired Quote cannot be converted unless a future feature explicitly reopens it.
- Conversion never deletes the original Quote.
- The Quote remains available as historical data.

---

## 9. Quote → Invoice Conversion

A Quote may produce at most one Invoice in the MVP.

During conversion:
- Invoice owner = Quote owner.
- Invoice client = Quote client.
- Invoice currency = Quote currency.
- Relevant notes and terms are copied.
- QuoteItems are copied into InvoiceItems.
- Totals are recalculated by the backend.
- `Invoice.source_quote_id` references the Quote.
- Quote status becomes `CONVERTED`.

Conversion must be atomic:

Either:
- Invoice and InvoiceItems are created, and
- Quote becomes `CONVERTED`

or:
- no state changes are persisted.

The Invoice receives its own independent document number.

---

## 10. Invoice Lifecycle

Suggested statuses:
- `DRAFT`
- `SENT`
- `PAID`
- `OVERDUE`
- `CANCELLED`

Important:
- The application does not process payments.
- `PAID` is a document/business status manually selected or implied by conversion to a Receipt.
- No payment gateway or payment transaction record is required for the MVP.

Rules:
- A cancelled Invoice cannot be converted to a Receipt.
- An Invoice converted into a Receipt remains available as historical data.
- A converted Invoice must not be silently changed by later Receipt edits.

---

## 11. Invoice → Receipt Conversion

An Invoice may be converted into a Receipt.

During conversion:
- Receipt owner = Invoice owner.
- Receipt client = Invoice client.
- Receipt currency = Invoice currency.
- InvoiceItems are copied into ReceiptItems.
- Relevant notes are copied.
- Totals are recalculated by the backend.
- `Receipt.source_invoice_id` references the Invoice.

The Receipt receives its own independent receipt number.

The application does not verify that money moved. The user is responsible for issuing the Receipt appropriately.

---

## 12. Direct Document Creation

The system supports:
- direct Quote creation
- direct Invoice creation
- direct Receipt creation

Therefore the lifecycle is flexible:

`Quote → Invoice → Receipt`

or

`Invoice → Receipt`

or

`Receipt`

Direct creation must obey the same validation and calculation rules as converted documents.

---

## 13. Historical Integrity

Conversion means **copy + link**, not move.

When converting:
- Source document items remain unchanged.
- Destination document items are new rows.
- Later changes to the destination must not mutate the source.

Examples:
- Editing an Invoice does not change its source Quote.
- Editing a Receipt does not change its source Invoice.

This preserves the commercial history.

---

## 14. Dates

Quote:
- `issue_date` is required.
- `expiry_date >= issue_date` when provided.

Invoice:
- `issue_date` is required.
- `due_date >= issue_date` when provided.

Receipt:
- `issue_date` is required.

System timestamps:
- `created_at` and `updated_at` use UTC timestamps.
- Display timezone is a presentation-layer concern.

---

## 15. Deletion Rules

Recommended MVP behavior:

- Draft documents may be hard-deleted.
- Converted Quotes should not be hard-deleted.
- Invoices that have been converted to Receipts should not be hard-deleted.
- Receipts should preferably be archived/voided rather than deleted.

Future refinement:
- Add `archived_at` or `voided_at`.

---

## 16. PDF Generation

- PDFs are generated from persisted backend data.
- PDF endpoints never trust arbitrary totals sent by the client.
- The authenticated user must own the underlying document.
- The generated PDF must use recalculated/persisted values.
- Quote, Invoice, and Receipt PDFs must use their own document numbers and dates.

---

## 17. Transaction Boundaries

The following operations must be transactional:

### Quote Conversion
1. Validate Quote ownership and state.
2. Create Invoice.
3. Copy QuoteItems to InvoiceItems.
4. Recalculate Invoice totals.
5. Link `source_quote_id`.
6. Mark Quote `CONVERTED`.
7. Commit.

### Invoice Conversion
1. Validate Invoice ownership and state.
2. Create Receipt.
3. Copy InvoiceItems to ReceiptItems.
4. Recalculate Receipt totals.
5. Link `source_invoice_id`.
6. Optionally mark Invoice `PAID`/converted according to product rules.
7. Commit.

Any failure causes rollback.



---

<!-- DB_MODELS.md -->

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



---

<!-- API_CONTRACT.md -->

# Invoice Generator — API Contract

## Purpose

This contract defines the frontend/backend boundary for the MVP.

Base path:

`/api/v1`

Transport:
- HTTPS
- JSON for normal API requests/responses
- PDF responses for document downloads

Authentication:
- JWT access token
- refresh token flow

---

## 1. Common Response Shapes

### Single-resource success

```json
{
  "data": {}
}
```

### Collection success

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 0
  }
}
```

### Error

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message.",
    "details": {}
  }
}
```

Suggested HTTP semantics:
- `200` successful read/update
- `201` resource created
- `204` successful delete with no response body
- `400` invalid business input
- `401` unauthenticated
- `403` authenticated but unauthorized
- `404` resource not found
- `409` state conflict
- `422` request validation error
- `500` unexpected server error

---

## 2. Authentication

### Register

`POST /api/v1/auth/register`

Request:

```json
{
  "name": "Muhammad",
  "email": "m@example.com",
  "phone": "0712345678",
  "password": "secret"
}
```

Response:

```json
{
  "data": {
    "id": "uuid",
    "name": "Muhammad",
    "email": "m@example.com",
    "phone": "0712345678"
  }
}
```

---

### Login

`POST /api/v1/auth/login`

Request:

```json
{
  "email": "m@example.com",
  "password": "secret"
}
```

Response:

```json
{
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer"
  }
}
```

---

### Refresh

`POST /api/v1/auth/refresh`

---

### Current User

`GET /api/v1/auth/me`

---

## 3. Business Profile

Because an authenticated user has one business profile:

- `GET /api/v1/business-profile`
- `PUT /api/v1/business-profile`

Example update:

```json
{
  "business_name": "Ndurya Digital",
  "email": "hello@example.com",
  "phone": "0712345678",
  "address": "Kisii, Kenya",
  "tax_number": null,
  "default_currency": "KES",
  "logo_url": null
}
```

---

## 4. Clients

Endpoints:

- `POST /api/v1/clients`
- `GET /api/v1/clients`
- `GET /api/v1/clients/{client_id}`
- `PATCH /api/v1/clients/{client_id}`
- `DELETE /api/v1/clients/{client_id}`

### Create Client

Request:

```json
{
  "name": "Acme Ltd",
  "email": "accounts@acme.com",
  "phone": "0712345678",
  "address": "Nairobi, Kenya"
}
```

---

## 5. Quotes

Endpoints:

- `POST /api/v1/quotes`
- `GET /api/v1/quotes`
- `GET /api/v1/quotes/{quote_id}`
- `PATCH /api/v1/quotes/{quote_id}`
- `DELETE /api/v1/quotes/{quote_id}`
- `POST /api/v1/quotes/{quote_id}/send`
- `POST /api/v1/quotes/{quote_id}/accept`
- `POST /api/v1/quotes/{quote_id}/reject`
- `POST /api/v1/quotes/{quote_id}/convert`
- `GET /api/v1/quotes/{quote_id}/pdf`

### Create Quote

Request:

```json
{
  "client_id": "uuid",
  "issue_date": "2026-09-12",
  "expiry_date": "2026-09-26",
  "currency": "KES",
  "tax_rate": "16.000",
  "discount_type": "FIXED",
  "discount_value": "2000.00",
  "notes": "Thank you for considering our services.",
  "terms": "Quote valid for 14 days.",
  "items": [
    {
      "description": "Website development",
      "quantity": "1.000",
      "unit_price": "30000.00"
    },
    {
      "description": "Hosting setup",
      "quantity": "1.000",
      "unit_price": "5000.00"
    }
  ]
}
```

The client does **not** authoritatively submit:
- `quote_number`
- `line_total`
- `subtotal`
- `tax_amount`
- `discount_amount`
- `total`
- `status`

The backend calculates and assigns these.

Example response:

```json
{
  "data": {
    "id": "uuid",
    "quote_number": "QT-0007",
    "client_id": "uuid",
    "issue_date": "2026-09-12",
    "expiry_date": "2026-09-26",
    "currency": "KES",
    "subtotal": "35000.00",
    "tax_rate": "16.000",
    "tax_amount": "5600.00",
    "discount_type": "FIXED",
    "discount_value": "2000.00",
    "discount_amount": "2000.00",
    "total": "38600.00",
    "status": "DRAFT",
    "items": []
  }
}
```

---

## 6. Quote Status Actions

### Mark Sent

`POST /api/v1/quotes/{quote_id}/send`

### Accept

`POST /api/v1/quotes/{quote_id}/accept`

### Reject

`POST /api/v1/quotes/{quote_id}/reject`

State transitions must follow domain invariants.

---

## 7. Convert Quote to Invoice

`POST /api/v1/quotes/{quote_id}/convert`

Request:

```json
{
  "issue_date": "2026-09-12",
  "due_date": "2026-09-26"
}
```

Backend behavior:
1. Authenticate user.
2. Confirm Quote ownership.
3. Validate Quote state.
4. Create Invoice.
5. Copy items.
6. Preserve currency and relevant metadata.
7. Recalculate totals.
8. Link `source_quote_id`.
9. Mark Quote as `CONVERTED`.
10. Commit transaction.

Response:

`201 Created`

```json
{
  "data": {
    "id": "invoice_uuid",
    "invoice_number": "INV-0004",
    "source_quote_id": "quote_uuid",
    "status": "DRAFT",
    "total": "38600.00"
  }
}
```

Conflict example:

`409 Conflict`

```json
{
  "error": {
    "code": "QUOTE_ALREADY_CONVERTED",
    "message": "This quote has already been converted to an invoice.",
    "details": {}
  }
}
```

---

## 8. Invoices

Endpoints:

- `POST /api/v1/invoices`
- `GET /api/v1/invoices`
- `GET /api/v1/invoices/{invoice_id}`
- `PATCH /api/v1/invoices/{invoice_id}`
- `DELETE /api/v1/invoices/{invoice_id}`
- `POST /api/v1/invoices/{invoice_id}/send`
- `POST /api/v1/invoices/{invoice_id}/mark-paid`
- `POST /api/v1/invoices/{invoice_id}/cancel`
- `POST /api/v1/invoices/{invoice_id}/convert`
- `GET /api/v1/invoices/{invoice_id}/pdf`

### Direct Invoice Creation

Request shape mirrors Quote creation but uses:
- `issue_date`
- `due_date`
- Invoice-specific notes/terms

Computed totals remain backend-authoritative.

---

## 9. Convert Invoice to Receipt

`POST /api/v1/invoices/{invoice_id}/convert`

Request:

```json
{
  "issue_date": "2026-09-12"
}
```

Backend behavior:
1. Authenticate user.
2. Confirm Invoice ownership.
3. Validate Invoice state.
4. Create Receipt.
5. Copy InvoiceItems into ReceiptItems.
6. Preserve currency and relevant metadata.
7. Recalculate totals.
8. Link `source_invoice_id`.
9. Optionally update Invoice status according to agreed product rule.
10. Commit transaction.

Response:

```json
{
  "data": {
    "id": "receipt_uuid",
    "receipt_number": "RCT-0002",
    "source_invoice_id": "invoice_uuid",
    "total": "38600.00"
  }
}
```

---

## 10. Receipts

Endpoints:

- `POST /api/v1/receipts`
- `GET /api/v1/receipts`
- `GET /api/v1/receipts/{receipt_id}`
- `PATCH /api/v1/receipts/{receipt_id}`
- `DELETE /api/v1/receipts/{receipt_id}`
- `GET /api/v1/receipts/{receipt_id}/pdf`

Direct Receipt creation is supported because the user may need to issue a Receipt without first creating an Invoice.

Direct create request:

```json
{
  "client_id": "uuid",
  "issue_date": "2026-09-12",
  "currency": "KES",
  "tax_rate": "0",
  "discount_type": "NONE",
  "discount_value": "0",
  "notes": "Payment received.",
  "items": [
    {
      "description": "Website development",
      "quantity": "1.000",
      "unit_price": "30000.00"
    }
  ]
}
```

---

## 11. PDF Endpoints

- `GET /api/v1/quotes/{quote_id}/pdf`
- `GET /api/v1/invoices/{invoice_id}/pdf`
- `GET /api/v1/receipts/{receipt_id}/pdf`

Rules:
- User must own the document.
- Data comes from persisted backend state.
- Computed totals must not come from arbitrary query/body input.
- Response content type: `application/pdf`.

---

## 12. Dashboard

`GET /api/v1/dashboard/summary`

Example response:

```json
{
  "data": {
    "quotes": {
      "total": 18,
      "draft": 3,
      "sent": 8,
      "accepted": 4
    },
    "invoices": {
      "total": 12,
      "draft": 2,
      "sent": 3,
      "paid": 6,
      "overdue": 1
    },
    "receipts": {
      "total": 9
    },
    "recent_documents": []
  }
}
```

---

## 13. Filtering and Pagination

Suggested collection query parameters:

```text
?page=1
&page_size=20
?status=DRAFT
?client_id=<uuid>
?search=acme
?sort=-created_at
```

Applicable endpoints:
- `/clients`
- `/quotes`
- `/invoices`
- `/receipts`

---

## 14. Domain Error Codes

Suggested error codes:

### Authentication / Authorization
- `AUTHENTICATION_REQUIRED`
- `INVALID_CREDENTIALS`
- `FORBIDDEN_RESOURCE`

### Clients
- `CLIENT_NOT_FOUND`
- `CLIENT_OWNERSHIP_MISMATCH`

### Quotes
- `QUOTE_NOT_FOUND`
- `INVALID_QUOTE_STATUS`
- `QUOTE_ALREADY_CONVERTED`

### Invoices
- `INVOICE_NOT_FOUND`
- `INVALID_INVOICE_STATUS`
- `INVOICE_CANCELLED`

### Receipts
- `RECEIPT_NOT_FOUND`

### Validation
- `INVALID_DATE_RANGE`
- `INVALID_QUANTITY`
- `INVALID_UNIT_PRICE`
- `INVALID_TAX_RATE`
- `INVALID_DISCOUNT`
- `INVALID_CURRENCY`
- `EMPTY_LINE_ITEMS`

---

## 15. API Resource Map

```text
/api/v1

auth/
    register
    login
    refresh
    me

business-profile/

clients/
    {id}

quotes/
    {id}
    {id}/send
    {id}/accept
    {id}/reject
    {id}/convert
    {id}/pdf

invoices/
    {id}
    {id}/send
    {id}/mark-paid
    {id}/cancel
    {id}/convert
    {id}/pdf

receipts/
    {id}
    {id}/pdf

dashboard/
    summary
```

---

## 16. Out of Scope for MVP API

No endpoints for:
- payment processing
- M-Pesa STK Push
- payment callbacks
- payment reconciliation
- accounting ledgers
- inventory
- recurring invoices
- team/employee management

The MVP is a document-generation and document-conversion product, not a payment processor or accounting platform.

