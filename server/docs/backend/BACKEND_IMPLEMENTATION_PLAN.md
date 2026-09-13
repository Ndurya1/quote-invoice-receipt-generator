# Backend Implementation Plan — Plug-and-Send Billing

## Purpose

This plan converts the approved MVP product/system documents into small backend implementation tasks that can be implemented, reviewed, tested, and committed independently.

For every task: implement only the stated scope, add/update tests, run the relevant test subset, inspect the diff, commit, then move on.

---

# 0. Source of Truth and Scope Decisions

## 0.1 Implementation-facing source precedence

Use the implementation documents in this order:

1. `INVARIANTS.md` — rules that must always remain true.
2. `DB_MODELS.md` — persisted models, constraints, indexes, relationships.
3. `API_CONTRACT.md` — routes, payloads, response envelopes, error/status semantics.
4. `product.md` — product intent and broader roadmap context.

Where `product.md` is broader than the implementation documents, do not silently add backend scope.

### Current MVP decisions

- No `Payment` model.
- No payment gateway, M-Pesa callback, reconciliation, or settlement logic.
- Invoice `PAID` is a document/business status; no payment transaction is created.
- Direct Quote creation is supported.
- Direct Invoice creation is supported.
- Direct Receipt creation is supported.
- Quote → Invoice conversion is supported.
- Invoice → Receipt conversion is supported.
- A Quote may produce at most one Invoice.
- An Invoice may be referenced by multiple Receipts because `Receipt.source_invoice_id` is not unique.
- Business/client snapshots are not in the current schema.
- Saved product/service catalogue is not in the current schema/API.
- Rich branding beyond `logo_url` is not in the current schema/API.
- Backend calculations are authoritative.
- All user-owned resources are tenant-isolated.

## 0.2 Decision gate — Receipt deletion semantics

The API contract exposes `DELETE /api/v1/receipts/{receipt_id}`. The invariants say Receipts should preferably be archived/voided rather than deleted, but the schema has no archival/void field.

Before implementing Receipt deletion, choose explicitly:

- **A:** hard-delete according to a documented MVP rule;
- **B:** add archival/void fields and update schema/API first; or
- **C:** remove/disable Receipt delete for MVP.

Do not improvise this inside a controller.

## 0.3 Framework note

The source documents specify PostgreSQL-style relational persistence, JWT auth, JSON APIs, PDF responses, and `/api/v1`, but not a framework. Terms below are framework-neutral. If using Django + DRF, map model/request schema/service/handler/query-layer to models/serializers/services/views/selectors/permissions.

---

# 1. Project Foundation

## Task 1.1 — Initialize backend project structure

**Goal:** create the backend skeleton without domain features.

**Implementation:**
- Create modules/apps for accounts, business, clients, quotes, invoices, receipts, common utilities.
- Mount `/api/v1`.
- Add environment-driven settings and `.env.example`.
- Add test configuration.
- Keep secrets out of source control.

**Acceptance:** app starts; test runner works; API namespace resolves.

**Commit:** `chore(backend): initialize project structure`

## Task 1.2 — Configure PostgreSQL

**Implementation:** configure DB name/user/password/host/port, migrations, test DB, UTC timestamps where applicable.

**Acceptance:** local connection and migrations succeed; tests use PostgreSQL-compatible behavior.

**Commit:** `chore(database): configure PostgreSQL`

## Task 1.3 — Add standard API response envelopes

Implement helpers for:

```json
{"data": {}}
```

```json
{"data": [], "meta": {"page": 1, "page_size": 20, "total": 0}}
```

```json
{"error": {"code": "ERROR_CODE", "message": "...", "details": {}}}
```

**Tests:** single-resource, collection, error envelope.

**Commit:** `feat(api): add standard response envelopes`

## Task 1.4 — Add global exception/error mapping

Map expected failures to 400/401/403/404/409/422/500 and stable domain error codes. Do not expose stack traces.

**Commit:** `feat(api): add domain error mapping`

---

# 2. Authentication and User Model

## Task 2.1 — Implement UUID User model

Fields: UUID PK, name, unique email, nullable phone, framework-managed password hash, created_at, updated_at.

**Tests:** creation, duplicate email, password hashing, UUID PK.

**Commit:** `feat(auth): add user model`

## Task 2.2 — Add registration validation

Validate name/email/phone/password. Normalize email consistently. Never serialize password fields.

**Commit:** `feat(auth): add registration validation`

## Task 2.3 — Implement registration endpoint

`POST /api/v1/auth/register`

Return id/name/email/phone in `data` envelope; 201 on success.

**Tests:** success, duplicate email, invalid email, missing fields.

**Commit:** `feat(auth): add registration endpoint`

## Task 2.4 — Implement JWT login

`POST /api/v1/auth/login`

Return access token, refresh token, `token_type: bearer`. Invalid credentials must not reveal which credential failed.

**Commit:** `feat(auth): add JWT login endpoint`

## Task 2.5 — Implement JWT refresh

`POST /api/v1/auth/refresh`

**Tests:** valid refresh; invalid/expired token.

**Commit:** `feat(auth): add JWT refresh endpoint`

## Task 2.6 — Implement current-user endpoint

`GET /api/v1/auth/me`

Authenticated only; no sensitive fields.

**Commit:** `feat(auth): add current user endpoint`

---

# 3. Business Profile

## Task 3.1 — Implement BusinessProfile model

Fields: UUID PK, unique user FK, business_name, logo_url, email, phone, address, tax_number, default_currency default `KES`, timestamps.

**Rules:** max one profile/user; default currency can be overridden by documents.

**Tests:** creation, second profile rejected, default currency.

**Commit:** `feat(business): add business profile model`

## Task 3.2 — Add reusable currency-code validator

Require uppercase 3-character ISO-style code. No FX conversion.

**Commit:** `feat(common): add currency code validation`

## Task 3.3 — Implement profile read endpoint

`GET /api/v1/business-profile`

Always resolve from authenticated user; never accept caller `user_id`.

**Commit:** `feat(business): add business profile retrieval`

## Task 3.4 — Implement profile upsert/update

`PUT /api/v1/business-profile`

Assign owner server-side; validate currency; deterministic create/update semantics.

**Tests:** create, update, invalid currency, ownership cannot be overridden.

**Commit:** `feat(business): add business profile update endpoint`

---

# 4. Clients

## Task 4.1 — Implement Client model

Fields: UUID PK, user FK, required name, nullable email/phone/address, timestamps.

Indexes: `user_id`, `(user_id, name)`.

**Tests:** creation, required name, duplicate emails allowed.

**Commit:** `feat(clients): add client model`

## Task 4.2 — Add user-scoped Client query layer

Create reusable list/get operations that always scope by authenticated user before public UUID.

**Tests:** own client found; foreign client inaccessible.

**Commit:** `feat(clients): add user scoped client queries`

## Task 4.3 — Add Client create endpoint

`POST /api/v1/clients`

Owner assigned from auth context. Caller cannot choose ownership.

**Commit:** `feat(clients): add client creation endpoint`

## Task 4.4 — Add Client list endpoint

`GET /api/v1/clients`

User-scoped, paginated collection response.

**Commit:** `feat(clients): add client list endpoint`

## Task 4.5 — Add Client detail endpoint

`GET /api/v1/clients/{client_id}`

Test own/not-found/foreign cases.

**Commit:** `feat(clients): add client detail endpoint`

## Task 4.6 — Add Client patch endpoint

`PATCH /api/v1/clients/{client_id}`

Owner immutable; name remains valid.

**Commit:** `feat(clients): add client update endpoint`

## Task 4.7 — Add safe Client delete endpoint

`DELETE /api/v1/clients/{client_id}`

The docs do not define the Client FK deletion policy explicitly. Choose/document a policy that cannot cascade-delete document history; `PROTECT/RESTRICT` is the conservative choice.

**Commit:** `feat(clients): add safe client deletion`

---

# 5. Shared Financial Domain

## Task 5.1 — Define DiscountType enum

Values: `NONE`, `FIXED`, `PERCENTAGE`.

**Commit:** `feat(documents): add discount type enum`

## Task 5.2 — Implement shared line-item validation

Validate description, `quantity > 0`, `unit_price >= 0`, fixed-precision decimal values, optional position.

**Tests:** negative/zero quantities, negative unit price, decimal inputs.

**Commit:** `feat(calculations): add line item validation`

## Task 5.3 — Implement line-total calculation

Formula: `line_total = quantity × unit_price`.

Caller-supplied line totals are never authoritative.

**Commit:** `feat(calculations): add line total calculation`

## Task 5.4 — Implement subtotal calculation

Formula: `subtotal = SUM(line_total)`.

**Commit:** `feat(calculations): add subtotal calculation`

## Task 5.5 — Implement tax calculation

Formula: `tax_amount = subtotal × tax_rate / 100`.

Rules: tax optional; percentage-based; rate >= 0; default 0.

**Commit:** `feat(calculations): add tax calculation`

## Task 5.6 — Implement discount calculation

Rules:
- NONE => value/amount 0.
- PERCENTAGE => 0..100; amount = subtotal × value / 100.
- FIXED => amount = value.
- Discount must never make final total negative.

**Commit:** `feat(calculations): add discount calculation`

## Task 5.7 — Implement authoritative totals service

Formula:
- line_total = quantity × unit_price
- subtotal = Σ line_total
- tax_amount = subtotal × tax_rate / 100
- discount_amount = derived by discount type
- total = subtotal + tax_amount - discount_amount

Use decimal arithmetic only.

**Acceptance:** same service reusable by Quote, Invoice, Receipt and conversions.

**Commit:** `feat(calculations): add authoritative document totals service`

## Task 5.8 — Add computed-field tampering tests

Prove request values cannot override line_total/subtotal/tax_amount/discount_amount/total.

**Commit:** `test(calculations): reject client controlled totals`

---

# 6. Document Numbering

## Task 6.1 — Implement per-user Quote numbering

Format `QT-0001`; unique per user; immutable; concurrency-safe. Do not use unsafe `count() + 1` without collision protection.

**Commit:** `feat(numbering): add quote number generation`

## Task 6.2 — Implement per-user Invoice numbering

Format `INV-0001`; same concurrency/uniqueness guarantees.

**Commit:** `feat(numbering): add invoice number generation`

## Task 6.3 — Implement per-user Receipt numbering

Format `RCT-0001`; same guarantees.

**Commit:** `feat(numbering): add receipt number generation`

---

# 7. Quote Persistence and Creation

## Task 7.1 — Implement Quote model

Fields exactly from DB model: user/client FKs, quote_number, issue/expiry dates, currency, subtotal, tax_rate/tax_amount, discount fields, total, status, notes, terms, timestamps.

Statuses: DRAFT, SENT, ACCEPTED, REJECTED, EXPIRED, CONVERTED.

Constraints: unique `(user_id, quote_number)`, nonnegative values, expiry >= issue date. Add documented indexes.

**Commit:** `feat(quotes): add quote model`

## Task 7.2 — Implement QuoteItem model

Fields: UUID, quote FK with cascade from legitimate parent deletion, description, quantity NUMERIC(12,3), unit_price NUMERIC(14,2), line_total NUMERIC(14,2), position.

Constraints: quantity > 0; unit_price/line_total >= 0.

**Commit:** `feat(quotes): add quote item model`

## Task 7.3 — Add Quote create request validation

Validate: owned client, at least one item, dates, currency, tax, discount, item rules.

Server-managed/read-only: user_id, quote_number, line_total, subtotal, tax_amount, discount_amount, total, status.

**Commit:** `feat(quotes): add quote request validation`

## Task 7.4 — Implement atomic Quote creation service

Transaction:
1. validate owned client;
2. validate request;
3. generate number;
4. calculate items/totals;
5. create Quote;
6. create QuoteItems;
7. commit.

Any item failure must roll back parent Quote.

**Commit:** `feat(quotes): add quote creation service`

## Task 7.5 — Expose Quote create endpoint

`POST /api/v1/quotes`

Return 201, DRAFT status, generated number, backend totals.

**Commit:** `feat(quotes): add quote creation endpoint`

---

# 8. Quote Read/Update/Delete

## Task 8.1 — Add user-scoped Quote queries

Get/list own Quotes and efficiently load items/client.

**Commit:** `feat(quotes): add user scoped quote queries`

## Task 8.2 — Add Quote list endpoint

`GET /api/v1/quotes`

User-scoped; paginated.

**Commit:** `feat(quotes): add quote list endpoint`

## Task 8.3 — Add Quote detail endpoint

`GET /api/v1/quotes/{quote_id}` including persisted items and computed fields.

**Commit:** `feat(quotes): add quote detail endpoint`

## Task 8.4 — Implement Quote edit service

Rules: number/owner immutable; status not freely PATCHed; financial edits recalc totals; replacement client must be owned; destination changes never mutate source history.

**Decision note:** docs do not provide a full editability matrix for all Quote statuses. Define it explicitly before allowing edits beyond DRAFT.

**Commit:** `feat(quotes): add quote update service`

## Task 8.5 — Expose Quote PATCH

`PATCH /api/v1/quotes/{quote_id}`

**Tests:** allowed fields, immutable fields, foreign quote, recalculation.

**Commit:** `feat(quotes): add quote update endpoint`

## Task 8.6 — Enforce Quote deletion rules

`DELETE /api/v1/quotes/{quote_id}`

At minimum: DRAFT may delete; CONVERTED may not. Define SENT/ACCEPTED/REJECTED/EXPIRED behavior explicitly before coding.

**Commit:** `feat(quotes): enforce quote deletion rules`

---

# 9. Quote Lifecycle Actions

## Task 9.1 — Implement Quote transition service

Allowed transitions:
- DRAFT → SENT
- DRAFT → ACCEPTED
- SENT → ACCEPTED
- SENT → REJECTED
- SENT → EXPIRED
- ACCEPTED → CONVERTED

Invalid transitions produce domain conflict/error rather than direct status assignment.

**Commit:** `feat(quotes): add quote status transition service`

## Task 9.2 — Add mark-sent action

`POST /api/v1/quotes/{quote_id}/send`

**Commit:** `feat(quotes): add mark sent action`

## Task 9.3 — Add accept action

`POST /api/v1/quotes/{quote_id}/accept`

**Commit:** `feat(quotes): add accept quote action`

## Task 9.4 — Add reject action

`POST /api/v1/quotes/{quote_id}/reject`

**Commit:** `feat(quotes): add reject quote action`

## Task 9.5 — Add lifecycle transition tests

Cover every valid transition plus representative invalid transitions.

**Commit:** `test(quotes): cover quote status transitions`

---

# 10. Invoice Persistence and Direct Creation

## Task 10.1 — Implement Invoice model

Use schema exactly, including nullable unique `source_quote_id`, invoice_number, dates, status, money fields, notes/terms, timestamps.

Statuses: DRAFT, SENT, PAID, OVERDUE, CANCELLED.

Constraints/indexes exactly as documented.

**Commit:** `feat(invoices): add invoice model`

## Task 10.2 — Implement InvoiceItem model

Mirror documented schema and constraints.

**Commit:** `feat(invoices): add invoice item model`

## Task 10.3 — Add direct Invoice request validation

Validate owned client, non-empty items, due_date >= issue_date, shared finance rules. source_quote_id and computed fields are server-managed.

**Commit:** `feat(invoices): add invoice request validation`

## Task 10.4 — Implement atomic direct Invoice service

Generate number, calculate values, persist Invoice + items in one transaction; source_quote_id null.

**Commit:** `feat(invoices): add direct invoice creation service`

## Task 10.5 — Expose direct Invoice endpoint

`POST /api/v1/invoices`

**Commit:** `feat(invoices): add invoice creation endpoint`

---

# 11. Invoice Read/Update/Delete

## Task 11.1 — Add user-scoped Invoice queries

**Commit:** `feat(invoices): add user scoped invoice queries`

## Task 11.2 — Add Invoice list endpoint

`GET /api/v1/invoices`

**Commit:** `feat(invoices): add invoice list endpoint`

## Task 11.3 — Add Invoice detail endpoint

`GET /api/v1/invoices/{invoice_id}`

**Commit:** `feat(invoices): add invoice detail endpoint`

## Task 11.4 — Implement Invoice edit service

Owner, number, source_quote_id immutable; status not arbitrary PATCH; financial changes recalc totals; source Quote never mutated.

**Decision note:** docs do not define complete mutability rules beyond lifecycle constraints. Define before allowing edits outside DRAFT.

**Commit:** `feat(invoices): add invoice update service`

## Task 11.5 — Expose Invoice PATCH

`PATCH /api/v1/invoices/{invoice_id}`

**Commit:** `feat(invoices): add invoice update endpoint`

## Task 11.6 — Enforce Invoice deletion rules

`DELETE /api/v1/invoices/{invoice_id}`

DRAFT may hard-delete. If any Receipt references Invoice, hard delete must be blocked. Define other statuses explicitly.

**Commit:** `feat(invoices): enforce invoice deletion rules`

---

# 12. Invoice Lifecycle Actions

## Task 12.1 — Define and implement Invoice transition service

Contract exposes send, mark-paid, cancel. Sources do not provide a full transition matrix like Quotes.

Before coding, explicitly define allowed transitions for DRAFT/SENT/PAID/OVERDUE/CANCELLED, including how OVERDUE is reached. Then centralize enforcement in one service.

**Commit:** `feat(invoices): add invoice status transition service`

## Task 12.2 — Add mark-sent action

`POST /api/v1/invoices/{invoice_id}/send`

**Commit:** `feat(invoices): add mark sent action`

## Task 12.3 — Add mark-paid action

`POST /api/v1/invoices/{invoice_id}/mark-paid`

No Payment record is created.

**Commit:** `feat(invoices): add mark paid action`

## Task 12.4 — Add cancel action

`POST /api/v1/invoices/{invoice_id}/cancel`

**Commit:** `feat(invoices): add cancel invoice action`

## Task 12.5 — Add lifecycle tests

**Commit:** `test(invoices): cover invoice status actions`

---

# 13. Quote → Invoice Conversion

## Task 13.1 — Implement conversion eligibility validator

Rules: owned Quote; must be ACCEPTED; converted/rejected/expired not eligible; one Invoice max; use domain error codes.

**Commit:** `feat(conversion): validate quote conversion eligibility`

## Task 13.2 — Implement atomic conversion service

Transaction:
1. load/lock user-scoped Quote;
2. validate state;
3. validate issue/due dates;
4. generate Invoice number;
5. create Invoice with same owner/client/currency and source_quote_id;
6. copy relevant notes/terms;
7. create new InvoiceItem rows from QuoteItems;
8. recalculate all destination totals;
9. set Quote CONVERTED;
10. commit.

Any failure rolls back Invoice/items/status change.

**Commit:** `feat(conversion): implement quote to invoice transaction`

## Task 13.3 — Expose conversion endpoint

`POST /api/v1/quotes/{quote_id}/convert`

Input: issue_date, due_date. Return 201 with new Invoice summary.

**Commit:** `feat(conversion): expose quote to invoice endpoint`

## Task 13.4 — Add conversion integration tests

Cover success, copied metadata, new rows, recalculated totals, independent number, lineage, repeated conversion, invalid states, foreign ownership, rollback.

**Commit:** `test(conversion): cover quote to invoice workflow`

---

# 14. Receipt Persistence and Direct Creation

## Task 14.1 — Implement Receipt model

Use schema exactly; `source_invoice_id` nullable and non-unique. Do not add payment-specific fields from broader product requirements unless schema/API are revised.

**Commit:** `feat(receipts): add receipt model`

## Task 14.2 — Implement ReceiptItem model

**Commit:** `feat(receipts): add receipt item model`

## Task 14.3 — Add direct Receipt request validation

Validate owned client, issue_date, currency, tax/discount, non-empty items. source_invoice_id/computed fields are server-managed.

**Commit:** `feat(receipts): add receipt request validation`

## Task 14.4 — Implement atomic direct Receipt service

Generate number, source_invoice_id null, calculate totals, persist Receipt + items transactionally.

**Commit:** `feat(receipts): add direct receipt creation service`

## Task 14.5 — Expose direct Receipt endpoint

`POST /api/v1/receipts`

**Commit:** `feat(receipts): add receipt creation endpoint`

---

# 15. Receipt Read/Update/Delete

## Task 15.1 — Add user-scoped Receipt queries

**Commit:** `feat(receipts): add user scoped receipt queries`

## Task 15.2 — Add Receipt list endpoint

`GET /api/v1/receipts`

**Commit:** `feat(receipts): add receipt list endpoint`

## Task 15.3 — Add Receipt detail endpoint

`GET /api/v1/receipts/{receipt_id}`

**Commit:** `feat(receipts): add receipt detail endpoint`

## Task 15.4 — Implement Receipt edit service

Number/owner/source_invoice_id immutable; financial edits recalc; source Invoice never mutated. Define issued-receipt editability before broad PATCH behavior.

**Commit:** `feat(receipts): add receipt update service`

## Task 15.5 — Expose Receipt PATCH

`PATCH /api/v1/receipts/{receipt_id}`

**Commit:** `feat(receipts): add receipt update endpoint`

## Task 15.6 — Implement agreed Receipt deletion/archival rule

Depends on Task 0.2 decision.

**Commit:** choose matching commit after decision.

---

# 16. Invoice → Receipt Conversion

## Task 16.1 — Implement conversion eligibility validator

Rules: user owns Invoice; CANCELLED cannot convert; other restrictions follow agreed Invoice transition policy. Multiple Receipts per Invoice are structurally permitted by current schema.

**Commit:** `feat(conversion): validate invoice conversion eligibility`

## Task 16.2 — Implement atomic Invoice → Receipt service

Transaction:
1. load/lock user-scoped Invoice;
2. validate state;
3. generate Receipt number;
4. create Receipt with same owner/client/currency/source_invoice_id;
5. copy relevant notes;
6. create new ReceiptItem rows;
7. recalc totals;
8. optionally mark Invoice PAID according to explicit product rule;
9. commit.

Destination edits must never mutate source Invoice.

**Commit:** `feat(conversion): implement invoice to receipt transaction`

## Task 16.3 — Expose conversion endpoint

`POST /api/v1/invoices/{invoice_id}/convert`

Input: issue_date.

**Commit:** `feat(conversion): expose invoice to receipt endpoint`

## Task 16.4 — Add conversion integration tests

Cover valid conversion, cancelled/foreign rejection, preserved client/currency, independent number, new rows, recalculation, rollback, multiple Receipt behavior.

**Commit:** `test(conversion): cover invoice to receipt workflow`

---

# 17. Historical Integrity

## Task 17.1 — Quote remains unchanged after Invoice edits

Create Quote → convert → edit Invoice → assert Quote and QuoteItems unchanged.

**Commit:** `test(history): preserve quote after invoice edits`

## Task 17.2 — Invoice remains unchanged after Receipt edits

**Commit:** `test(history): preserve invoice after receipt edits`

## Task 17.3 — Verify full lineage

Quote → Invoice → Receipt; assert source IDs, independent numbers, independent item rows.

**Commit:** `test(history): cover document conversion lineage`

---

# 18. Filtering, Search, Sorting, Pagination

## Task 18.1 — Implement shared pagination

Support `page`, `page_size`, documented metadata, maximum page size.

**Commit:** `feat(api): add collection pagination`

## Task 18.2 — Add Client search/sort

Whitelist sortable/searchable fields.

**Commit:** `feat(clients): add client search and sorting`

## Task 18.3 — Add Quote filters

Support status, client_id, search, sort, pagination after tenant scoping.

**Commit:** `feat(quotes): add quote filters and sorting`

## Task 18.4 — Add Invoice filters

**Commit:** `feat(invoices): add invoice filters and sorting`

## Task 18.5 — Add Receipt filters

**Commit:** `feat(receipts): add receipt filters and sorting`

---

# 19. Dashboard

## Task 19.1 — Implement summary aggregation service

Return user-scoped counts:
- Quotes total/draft/sent/accepted
- Invoices total/draft/sent/paid/overdue
- Receipts total
- recent_documents

Do not add payment aggregates; current backend has no Payment model.

**Commit:** `feat(dashboard): add summary aggregation service`

## Task 19.2 — Expose dashboard endpoint

`GET /api/v1/dashboard/summary`

**Tests:** correct counts, empty account, recent ordering, tenant isolation.

**Commit:** `feat(dashboard): add summary endpoint`

---

# 20. PDF Generation

## Task 20.1 — Create persisted document render context

Build rendering DTO from persisted business, client, document, items, totals, notes/terms. Never accept arbitrary totals for PDF generation.

**Commit:** `feat(pdf): add document rendering context`

## Task 20.2 — Implement Quote PDF renderer

**Commit:** `feat(pdf): add quote PDF rendering`

## Task 20.3 — Expose Quote PDF

`GET /api/v1/quotes/{quote_id}/pdf`, `application/pdf`, owner-only.

**Commit:** `feat(pdf): add quote PDF endpoint`

## Task 20.4 — Implement Invoice PDF renderer

**Commit:** `feat(pdf): add invoice PDF rendering`

## Task 20.5 — Expose Invoice PDF

`GET /api/v1/invoices/{invoice_id}/pdf`

**Commit:** `feat(pdf): add invoice PDF endpoint`

## Task 20.6 — Implement Receipt PDF renderer

**Commit:** `feat(pdf): add receipt PDF rendering`

## Task 20.7 — Expose Receipt PDF

`GET /api/v1/receipts/{receipt_id}/pdf`

**Commit:** `feat(pdf): add receipt PDF endpoint`

## Task 20.8 — Add PDF integrity/authorization tests

Owner succeeds; foreign user fails; correct document number; request cannot override totals; content type PDF.

**Commit:** `test(pdf): cover PDF authorization and integrity`

---

# 21. Tenant Isolation Security Pass

## Task 21.1 — Client cross-tenant tests

GET/PATCH/DELETE another user's Client must fail.

**Commit:** `test(security): cover client tenant isolation`

## Task 21.2 — Quote cross-tenant tests

Read/update/delete/status/convert/PDF another user's Quote must fail.

**Commit:** `test(security): cover quote tenant isolation`

## Task 21.3 — Invoice cross-tenant tests

**Commit:** `test(security): cover invoice tenant isolation`

## Task 21.4 — Receipt cross-tenant tests

**Commit:** `test(security): cover receipt tenant isolation`

## Task 21.5 — Reject foreign Client references

User A cannot create Quote/Invoice/Receipt using User B's client UUID.

**Commit:** `test(security): reject foreign client document references`

---

# 22. Database Constraint Verification

## Task 22.1 — Verify per-user document number uniqueness

Same number for same user fails; same number across users allowed.

**Commit:** `test(database): cover document number uniqueness`

## Task 22.2 — Verify date constraints

Quote expiry before issue date and Invoice due before issue date rejected.

**Commit:** `test(database): cover document date constraints`

## Task 22.3 — Verify monetary constraints

Persisted negative impossible states rejected.

**Commit:** `test(database): cover monetary constraints`

## Task 22.4 — Verify source constraints

One Invoice per Quote; multiple Receipts per Invoice under current schema.

**Commit:** `test(database): cover document source constraints`

---

# 23. API Contract Verification

## Task 23.1 — Audit complete route map

Verify every documented `/api/v1` auth, business-profile, clients, quotes, invoices, receipts, dashboard route and method.

**Commit:** `test(api): verify MVP route contract`

## Task 23.2 — Audit server-managed fields

Ensure clients cannot authoritatively set owner IDs, document numbers, computed totals, source IDs on direct creation, status, timestamps.

**Commit:** `test(api): protect server managed fields`

## Task 23.3 — Audit domain error codes

Cover documented auth/client/quote/invoice/receipt/validation codes such as `AUTHENTICATION_REQUIRED`, `INVALID_CREDENTIALS`, `FORBIDDEN_RESOURCE`, `CLIENT_NOT_FOUND`, `QUOTE_ALREADY_CONVERTED`, `INVOICE_CANCELLED`, `EMPTY_LINE_ITEMS`, etc.

**Commit:** `test(api): cover documented domain errors`

---

# 24. Query Performance

## Task 24.1 — Optimize Quote queries

Avoid N+1 for client/items.

**Commit:** `perf(quotes): optimize quote queries`

## Task 24.2 — Optimize Invoice queries

**Commit:** `perf(invoices): optimize invoice queries`

## Task 24.3 — Optimize Receipt queries

**Commit:** `perf(receipts): optimize receipt queries`

## Task 24.4 — Verify documented indexes

Check user, status, client, source-document, created_at, and Client `(user_id, name)` indexes.

**Commit:** `perf(database): verify MVP indexes`

---

# 25. Production Configuration

## Task 25.1 — Configure CORS

Whitelist real frontend origins; keep dev/prod separate.

**Commit:** `chore(security): configure CORS`

## Task 25.2 — Harden production settings

Debug off, allowed hosts, HTTPS/proxy handling, secure cookies as relevant, environment secrets, JWT settings.

**Commit:** `chore(security): harden production settings`

## Task 25.3 — Configure logging

Log operational failures without passwords/tokens/secrets.

**Commit:** `chore(logging): configure backend logging`

## Task 25.4 — Add deployment configuration

Install/build command, migration command, start command, env vars, PostgreSQL connection.

**Commit:** `chore(deploy): add backend deployment config`

---

# 26. End-to-End Verification

## Task 26.1 — First-user Quote flow

Register → Login → Business profile → Client → Quote → retrieve → PDF.

**Commit:** `test(e2e): cover first user quote workflow`

## Task 26.2 — Full Quote → Invoice → Receipt flow

Create Quote → send → accept → convert to Invoice → send → convert to Receipt → retrieve/download all.

Verify independent numbers, lineage, preserved client/currency, copied independent items, backend totals, ownership.

**Commit:** `test(e2e): cover full document lifecycle`

## Task 26.3 — Direct Invoice → Receipt flow

Direct Invoice with null source_quote_id → convert → Receipt references Invoice.

**Commit:** `test(e2e): cover direct invoice workflow`

## Task 26.4 — Direct Receipt flow

Create direct Receipt with null source_invoice_id → retrieve → PDF.

**Commit:** `test(e2e): cover direct receipt workflow`

## Task 26.5 — Adversarial financial requests

Try forged totals, negative values, invalid percentage discounts, invalid dates, foreign client IDs.

**Commit:** `test(e2e): cover financial tampering cases`

---

# 27. MVP Backend Completion Gate

- [ ] JWT register/login/refresh/me works.
- [ ] One BusinessProfile per User enforced.
- [ ] Client CRUD tenant-isolated.
- [ ] Direct Quote creation works.
- [ ] Direct Invoice creation works.
- [ ] Direct Receipt creation works.
- [ ] Backend recalculates all financial totals.
- [ ] Money uses fixed-precision decimals.
- [ ] Numbers generated server-side and unique per user/type.
- [ ] Quote lifecycle transition rules enforced.
- [ ] Invoice lifecycle uses an explicit tested transition policy.
- [ ] Quote → Invoice conversion atomic.
- [ ] Invoice → Receipt conversion atomic.
- [ ] Source documents remain unchanged after destination edits.
- [ ] Direct/converted documents use the same calculations.
- [ ] Cross-user read/write/delete/convert/download fails.
- [ ] Collections paginate and filter safely.
- [ ] Dashboard matches contract.
- [ ] PDFs use persisted backend state.
- [ ] Response/error envelopes match contract.
- [ ] Domain error codes stable.
- [ ] DB constraints/indexes present.
- [ ] Deployment works with PostgreSQL.
- [ ] E2E lifecycle tests pass.

---

# 28. Deferred / Not in Current Backend MVP

Do not implement unless schema/API are deliberately revised:

- Payment model or partial-payment ledger
- payment method/reference storage tied to payment records
- amount-paid/balance-due accounting
- M-Pesa STK Push/callbacks/reconciliation
- saved services/products catalogue
- recurring invoices
- inventory/accounting ledger/tax filing
- team/multi-user businesses
- public share links/customer portal
- native email/WhatsApp sending
- document/business snapshots
- multi-branch support
- automatic FX conversion
- richer branding fields not represented in BusinessProfile

---

# 29. Recommended Commit Sequence

```text
Foundation
→ PostgreSQL
→ API envelopes/errors
→ User + JWT
→ BusinessProfile
→ Client CRUD
→ Shared calculation engine
→ Numbering
→ Quote models + CRUD + lifecycle
→ Invoice models + direct flow + lifecycle
→ Quote→Invoice conversion
→ Receipt models + direct flow
→ Invoice→Receipt conversion
→ Historical integrity tests
→ Filtering/pagination
→ Dashboard
→ PDFs
→ Tenant-isolation audit
→ DB/API contract audit
→ Query optimization
→ Production config
→ E2E verification
```

Build calculation and ownership primitives before multiplying document endpoints. That prevents Quote, Invoice, and Receipt from growing separate versions of money logic or authorization.

---

# 30. AI-Assisted Implementation Workflow

For each task handed to Codex or another coding agent, provide:

1. Task ID and exact task text.
2. Relevant model/API/invariant excerpts.
3. Current project structure.
4. Files it may change if known.
5. Requirement to propose a short implementation plan first.
6. Requirement to add tests.
7. Explicit instruction not to implement adjacent tasks.

Before committing, verify:

- only this task was implemented;
- no invariant changed silently;
- no schema-absent fields were introduced;
- no server-managed field became writable;
- all user resources are tenant-scoped;
- money uses Decimal/fixed precision, not float;
- calculations are centralized;
- status changes/conversions go through domain services;
- failure cases are tested;
- responses match the API contract;
- the commit remains small and independently revertible.
