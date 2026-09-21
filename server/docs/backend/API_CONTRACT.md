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

Retrieval requires an access bearer token and resolves ownership from the
authenticated user. Caller-supplied `user_id` is not used for selection.
Success returns HTTP 200 in the `data` envelope with `id`, `user_id`,
`business_name`, `logo_url`, `email`, `phone`, `address`, `tax_number`,
`default_currency`, `created_at`, and `updated_at`. Nullable fields remain null.
The response includes `Cache-Control: no-store`.

If the authenticated user has no profile, retrieval returns HTTP 404 with
`BUSINESS_PROFILE_NOT_FOUND`; it does not create one. Missing or invalid
authentication returns HTTP 401 `AUTHENTICATION_REQUIRED`.

PUT requires the same authentication and performs a full replacement of editable
fields, creating the profile if absent. Both creation and update return HTTP 200
with the stored profile in the same `data` envelope and `Cache-Control: no-store`.
`business_name` is required, trimmed, and must contain 1–160 characters. Omitted
optional fields become null; omitted `default_currency` becomes `KES`, including
on updates. Currency must contain exactly three uppercase ASCII letters.
Email must be valid when supplied; logo URLs must use HTTP or HTTPS. Phone and
tax number have maximum lengths of 30 and 100 characters respectively.
Explicit null is allowed for optional fields but not business name or currency.
Unknown fields, including `id`, `user_id`, `created_at`, and `updated_at`, are
rejected with HTTP 422 `VALIDATION_ERROR`, as are invalid editable values.
Ownership is assigned from authentication. Updates preserve the profile ID,
owner, and creation timestamp; `updated_at` is maintained by the database.

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

`POST /api/v1/clients` requires an access bearer token. The owner is assigned
from authentication. Success returns HTTP 201 with the stored client in `data`:
`id`, `user_id`, `name`, `email`, `phone`, `address`, `created_at`, and `updated_at`.
The response includes `Cache-Control: no-store`.

Name is required, trimmed, and must contain 1–160 characters. Email, phone, and
address are optional and nullable. Email must be valid and at most 255 characters;
phone is text of at most 30 characters. Duplicate client emails are allowed.
Unknown or server-managed fields (`id`, `user_id`, timestamps) are rejected with
422 `VALIDATION_ERROR`, as are invalid editable values. Invalid authentication
returns 401 `AUTHENTICATION_REQUIRED`. Creation does not require a business profile.

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

### List Clients

`GET /api/v1/clients` requires an access bearer token. It returns HTTP 200 with
`data` containing only the authenticated user's clients and `meta` containing
`page`, `page_size`, and that user's total client count. Query parameters default
to `page=1` and `page_size=20`; page must be 1–2147483647 and page size 1–100.
Invalid pagination returns 422 `VALIDATION_ERROR`. Results are ordered by
`created_at` ascending, then UUID ascending. Empty accounts and pages past the
end return an empty list with the requested pagination values and scoped total.
Successful responses include `Cache-Control: no-store`. Caller-supplied user IDs
do not change ownership scope. Search and configurable sorting are later tasks.

---

### Client Detail

`GET /api/v1/clients/{client_id}` requires an access bearer token and a UUID path
parameter. It returns HTTP 200 with the owned client's stored fields in `data`,
using the same shape as creation, and `Cache-Control: no-store`. Missing and
foreign-owned clients both return 404 `CLIENT_NOT_FOUND` with the message
`Client not found.` Invalid UUIDs return 422 `VALIDATION_ERROR`; invalid
authentication returns 401 `AUTHENTICATION_REQUIRED`. Caller-supplied owner IDs
cannot change the authenticated ownership scope.

---

### Update Client

`PATCH /api/v1/clients/{client_id}` requires an access bearer token and returns
HTTP 200 with the updated client in `data` and `Cache-Control: no-store`.
Only supplied `name`, `email`, `phone`, and `address` fields are changed.
Omitted fields are preserved; explicit null clears contact fields but is invalid
for name. Supplied values follow creation validation, including trimming name.
Unknown fields and server-managed IDs/ownership/timestamps return 422
`VALIDATION_ERROR`. An empty object returns the owned client without writing or
changing its timestamp. Missing and foreign-owned clients both return 404
`CLIENT_NOT_FOUND`; malformed UUIDs return 422 and invalid authentication 401.

---

### Delete Client

`DELETE /api/v1/clients/{client_id}` requires an access bearer token. An owned
client with no document references is hard-deleted and returns HTTP 204 with no
body. If any Quote, Invoice, or Receipt references the client, regardless of
document status, deletion returns 409 `CLIENT_IN_USE`. The client and documents
remain unchanged. Existing `ON DELETE RESTRICT` foreign keys enforce this policy;
client deletion never cascades to document history.

Missing and foreign-owned clients return 404 `CLIENT_NOT_FOUND`, including repeat
deletion of an already deleted client. Invalid UUIDs return 422 and invalid
authentication returns 401.

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

### Delete Quote (Task 8.6)

`DELETE /api/v1/quotes/{quote_id}` requires access bearer authentication.
Only DRAFT quotes without an invoice reference may be deleted. SENT, ACCEPTED,
REJECTED, EXPIRED and CONVERTED return 409 `INVALID_QUOTE_STATUS`; invoice-linked
drafts return the same code. The server locks the quote before checking policy.
Successful deletion atomically removes the quote and its own items, returning
204 with no body. Missing/foreign/already-deleted quotes return 404
`QUOTE_NOT_FOUND`; malformed UUIDs return 422. Numbers are never reused.
Other documents, clients, and number counters are preserved.

### Update Quote (Task 8.5)

`PATCH /api/v1/quotes/{quote_id}` requires access bearer authentication. Only
unlinked DRAFT quotes are editable. All other statuses (SENT, ACCEPTED, REJECTED,
EXPIRED, CONVERTED), and DRAFT quotes referenced by invoices, return 409
`INVALID_QUOTE_STATUS`. Missing/foreign quotes return 404 `QUOTE_NOT_FOUND`.

Writable fields: client_id, issue_date, expiry_date, currency, tax_rate,
discount_type, discount_value, notes, terms, items. Omitted fields retain saved
values. Null clears only expiry_date, notes and terms. Empty PATCH is a no-op
after ownership/state checks. Supplied items replace the entire collection with
new item UUIDs; omitted items keep their UUIDs. Supplied items use creation's
input shape and must be nonempty. Item IDs, owner, number, status, timestamps,
unknown fields and computed amounts are rejected with 422.

The merged document is validated (including dates and discounts), the client
must belong to the caller (404 CLIENT_NOT_FOUND otherwise), and totals are
recalculated. Quote and item changes are one transaction. Currency changes
relabel the amounts; there is no FX conversion. Success returns 200 with the
persisted Quote and position/UUID-ordered items inside `data`, decimal strings,
and `Cache-Control: no-store`. Validation errors return 422. No source or
destination documents are modified.

### Read Quote (Task 8.3)

`GET /api/v1/quotes/{quote_id}` requires access bearer authentication and returns
200 with persisted Quote fields and items inside `data`. Items are ordered by
position then UUID ascending. Amounts remain decimal strings; no recalculation
occurs on reads. Missing and foreign quotes return 404 `QUOTE_NOT_FOUND` with
identical bodies. Malformed UUIDs return 422. Responses use `Cache-Control: no-store`.

### List Quotes (Task 8.2)

`GET /api/v1/quotes` requires access bearer authentication. Returns 200 with
`data` containing persisted Quote fields and items, and `meta` containing
`page`, `page_size`, and the total owned Quote count. Defaults: page 1, page_size
20; page must be 1..2147483647 and page_size 1..100 (invalid values return 422).
Results are ordered by created_at descending, then UUID descending. Items are
ordered by position ascending, then UUID ascending. Empty/out-of-range pages
return an empty array. Responses use `Cache-Control: no-store` and decimal
strings. Only the authenticated owner's quotes are counted or returned.
Filtering/search/sort parameters are deferred to Task 18.3.

### Create Quote

`POST /api/v1/quotes` requires an access bearer token. Success returns HTTP 201
with the persisted Quote and its items inside `data`, including owner UUID,
notes, terms, and timestamps in addition to the fields in the example below.
Each item includes its generated UUID, quote UUID, description, quantity, unit
price, calculated line total, and position. Items retain request order.
Monetary amounts are decimal strings. Responses use `Cache-Control: no-store`.
Client ownership is resolved from authentication. Missing/foreign clients return
404 `CLIENT_NOT_FOUND`; invalid input or server-managed fields return 422;
invalid authentication returns 401. Failed creation rolls back the Quote, items,
and number allocation together.

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
- `CLIENT_IN_USE`
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
