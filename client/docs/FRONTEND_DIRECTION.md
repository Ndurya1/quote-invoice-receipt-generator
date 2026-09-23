# Frontend Product and Architecture Direction

Status: implementation-ready MVP direction  
Last reviewed: 22 September 2026

## 1. Purpose and source of truth

This document turns the existing product, design, API, and database documents into one implementable frontend direction. It defines the complete page map, route behavior, user journeys, API dependencies, persisted records, lifecycle actions, shared UI rules, and known contract gaps.

Use this precedence when documents disagree:

1. Implemented backend routes, schemas, invariants, and migrations.
2. `server/docs/backend/API_CONTRACT.md` and `DB_MODELS.md`.
3. This frontend direction.
4. `LANDING_AUTH_ONBOARDING_DESIGN_SPEC.md` and `DASHBOARD_DESIGN_SPEC.md` for visual treatment.
5. `content_copy.md` as draft copy only.

The browser never accesses PostgreSQL directly. Every persisted change follows:

```text
React page -> frontend API client -> /api/v1 endpoint -> backend service -> PostgreSQL
```

## 2. Product boundary

The MVP is a lightweight document workflow for freelancers and small service businesses:

```text
Account -> Business profile -> Client -> Quotation -> Invoice -> Receipt -> PDF
```

Invoices and receipts may also be created directly. The product records document states but does not process money, verify payment, send email or WhatsApp messages, perform currency conversion, file taxes, or provide accounting ledgers.

The main experience must optimize for four outcomes:

- enter business and client information once;
- create a correct document quickly;
- preserve the quotation-to-invoice-to-receipt relationship;
- retrieve and download prior documents without reconstructing them.

Use the formal UI terms `Quotation`, `Invoice`, and `Receipt`. API paths and internal code may retain `quotes` where required by the backend.

## 3. Current implementation baseline

The client is React 19, Vite, React Router, Tailwind CSS, and Lucide. It currently implements only `/` and has no backend integration, authenticated shell, form system, or route protection.

The backend currently supports:

- registration, login, access-token refresh, and current-user lookup;
- one business profile per user;
- client CRUD;
- quotation, invoice, and receipt create/read/list/update/delete operations within domain rules;
- quotation and invoice lifecycle actions;
- quotation-to-invoice and invoice-to-receipt conversion;
- PDF downloads;
- dashboard counts and five recent documents;
- owner-scoped search, filtering, sorting, and pagination.

## 4. Scope decisions and contract reconciliation

| Design/product request | Implemented reality | MVP frontend decision |
| --- | --- | --- |
| Registration immediately authenticates | `POST /auth/register` returns a user, not tokens | After successful registration, call login once with the submitted credentials, then enter onboarding. Show a recoverable login error if that second request fails. |
| Forgot/reset password | No recovery endpoints or token/email flow | Do not ship routes or a `Forgot password?` link. Add only after end-to-end backend support exists. |
| Remember me | Token API has no cookie/session preference | Do not show it. |
| Logout endpoint | None | Clear the local session and cached owner-scoped data, then route to `/login`. Document that this does not revoke an already issued token. |
| Two-step onboarding | Business profile uses one full-replacement `PUT` and has no completion flag | Keep a local onboarding draft between steps and create the profile only at final submit. Profile existence is the completion signal. Never create a partial profile after step one. |
| Default tax, footer, payment instructions, and brand color | No profile columns or API fields | Omit these controls. Step two contains only default currency. Move optional branding defaults to a later backend-backed release. |
| Logo upload | Profile stores only `logo_url`; no upload endpoint exists | Omit file upload in MVP onboarding. Do not ask users to paste a URL during first-run setup. A future upload service may add it. |
| Products and services | No model or endpoint | Remove from MVP navigation. Keep it as a P1 product item, not a dead page. Ad-hoc line items remain available. |
| Dashboard outstanding balance | Summary API returns counts, not currency-grouped balance | MVP dashboard shows counts only. Add monetary outstanding balance only after the API returns totals grouped by currency. Never sum currencies in the browser. |
| Dashboard overdue attention | API exposes overdue count but does not assign overdue automatically | Show the notice only when the returned overdue count is nonzero; do not infer overdue from dates. |
| Review converted documents before save | Conversion endpoints immediately persist the destination, and source-linked invoices/receipts are immutable | Use a confirmation dialog for destination dates, perform conversion, then navigate to the new detail page. Editing converted content requires a future backend workflow change. |
| Duplicate document | No duplicate endpoint; computed and server-managed fields cannot be resubmitted as-is | Defer. Do not expose a menu action. |
| Native send | `/send` changes status only | Label the action `Mark as sent`; explain that delivery happens outside the product. PDF download remains the sharing mechanism. |
| Receipt status | Receipts have no lifecycle status | Do not invent one. Display `Receipt` or `Issued`, not a persisted status badge. |
| Account editing | Only `GET /auth/me` exists | Account screen is read-only plus logout. Name/email/password editing is deferred. |

## 5. Complete route and page map

Routes use readable UI nouns. The API adapter translates `quotations` routes to `/quotes` endpoints.

### 5.1 Public and authentication

| Route | Page | Purpose | API | Persistence/readiness |
| --- | --- | --- | --- | --- |
| `/` | Landing | Explain the connected workflow and start registration | None | Implemented design; enable real links when auth routes land |
| `/register` | Register | Create the minimum user account | `POST /auth/register`, then `POST /auth/login` | Creates `users`; supported |
| `/login` | Login | Start an existing-user session | `POST /auth/login`, `GET /auth/me`, `GET /business-profile` | Reads `users` and profile state; supported |
| `*` | Not found | Recover from invalid URLs | None | Required |

Do not register `/forgot-password` or `/reset-password/:token` in the production router until backend support exists.

### 5.2 Onboarding

| Route | Page | Purpose | API | Persistence/readiness |
| --- | --- | --- | --- | --- |
| `/onboarding/business` | Business details | Capture business/freelancer name, contact details, address, and tax number | `GET /auth/me`; no write yet | Local draft only |
| `/onboarding/defaults` | Document defaults | Choose default currency and review the profile | `PUT /business-profile` on final submit | Creates `business_profiles`; supported |
| `/onboarding/complete` | Setup complete | Offer first quotation or dashboard | None | Ephemeral route; requires profile to exist |

Onboarding fields supported now are `business_name`, `email`, `phone`, `address`, `tax_number`, and `default_currency`. Send `logo_url: null`. Prefill contact email from `/auth/me` but keep it editable as the business contact.

### 5.3 Authenticated workspace

| Route | Page | Primary responsibility | API/data |
| --- | --- | --- | --- |
| `/dashboard` | Dashboard | Counts, recent documents, setup/overdue attention, creation entry points | `GET /dashboard/summary`, profile from session bootstrap |
| `/documents` | Documents | Unified entry with type tabs and URL-backed filters | Type-specific list endpoint selected by `type` query parameter |
| `/documents/quotations/new` | Create quotation | Create a draft quotation | Clients list, profile, `POST /quotes` |
| `/documents/quotations/:quoteId` | Quotation detail | Inspect totals, items, relationship, status, and actions | `GET /quotes/:id`, PDF and action endpoints |
| `/documents/quotations/:quoteId/edit` | Edit quotation | Edit an unlinked draft | `GET` then `PATCH /quotes/:id` |
| `/documents/invoices/new` | Create invoice | Create a direct draft invoice | Clients list, profile, `POST /invoices` |
| `/documents/invoices/:invoiceId` | Invoice detail | Inspect totals, source, state, and actions | `GET /invoices/:id`, PDF and action endpoints |
| `/documents/invoices/:invoiceId/edit` | Edit invoice | Edit an unlinked draft | `GET` then `PATCH /invoices/:id` |
| `/documents/receipts/new` | Create receipt | Create a direct receipt | Clients list, profile, `POST /receipts` |
| `/documents/receipts/:receiptId` | Receipt detail | Inspect totals, source invoice, and download | `GET /receipts/:id`, PDF endpoint |
| `/documents/receipts/:receiptId/edit` | Edit receipt | Edit a direct, unlinked receipt | `GET` then `PATCH /receipts/:id` |
| `/clients` | Clients | Search, sort, paginate, and start client creation | `GET /clients` |
| `/clients/new` | Create client | Add reusable client details | `POST /clients` |
| `/clients/:clientId` | Client detail | Show contact data and entry points for client-filtered documents | `GET /clients/:id`; document links use list filters |
| `/clients/:clientId/edit` | Edit client | Update reusable client information | `GET` then `PATCH /clients/:id` |
| `/settings/business` | Business settings | Replace the stored business profile | `GET`, `PUT /business-profile` |
| `/settings/account` | Account | Display current account identity and logout | `GET /auth/me`; local logout only |

Creation and editing use separate URLs so refresh, browser history, unsaved-change protection, and authorization failures behave predictably. Small client creation may also open from a document form, but it must still use the same validation and API adapter as `/clients/new`.

### 5.4 Intentionally deferred pages

- Password recovery and reset.
- Products/services catalogue.
- Account/profile credential editing.
- Branding/template editor and logo upload.
- Legal pages until approved content exists.
- Reports, analytics, payment processing, reminders, recurring documents, public share links, and customer portals.

## 6. Navigation and route guards

### Public shell

The landing header links to `/register` and `/login`. Logged-in users may still view `/`, but the primary action should become `Go to dashboard`.

### Authentication bootstrap

On application start:

1. Read the locally stored token pair.
2. If an access token exists, call `/auth/me`.
3. If access is rejected and a refresh token exists, refresh once and retry the original request once.
4. If refresh fails, clear the session and route to `/login` with a session-expired message.
5. After user lookup, request `/business-profile`.
6. Treat `BUSINESS_PROFILE_NOT_FOUND` as an expected incomplete-onboarding state, not a global error.

### Guard outcomes

| User state | Public auth route | Onboarding route | Protected app route |
| --- | --- | --- | --- |
| No valid session | Allow | Redirect to `/login` | Redirect to `/login?next=...` |
| Authenticated, no profile | Redirect to onboarding | Allow | Redirect to `/onboarding/business` |
| Authenticated, profile exists | Redirect to dashboard | Redirect to dashboard, except completion immediately after setup | Allow |

Only honor `next` values that resolve to an internal protected path. Never redirect to an arbitrary external URL.

## 7. End-to-end user journeys

### New user

```text
Landing -> Register -> automatic login -> Business details -> Default currency
-> profile PUT -> Setup complete -> Create quotation -> Quotation detail -> Download PDF
```

If automatic login fails after registration, route to login with the email prefilled and explain that the account was created.

### Returning user

```text
Login -> session/profile bootstrap -> requested protected page or Dashboard
```

### Quotation lifecycle

```text
Create DRAFT -> edit/delete OR mark as sent -> accept/reject according to state
-> accepted quotation may convert -> new DRAFT invoice + original becomes CONVERTED
```

### Invoice lifecycle

```text
Create direct DRAFT or convert accepted quotation -> edit/delete if eligible
-> mark as sent -> mark as paid or cancel -> optionally create receipt unless cancelled
```

`PAID` is recorded by the user. It never means the platform processed funds.

### Receipt lifecycle

```text
Create directly -> edit/delete while unlinked
or create from non-cancelled invoice -> linked immutable receipt -> download PDF
```

## 8. Lifecycle action matrix

The frontend must derive visible actions from the persisted status and source-link fields. The backend remains authoritative and a 409 must refresh the detail before explaining the conflict.

### Quotations

| State | Edit | Delete | Mark sent | Accept | Reject | Convert | PDF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DRAFT, unlinked | Yes | Yes | Yes | Yes | No | No | Yes |
| SENT | No | No | No | Yes | Yes | No | Yes |
| ACCEPTED | No | No | No | No | No | Yes | Yes |
| REJECTED / EXPIRED / CONVERTED | No | No | No | No | No | No | Yes |

### Invoices

| State/source | Edit | Delete | Mark sent | Mark paid | Cancel | Create receipt | PDF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DRAFT, direct and unlinked | Yes | Yes | Yes | No | Yes | Yes | Yes |
| DRAFT from quotation | No | No | Yes | No | Yes | Yes | Yes |
| SENT | No | No | No | Yes | Yes | Yes | Yes |
| OVERDUE | No | No | No | Yes | Yes | Yes | Yes |
| PAID | No | No | No | No | No | Yes | Yes |
| CANCELLED | No | No | No | No | No | No | Yes |

An invoice referenced by a receipt cannot be deleted. Because list/detail responses do not expose a receipt count, rely on the backend conflict response if this race or relationship is not already known.

### Receipts

| Source | Edit | Delete | PDF |
| --- | --- | --- | --- |
| Direct (`source_invoice_id` is null) | Yes | Yes | Yes |
| Converted from invoice | No | No | Yes |

## 9. Page composition requirements

### Authentication

- Share one `AuthShell`, form width, field anatomy, and error behavior.
- Registration fields: name, email, password. Do not request phone here even though the API accepts it.
- Display password rules before submit: at least eight characters, one uppercase, one lowercase, and one digit.
- Login fields: email and password only.
- Use stable inline errors and preserve non-password values after recoverable failures.

### Onboarding

- Two steps with text progress (`Step 1 of 2`) and a simple bar.
- Keep the draft in route-level state and session storage so refresh does not lose non-sensitive profile input.
- Clear the draft only after the profile PUT succeeds or the user explicitly discards setup.
- Step two shows default currency and a review summary. It must not fabricate unsupported defaults.
- Completion prioritizes `Create your first quotation`, with `Go to dashboard` secondary.

### Dashboard

- Use the existing restrained application shell and no charts.
- Present quotation, invoice, paid-invoice, and receipt counts from the summary endpoint.
- Show up to five recent documents and filter those five locally by type.
- Use an overdue notice only from `invoices.overdue`.
- For an empty account, keep honest zero counts and replace the table body with first-document guidance.
- Do not show an outstanding monetary total until the backend supplies currency-grouped data.

### Documents list

- One destination with URL-backed `type`, `status`, `client_id`, `search`, `sort`, `page`, and `page_size` controls.
- Default `type=quotations`; each type tab calls only its matching endpoint.
- Debounce search input and reset page to one when filters change.
- Reflect server `meta.total`; do not paginate already paginated data in the browser.
- Type-specific status filters appear only for quotations and invoices.
- Mobile rows become stacked summaries; no horizontal page scroll.

### Document form

All three document forms share:

- client selector with `Add client` escape hatch;
- issue date and type-specific date;
- currency defaulted from the business profile and editable per document;
- one or more line items with description, quantity, and unit price;
- optional tax percentage;
- discount type and value;
- notes, plus terms for quotations and invoices;
- live preview totals calculated with decimal arithmetic;
- a clear statement that saved totals are recalculated by the server.

Never submit document number, status, item IDs on replacement, line totals, subtotal, tax amount, discount amount, total, owner IDs, or timestamps.

### Document detail

- Lead with document type/number, client, status where applicable, issue dates, and total.
- Show line items and full totals without recomputing persisted values.
- Show source/destination relationship when exposed by the resource.
- Keep one primary valid lifecycle action; put secondary and destructive actions in a menu or separated action area.
- Download PDFs as authenticated blobs and preserve the server filename when available.
- Confirm delete, cancel, reject, and conversion actions with consequences stated plainly.

### Clients

- Name is required; email, phone, and address are optional.
- Duplicate email is allowed.
- A `CLIENT_IN_USE` delete failure becomes a durable inline explanation that historical documents protect the client record.
- Client detail links to filtered quotation, invoice, and receipt lists rather than fetching all document types itself.

### Settings

- Business settings must send a complete PUT payload. Merge form values with the loaded profile so omitted optional values do not accidentally erase unrelated fields.
- Existing `logo_url` must be preserved when the UI does not expose logo editing.
- Account settings is read-only until update endpoints exist.

## 10. Frontend data architecture

### Recommended structure

```text
src/
├── app/                 # router, providers, session bootstrap
├── api/                 # request client, endpoints, response/error types
├── auth/                # auth context/store, guards, auth pages
├── components/          # reusable primitives and feedback components
├── features/
│   ├── onboarding/
│   ├── dashboard/
│   ├── clients/
│   ├── documents/       # shared form, totals, list, detail building blocks
│   ├── quotations/
│   ├── invoices/
│   ├── receipts/
│   └── settings/
├── layouts/             # PublicShell, AuthShell, OnboardingShell, AppShell
├── styles/              # tokens and global responsive rules
└── utils/               # currency, dates, decimals, validation mapping
```

Use nested React Router routes. Keep server data in a query/cache layer rather than duplicating it into global UI state. Keep transient form drafts local to the owning route. The auth/session layer is the only global domain state.

### API client rules

- Configure the base URL from a Vite environment variable; never hard-code production origins.
- Parse `{ data }`, `{ data, meta }`, and `{ error }` centrally.
- Attach `Authorization: Bearer <access_token>` only to API requests.
- Coordinate a single refresh request when concurrent calls receive 401, then retry each request at most once.
- Never refresh for registration/login failures or loop on a failed refresh.
- Support JSON, 204 responses, and PDF blobs explicitly.
- Preserve backend decimal strings as strings in API models. Convert only inside display/calculation helpers.
- Cancel stale list/search requests when route filters change.
- Clear all owner-scoped caches at logout or session expiry.

### Token handling

The current JSON-token contract prevents an HTTP-only-cookie implementation. For the MVP, keep access and refresh tokens in session storage behind a small session adapter, never in URLs, logs, error reports, or rendered markup. Apply a strict Content Security Policy at deployment. A future backend change should prefer secure, same-site, HTTP-only refresh cookies and server-side revocation.

### Error mapping

- Map backend 422 locations to field errors when the location identifies a submitted field.
- Show domain errors such as `CLIENT_IN_USE` or `INVALID_QUOTE_STATUS` in the affected region.
- Treat 404 for another tenant exactly like an ordinary missing resource.
- On 409 lifecycle conflicts, invalidate and refetch the resource before rendering new actions.
- On network/5xx errors, preserve user input and provide an in-place retry.

## 11. Frontend-to-database map

This table is conceptual; all access remains API-mediated.

| UI capability | Endpoint(s) | Primary tables | Important rules |
| --- | --- | --- | --- |
| Register | `POST /auth/register` | `users` | Email unique; password stored only as a hash |
| Login/session | `POST /auth/login`, `/refresh`, `/me` | `users` | Bearer tokens; access 15 minutes and refresh 7 days by current defaults |
| Complete/edit setup | `PUT /business-profile` | `business_profiles` | At most one per user; PUT fully replaces editable fields |
| Client management | `/clients` | `clients` | Owner-scoped; referenced clients cannot be deleted |
| Create quotation | `POST /quotes` | `quotes`, `quote_items`, `quote_number_counters` | Number/totals/status server-managed |
| Quotation actions | `/quotes/:id/send|accept|reject` | `quotes` | Explicit state transitions only |
| Convert quotation | `POST /quotes/:id/convert` | `invoices`, `invoice_items`, invoice counter, source `quotes` | Atomic copy + link; source becomes `CONVERTED` |
| Create/manage invoice | `/invoices` | `invoices`, `invoice_items`, `invoice_number_counters` | Only direct unlinked draft invoices are editable/deletable |
| Invoice actions | `/invoices/:id/send|mark-paid|cancel` | `invoices` | Paid is user-recorded state, not a payment transaction |
| Convert invoice | `POST /invoices/:id/convert` | `receipts`, `receipt_items`, receipt counter | Atomic copy + link; source invoice remains |
| Create/manage receipt | `/receipts` | `receipts`, `receipt_items`, `receipt_number_counters` | Only direct receipts are editable/deletable |
| Dashboard | `GET /dashboard/summary` | Aggregates all document/client tables | Counts and five latest records; no balance total |
| PDF download | document `/pdf` endpoint | Reads profile, client, document, and item tables | Generated from persisted, owner-scoped data |

Database identity and relationship summary:

```text
users
├── business_profiles (0..1)
├── clients (many)
├── quotes (many) ── quote_items (many)
├── invoices (many) ── invoice_items (many)
└── receipts (many) ── receipt_items (many)

quote (0..1) -> invoice
invoice (0..many) -> receipt
```

## 12. Calculation and formatting rules

- Use decimal arithmetic, never binary floating point, for live totals.
- Match backend formulas: line total = quantity × unit price; tax is based on subtotal; total = subtotal + tax - discount.
- Round preview monetary results half-up to two decimal places.
- Quantity may have three decimal places, unit price two, tax rate three, and monetary values two.
- The frontend preview is advisory. Replace it with persisted values from the create/update response after save.
- Format as `KES 52,500.00`, using the document currency and locale-aware grouping.
- Never aggregate documents with different currencies.
- Display absolute dates such as `12 Sep 2026`; send ISO `YYYY-MM-DD` values.

## 13. Visual, responsive, and content direction

Continue the existing warm canvas, white surfaces, deep ink, restrained green accent, thin borders, 8px controls, 12px surfaces, and minimal shadows. The tokens in the existing design specifications remain valid.

- Public pages are spacious; application pages are moderately dense.
- Desktop uses a 224px sidebar and a fluid content region up to about 1280px.
- Below 768px, use a compact header and bottom navigation: Home, Documents, Clients, More.
- `More` contains Business settings, Account, and Logout. Do not include Products & services.
- Document forms reflow into one column; totals remain visible and line items become stacked groups.
- All mobile targets are at least 44×44px and bottom navigation reserves safe-area space.
- Status always uses text plus color.
- Use `Mark as sent`, not `Send`, where the action only updates status.
- Use `Download PDF`, not `Email` or `Share`, unless platform integration is added.

## 14. Required states and accessibility

Every data page needs loading, empty, loaded, recoverable error, unauthenticated, and not-found behavior. Mutation pages also need submitting, validation error, domain conflict, success, and unsaved-change states.

Accessibility requirements:

- semantic landmarks and one `h1` per page;
- skip link in public and authenticated shells;
- visible labels and programmatic error associations;
- keyboard-accessible menus, dialogs, and line-item controls;
- focus moved to the first invalid field after failed submit;
- focus returned to the trigger after closing a dialog/menu;
- status announcements for saves and conversions without relying on transient toast alone;
- WCAG AA contrast, visible focus, reduced motion, and usable 200% zoom;
- tables on desktop with equivalent labelled stacked content on mobile.

## 15. Release acceptance

The MVP frontend is complete when a user can:

1. create an account, become authenticated, and finish supported business setup;
2. resume an existing session or recover cleanly from expiry;
3. create, search, inspect, edit where permitted, and delete where permitted a client;
4. create a direct quotation, invoice, or receipt with correct live preview totals;
5. perform every valid implemented lifecycle action and see invalid actions hidden or explained;
6. convert an accepted quotation to an invoice and a non-cancelled invoice to a receipt;
7. identify the linked source document on resulting details;
8. download each document PDF using authenticated persisted data;
9. use dashboard counts and recent documents without mixed-currency claims;
10. complete the same core workflow at 360px, by keyboard, and at 200% text zoom.

No route or visible control may imply an unsupported backend capability.

The implementation hand-off for deferred capabilities is maintained in
[`BACKEND_FOLLOW_UP_CONTRACTS.md`](./BACKEND_FOLLOW_UP_CONTRACTS.md). That document defines the database, API, security, and acceptance criteria required before a deferred feature can receive a production route or navigation item.

## 16. Backend-dependent follow-up readiness

The following capabilities remain intentionally outside the MVP frontend until their backend contracts are complete:

- password recovery and reset;
- persistent onboarding progress and completion;
- business defaults, PDF branding, and logo storage;
- products and services;
- currency-grouped dashboard balances;
- pre-save conversion review and document duplication;
- account editing, password changes, and server-side logout revocation;
- native email and WhatsApp delivery.

The frontend may prepare fixtures and contract tests after backend readiness is demonstrated, but must not add dead routes, disabled navigation, or client-side-only persistence for these capabilities.
