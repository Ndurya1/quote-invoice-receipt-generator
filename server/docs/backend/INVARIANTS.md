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
- Line totals are computed with Decimal multiplication, then rounded once to two
  decimal places using ROUND_HALF_UP. Results outside NUMERIC(14,2) are rejected.
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
