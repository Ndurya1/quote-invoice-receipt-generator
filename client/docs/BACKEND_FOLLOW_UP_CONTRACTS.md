# Backend-Dependent Follow-up Contracts

Status: frontend readiness contract, not an implementation of the deferred features
Last reviewed: 23 September 2026

This document turns the deferred items in `FRONTEND_DIRECTION.md` into backend hand-off contracts. It is the entry point for future frontend work: a feature should not receive a production route, navigation item, or optimistic API adapter until its contract has been agreed, implemented, and covered by backend tests.

The current frontend deliberately keeps unsupported features out of the router and navigation. Developer preview access applies to implemented pages only; it must not be used to hide missing persistence or security behavior.

## Contract conventions

- All endpoints are under `/api/v1` and use the existing JSON envelope conventions.
- Owner-scoped resources must derive ownership from the authenticated user, never from a client-supplied owner ID.
- Successful writes return the persisted representation unless the endpoint is explicitly an action or asynchronous job.
- Validation failures use 422, authentication failures use 401, authorization/not-found responses remain tenant-safe, and state conflicts use 409.
- Financial values are decimal strings or the established backend numeric representation. The browser must not sum values across currencies.
- New document actions must define idempotency, lifecycle visibility, conflict behavior, and auditability before frontend work begins.
- Any token, reset link, upload URL, or provider credential must stay out of document URLs, logs, and rendered HTML unless its exposure is explicitly part of the security design.

## Readiness states

| State | Meaning | Frontend consequence |
| --- | --- | --- |
| Blocked | A persistence, endpoint, security, or provider decision is missing | No production route or navigation item |
| Contracted | Request/response, errors, ownership, and acceptance criteria are agreed | Frontend adapter and fixtures may be planned |
| Backend ready | Migration, endpoint, backend tests, and API documentation are available | Frontend implementation may start |
| Frontend ready | UI, developer preview, and release checks are complete | Feature may be exposed in production navigation |

All items below are currently **Blocked** unless noted otherwise.

## 1. Identity and session security

### 1.1 Password recovery

**Frontend outcome:** `/forgot-password` and `/reset-password/:token` with enumeration-safe request feedback, reset form validation, and post-reset login guidance.

**Required backend contract:**

- `POST /auth/password-recovery/request` accepts `{ email }` and returns the same 202-style response for known and unknown addresses.
- `POST /auth/password-recovery/reset` accepts `{ token, password }` and returns a generic success response after atomically consuming the token.
- Reset tokens are stored hashed, expire quickly, are one-use, and are invalidated after password reset or account security changes.
- Requests are rate limited by account and source. Email delivery is asynchronous and does not reveal whether an account exists.
- Password validation uses the same rules as registration and account password change.
- Existing sessions are invalidated after a successful reset, or the contract explicitly states why they remain valid.

**Required acceptance tests:** unknown email has the same status/body shape as a known email; expired, reused, malformed, and cross-account tokens fail safely; reset cannot be replayed; rate limiting is observable without leaking account existence.

### 1.2 Account editing and password change

**Frontend outcome:** editable account identity and a password-change flow at `/settings/account`.

**Required backend contract:**

- `PATCH /auth/me` defines editable fields, uniqueness rules, normalization, and whether email changes require verification.
- `POST /auth/password/change` accepts the current password and new password, with re-authentication and session invalidation rules.
- Email changes must not silently transfer ownership or bypass verification.
- Concurrent updates return 409 or a documented last-write policy.

**Required acceptance tests:** invalid current password, duplicate email, password reuse policy, session invalidation, and stale account updates.

### 1.3 Logout and refresh-token revocation

**Frontend outcome:** logout that revokes the server session, including other tabs where feasible, while preserving local cache cleanup.

**Required backend contract:**

- Choose persistent rotated refresh tokens with revocation, or a secure cookie-backed session model.
- `POST /auth/logout` revokes the current session/token family and is safe to retry.
- Refresh-token reuse detection and account-wide revocation behavior are defined.
- The response does not disclose whether a session was already revoked.

**Required acceptance tests:** logout blocks refresh, repeated logout is harmless, rotation rejects replay, and password reset/account security changes revoke the defined token scope.

## 2. Business profile, onboarding, and branding

### 2.1 Persistent onboarding progress and completion

**Frontend outcome:** onboarding can resume after a refresh, device change, or interrupted session without treating profile existence as completion.

**Required backend contract:**

- Choose an `onboarding_drafts` resource or explicit profile setup fields such as `setup_status`, `setup_step`, and `completed_at`.
- Define whether drafts are user-owned, business-owned, or one-to-one with the account.
- Provide read, upsert, and discard semantics with safe partial updates.
- Define migration behavior for existing profiles: completed, incomplete, or requiring review.
- Completion must be idempotent and must not create duplicate business profiles.

**Suggested endpoints:** `GET /onboarding`, `PUT /onboarding`, `POST /onboarding/complete`, and `DELETE /onboarding` if a discard operation is needed.

**Required acceptance tests:** resume at the saved step, cross-user isolation, completion retry, migration of existing accounts, and abandoned-draft cleanup policy.

### 2.2 Document defaults and branding

**Frontend outcome:** business settings and onboarding can manage default tax, footer text, payment instructions, brand color, and future PDF branding.

**Required backend contract:**

- Add validated profile fields for `default_tax_rate`, `footer_text`, `payment_instructions`, and `brand_color` with explicit null/default behavior.
- Define whether tax is a percentage, rate, or tax profile and how decimal precision is stored.
- Define length, character, and accessibility constraints for text and color values.
- Version PDF rendering behavior so existing documents remain historically stable if profile defaults change later.
- Clarify whether defaults apply only at document creation or are re-read during PDF generation.

**Required acceptance tests:** full PUT preserves unsupported fields, invalid values return 422, defaults apply only to new documents, and historical PDFs/documents do not mutate unexpectedly.

### 2.3 Logo upload

**Frontend outcome:** authenticated logo upload, replacement, preview, and removal in business settings.

**Required backend contract:**

- Choose multipart upload or a short-lived presigned upload flow.
- Enforce authenticated business ownership, MIME/type/size limits, image validation, malware/scanning policy, and safe filename handling.
- Define replacement and delete semantics, stable asset URLs, cache invalidation, and storage cleanup.
- Never trust a client-provided `logo_url` as proof of ownership.
- Define whether PDFs embed the image at document creation or resolve the current logo at render time.

**Required acceptance tests:** unauthorized upload/delete, invalid image, oversized image, replacement cleanup, stale URL behavior, and PDF rendering failure fallback.

## 3. Catalogue and dashboard data

### 3.1 Products and services

**Frontend outcome:** `/products` catalogue with owner-scoped CRUD/search/archive and line-item selection in document forms.

**Required backend contract:**

- Add a product/service table with owner/business scope, kind, name, description, unit, default price, currency, tax behavior, active/archive state, and timestamps.
- Define whether prices are inclusive or exclusive of tax and how a selected item is snapshotted onto a document.
- Provide owner-scoped list/search/pagination and create/update/archive operations.
- Selecting a catalogue item must copy values into a document line item; later catalogue edits must not rewrite historical documents.
- Define duplicate names, currency mismatch, inactive-item selection, and deletion behavior.

**Suggested endpoints:** `GET /products`, `POST /products`, `GET /products/:id`, `PATCH /products/:id`, and `POST /products/:id/archive` or an equivalent soft-delete action.

**Required acceptance tests:** tenant isolation, pagination/search, archived-item behavior, currency validation, line-item snapshotting, and historical integrity.

### 3.2 Dashboard outstanding balance

**Frontend outcome:** dashboard outstanding totals grouped by currency, with a clear definition of included invoices.

**Required backend contract:**

- Add grouped totals such as `{ currency, outstanding, overdue }` rather than one cross-currency number.
- Define whether outstanding includes only SENT/OVERDUE invoices and how PAID, CANCELLED, receipt-linked, credits, and partial payments are handled.
- Define precision, ordering, zero suppression, and whether totals are computed live or cached.
- No implicit foreign-exchange conversion is permitted.

**Suggested response shape:** `dashboard.outstanding_by_currency[]`, where each entry contains the currency code and persisted decimal totals.

**Required acceptance tests:** multiple currencies remain separate, status transitions update totals, cancellation/payment rules are correct, and no browser-side aggregation is required.

## 4. Document workflow extensions

### 4.1 Pre-save conversion review

**Frontend outcome:** a review screen or editable draft before quotation-to-invoice or invoice-to-receipt conversion is finalized.

**Required backend contract:** choose one of these explicit models:

1. A preview endpoint that returns a non-persisted destination representation and a finalize endpoint that accepts reviewed changes.
2. A clone-draft endpoint that creates an editable destination draft with clear source linkage and a finalization action.
3. Permission for the existing conversion endpoint to accept a restricted, validated destination override payload.

The chosen model must define numbering timing, dates, status, item copying, source immutability, idempotency, and what happens when the source changes during review.

**Required acceptance tests:** review does not create duplicate destinations, source links remain correct, server totals are authoritative, cancellation/invalid-source conflicts return 409, and retries are safe.

### 4.2 Duplicate document

**Frontend outcome:** a duplicate action from eligible quotation, invoice, or receipt details that opens a new editable draft.

**Required backend contract:**

- Add a type-specific or unified copy endpoint.
- Define eligible source states, copied fields, copied line items, client behavior, dates, numbering, currency, terms/notes, status reset, and source relationship clearing.
- Server-generated number, totals, IDs, timestamps, ownership, and lifecycle state must never be copied as authoritative values.
- Define idempotency and behavior if the source is deleted or changed during the copy.

**Suggested endpoint:** `POST /documents/{type}/{id}/duplicate` with an optional idempotency key, returning the new draft representation.

**Required acceptance tests:** eligible/ineligible sources, cross-tenant access, immutable source preservation, fresh numbering, reset lifecycle state, and retry behavior.

### 4.3 Native email and WhatsApp sharing

**Frontend outcome:** a share action that can request delivery and display queued/sent/failed status without exposing provider credentials or pretending a PDF was delivered when it was only downloaded.

**Required backend contract:**

- Choose providers and define whether delivery is synchronous or job-based.
- Define recipient validation, consent, opt-out, templates, sender identity, attachment/link strategy, and document access lifetime.
- Add delivery records with provider status, safe error categories, retry policy, and audit timestamps.
- Define privacy rules for phone/email disclosure and whether WhatsApp uses a business account or a deep link.
- Delivery must use a server-authorized document representation, not an access token placed in a public URL.

**Suggested endpoints:** `POST /documents/{type}/{id}/share`, `GET /documents/{type}/{id}/deliveries`, and a provider callback/webhook path if required.

**Required acceptance tests:** consent, invalid destinations, provider failure, retry/idempotency, tenant isolation, attachment authorization, and no sensitive data in logs.

## Frontend entry criteria

Before implementing any follow-up page or API adapter, the corresponding backend work must provide:

1. Migrated schema and rollback/forward migration notes.
2. Documented request, response, validation, 401/403/404/409/422/5xx behavior.
3. Ownership and tenant-isolation tests.
4. Idempotency and concurrency rules for actions and asynchronous jobs.
5. Historical-integrity rules for existing documents and PDFs.
6. Developer fixture data or a safe preview mode that exercises the real response shape.
7. An updated backend API contract checked into `server/docs/backend`.

The frontend phase can then add the route, API adapter, page states, developer preview, integration tests, and release QA for that specific item.

## Recommended delivery order

1. Logout/revocation and password recovery.
2. Account editing/password change.
3. Persistent onboarding progress.
4. Branding defaults and logo storage.
5. Products/services.
6. Duplicate and pre-save conversion review.
7. Outstanding balance.
8. Native email/WhatsApp sharing.

This order protects account security first, then establishes stable business/document data before adding workflow convenience and external delivery providers.
