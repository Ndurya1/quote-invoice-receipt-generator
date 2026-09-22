# Frontend Implementation Plan

Status: ready for execution  
Companion direction: `FRONTEND_DIRECTION.md`

## 1. Delivery approach

Build the frontend in vertical slices that remain runnable after every merge. Tasks below are intentionally small: most should fit in a focused change with their own tests and acceptance check. Complete tasks in phase order unless a dependency note says otherwise.

The MVP plan uses only currently implemented backend capabilities. Password recovery, product/service catalogue, logo upload, profile defaults beyond currency, account editing, document duplication, and monetary dashboard balances are excluded until their contracts exist.

### Definition of done for every task

- Behavior matches `FRONTEND_DIRECTION.md` and the backend contract.
- Loading, empty/error, keyboard, and narrow-screen behavior relevant to the change are included.
- No unrelated refactor or fabricated backend behavior is introduced.
- Automated tests cover non-trivial state, validation, and transformations.
- `npm run lint`, frontend tests, and `npm run build` pass.

## 2. Phase 0 — Baseline and decisions

- [ ] **P0-01 — Record the supported MVP scope.** Link the direction and this plan from the client README; list the deferred routes/features. Verify a new contributor can find the source-of-truth order.
- [ ] **P0-02 — Define frontend environment variables.** Add a documented `VITE_API_BASE_URL` example and fail with a clear development error when absent. Verify local and production builds do not hard-code an origin.
- [ ] **P0-03 — Confirm CORS development origin.** Run the Vite client against the FastAPI server and verify an authenticated preflight allows `Authorization` and `Content-Type`. Record the expected local ports.
- [ ] **P0-04 — Choose and pin focused client libraries.** Add a server-query cache, form/validation library, exact decimal library, and test stack only if they are used immediately. Avoid a component framework that conflicts with the existing visual system.
- [ ] **P0-05 — Add frontend test commands.** Provide unit/component and coverage scripts alongside lint/build. Add one smoke test proving the test environment renders React Router content.

Exit: the existing landing page still renders and all baseline commands pass.

## 3. Phase 1 — Application foundation

- [ ] **FND-01 — Create the feature-oriented source structure.** Add `app`, `api`, `auth`, `components`, `features`, `layouts`, `styles`, and `utils` folders with index files only where they improve imports.
- [ ] **FND-02 — Centralize route constants/builders.** Add helpers for quotation, invoice, receipt, client, settings, login, and onboarding paths. Test parameter encoding and internal-only `next` paths.
- [ ] **FND-03 — Replace the flat router with nested routes.** Add public, auth, onboarding, and protected layout branches plus a not-found route. Use placeholders so every planned route can be reached during development.
- [ ] **FND-04 — Add the root provider composition.** Mount router, query/cache provider, session provider, and global announcement/toast region in one place.
- [ ] **FND-05 — Extract shared design tokens.** Preserve the existing colors and spacing while separating public-page rules from reusable tokens and application-shell styles.
- [ ] **FND-06 — Build button and link variants.** Support primary, secondary, quiet, and destructive actions with loading and disabled states. Test accessible names and stable loading width.
- [ ] **FND-07 — Build form field primitives.** Implement label, control, helper text, error text, required marker, and `aria-describedby` wiring for input, textarea, and select.
- [ ] **FND-08 — Build feedback primitives.** Implement inline alert, empty state, regional retry, skeleton, and persistent success message. Keep toasts supplemental.
- [ ] **FND-09 — Build accessible overlay primitives.** Add menu and confirmation dialog behavior with Escape, outside click where appropriate, focus trapping, and focus return.
- [ ] **FND-10 — Add formatting utilities.** Implement absolute date, ISO date input, currency, document type, and status-label formatting. Test KES/USD examples, null status, and long values.
- [ ] **FND-11 — Add responsive verification fixtures.** Create a development-only route or test harness for primitives at desktop, tablet, and 360px widths.

Exit: all route groups render within their shell and the shared UI foundation is testable.

## 4. Phase 2 — API and session layer

- [ ] **API-01 — Implement response-envelope parsing.** Support resource, collection/meta, error, empty 204, and malformed-response cases.
- [ ] **API-02 — Implement the JSON request client.** Resolve the configured base URL, set JSON headers, attach an access token when present, and support abort signals.
- [ ] **API-03 — Normalize API errors.** Preserve status, domain code, safe message, and field locations from 422 details. Never expose raw HTML or stack traces.
- [ ] **API-04 — Implement the session-storage adapter.** Read/write/clear access and refresh tokens behind one module; tolerate unavailable/corrupt storage.
- [ ] **API-05 — Add coordinated refresh.** Allow only one active `/auth/refresh` request, update the access token, and retry waiting requests once.
- [ ] **API-06 — Prevent refresh loops.** Exclude auth endpoints from automatic refresh and terminate the session after a rejected refresh or second 401.
- [ ] **API-07 — Implement PDF requests.** Fetch authenticated blobs, parse a safe filename from `Content-Disposition`, and revoke temporary object URLs after download.
- [ ] **API-08 — Define endpoint adapters.** Add focused modules for auth, profile, clients, dashboard, quotations, invoices, receipts, and PDFs without putting UI logic in them.
- [ ] **API-09 — Define query keys/cache ownership.** Ensure all owner-scoped data can be invalidated together on logout and narrowly after mutations.
- [ ] **API-10 — Add API-layer tests.** Cover refresh concurrency, one-retry behavior, 204, 422 mapping, domain conflicts, aborts, and PDF filename fallback.

Exit: mocked API calls can authenticate, refresh once, parse all response shapes, and clear session data safely.

## 5. Phase 3 — Authentication

- [ ] **AUTH-01 — Build `AuthShell`.** Reuse the product mark and visual tokens, constrain the form width, and support mobile without marketing clutter.
- [ ] **AUTH-02 — Implement session bootstrap.** Load `/auth/me`, then `/business-profile`; represent `anonymous`, `loading`, `needsOnboarding`, and `ready` explicitly.
- [ ] **AUTH-03 — Implement public/protected guards.** Apply the route table in the direction document and preserve safe internal destinations.
- [ ] **AUTH-04 — Build registration validation.** Validate name, normalized email, and the backend's password rules before submit; do not request phone.
- [ ] **AUTH-05 — Submit registration.** Call register, map duplicate-email/422/network errors, preserve safe field values, and prevent duplicate requests.
- [ ] **AUTH-06 — Complete automatic login.** After registration, call login with the submitted credentials and route to business onboarding. If login fails, route to login with email and an account-created explanation.
- [ ] **AUTH-07 — Build login.** Submit email/password, store the token pair, bootstrap current user/profile, and honor an internal `next` destination.
- [ ] **AUTH-08 — Add session-expired behavior.** Clear owner caches and show a stable message on `/login` when refresh fails during protected use.
- [ ] **AUTH-09 — Add logout.** Clear tokens, onboarding drafts, owner-scoped caches, and sensitive form state before navigating to login.
- [ ] **AUTH-10 — Test authentication journeys.** Cover registration success/failure, automatic-login failure, invalid credentials, missing profile redirect, ready-user redirect, unsafe `next`, expiry, and logout.

Exit: a user can register or log in and reaches the correct next route with no dead auth controls.

## 6. Phase 4 — Business onboarding

- [ ] **ONB-01 — Build `OnboardingShell`.** Add quiet top bar, text progress, progress bar, form region, and responsive review/preview region.
- [ ] **ONB-02 — Define the onboarding draft model.** Include only business name, email, phone, address, tax number, and default currency; always prepare `logo_url: null` for a new profile.
- [ ] **ONB-03 — Persist the local draft safely.** Store non-sensitive setup fields in session storage, restore after refresh, version the draft shape, and clear invalid old versions.
- [ ] **ONB-04 — Build business-details step.** Prefill email from `/auth/me`; validate required name and supported contact constraints; save locally without calling profile PUT.
- [ ] **ONB-05 — Build document-defaults step.** Provide ISO currency-code selection, back navigation, helper copy, and a read-only review of step-one values.
- [ ] **ONB-06 — Submit the complete profile.** Send one full `PUT /business-profile`, map field/server errors, and keep the draft when submission fails.
- [ ] **ONB-07 — Build setup completion.** Clear the draft after confirmed persistence and provide `Create your first quotation` plus `Go to dashboard`.
- [ ] **ONB-08 — Protect onboarding steps.** Redirect anonymous users to login and users with an existing profile to dashboard; require a valid local step-one draft before step two.
- [ ] **ONB-09 — Test onboarding.** Cover refresh/resume, back navigation, missing draft, failed PUT, supported payload shape, successful profile bootstrap, and 360px layout.

Exit: profile existence reliably distinguishes setup from the workspace without partial database records.

## 7. Phase 5 — Authenticated shell and navigation

- [ ] **SHELL-01 — Build desktop `AppShell`.** Add 224px sidebar, product mark, Dashboard/Documents/Clients links, and bottom Business settings/Account links.
- [ ] **SHELL-02 — Build mobile application navigation.** Add header and bottom navigation for Home, Documents, Clients, and More with safe-area spacing.
- [ ] **SHELL-03 — Build account menu.** Show current user identity, settings links, and logout with complete keyboard behavior.
- [ ] **SHELL-04 — Add active-route states.** Highlight parent sections for list/create/detail/edit URLs without using color alone.
- [ ] **SHELL-05 — Add application skip link and main focus.** Move focus to the page heading after significant route navigation without disrupting browser back behavior.
- [ ] **SHELL-06 — Remove unsupported navigation.** Ensure Products & services, password recovery, reports, and payment pages do not appear.
- [ ] **SHELL-07 — Test responsive shell behavior.** Verify keyboard, 200% zoom, 360px, safe areas, and long user names.

Exit: every protected page has consistent responsive navigation and accessibility landmarks.

## 8. Phase 6 — Dashboard

- [ ] **DASH-01 — Add dashboard query and state boundary.** Fetch `/dashboard/summary` with regional retry and no stale cross-user data.
- [ ] **DASH-02 — Build dashboard header/actions.** Provide one creation menu on desktop and focused quick actions at smaller widths without duplication.
- [ ] **DASH-03 — Build the count overview band.** Display quotations, invoices, paid invoices, and receipts; link each metric to a URL-backed document filter.
- [ ] **DASH-04 — Build overdue notice.** Render only from `invoices.overdue`; route to the overdue invoice filter and avoid calculating dates locally.
- [ ] **DASH-05 — Build recent documents table.** Render the API's maximum five records with type, client, date, currency/total, status, and detail link.
- [ ] **DASH-06 — Build mobile recent-document rows.** Preserve amount and status, truncate long client names safely, and avoid horizontal scrolling.
- [ ] **DASH-07 — Add local recent-type filtering.** Filter only the returned five records and make the limited scope clear; `View all` opens the full documents page.
- [ ] **DASH-08 — Build first-document empty state.** Show honest zero counts and quotation/invoice creation actions without fake activity.
- [ ] **DASH-09 — Add independent error/loading states.** Keep creation/navigation available when metrics or recent documents fail.
- [ ] **DASH-10 — Test dashboard variants.** Cover empty, populated, overdue, mixed currencies, null receipt status, regional failure, and mobile layouts.

Exit: the dashboard reflects exactly what the summary API supplies and makes no balance claim.

## 9. Phase 7 — Clients

- [ ] **CLI-01 — Build clients list query.** Read URL-backed page, page size, search, and sort; debounce search and cancel stale requests.
- [ ] **CLI-02 — Build clients list/table.** Include responsive rows, total count, pagination, clear filters, loading, empty, and error states.
- [ ] **CLI-03 — Build reusable client form.** Support name, email, phone, and address with frontend/backend field-error mapping.
- [ ] **CLI-04 — Implement create client page.** Submit `POST /clients`, update caches, and navigate to client detail with persistent success context.
- [ ] **CLI-05 — Implement client detail page.** Show stored contact fields and links to each client-filtered document type.
- [ ] **CLI-06 — Implement edit client page.** Load current values, submit only intended PATCH fields, and protect unsaved changes.
- [ ] **CLI-07 — Implement delete client.** Confirm intent, handle 204, and render `CLIENT_IN_USE` as a durable historical-record explanation.
- [ ] **CLI-08 — Add inline client creation adapter.** Reuse the client form from document creation without duplicating validation or API logic.
- [ ] **CLI-09 — Test client workflows.** Cover duplicate email allowance, optional nulls, page reset on search, in-use deletion, foreign/not-found behavior, and inline creation.

Exit: clients are reusable from their own pages and document forms.

## 10. Phase 8 — Shared document foundation

- [ ] **DOC-01 — Implement exact decimal helpers.** Match backend line, tax, fixed/percentage discount, half-up rounding, and total formulas.
- [ ] **DOC-02 — Test calculation edge cases.** Cover fractional quantity, zero price, three-decimal tax, percentage bounds, excessive fixed discount, and large values.
- [ ] **DOC-03 — Define the shared document draft.** Separate editable input from server-managed output and type-specific dates/terms.
- [ ] **DOC-04 — Build client selector.** Search/select owned clients, retain selection across pagination, and open inline creation accessibly.
- [ ] **DOC-05 — Build document metadata fields.** Implement client, issue date, optional expiry/due date, and currency defaulting from profile.
- [ ] **DOC-06 — Build line-item editor.** Add, remove, reorder, and edit at least one item with stable keys and keyboard-operable controls.
- [ ] **DOC-07 — Build tax and discount controls.** Enforce `NONE`, `FIXED`, and `PERCENTAGE` payload rules and label percentages clearly.
- [ ] **DOC-08 — Build notes/terms fields.** Include terms only for quotations/invoices and allow nullable text without sending unsupported fields.
- [ ] **DOC-09 — Build live totals summary.** Present advisory calculations, currency, and validation without making total editable.
- [ ] **DOC-10 — Build payload serializers.** Emit only backend-editable fields and decimal strings; explicitly exclude IDs, totals, status, owner, and timestamps.
- [ ] **DOC-11 — Build server-response hydration.** Replace previews with persisted decimal strings and item ordering after save/update.
- [ ] **DOC-12 — Add unsaved-change protection.** Guard route changes and browser unload only after the form becomes dirty; clear after successful save.
- [ ] **DOC-13 — Build shared detail sections.** Implement metadata, client link, line-item table/mobile list, totals, notes/terms, and relationship block.
- [ ] **DOC-14 — Build status and action utilities.** Derive labels and allowed visible actions from status/source fields using tested matrices.
- [ ] **DOC-15 — Build destructive/action confirmations.** Reuse accessible dialogs for delete, reject, cancel, mark-paid, mark-sent, and conversion consequences.
- [ ] **DOC-16 — Build PDF download action.** Show progress, prevent duplicate clicks, preserve filename, and surface a local retry without navigating away.
- [ ] **DOC-17 — Add shared document accessibility tests.** Cover field errors, item removal focus, dialog focus, stacked mobile semantics, and totals announcements.

Exit: all document types can reuse one validated form/detail foundation while keeping their domain differences explicit.

## 11. Phase 9 — Quotations

- [ ] **QUO-01 — Implement quotation create page.** Default issue date/profile currency, require one item, submit `POST /quotes`, and navigate to detail.
- [ ] **QUO-02 — Implement quotation detail page.** Fetch by ID and render persisted number, dates, status, client, items, totals, notes, terms, and related invoice link when available.
- [ ] **QUO-03 — Implement quotation edit page.** Permit only unlinked drafts, hydrate the shared form, send PATCH, and handle a stale 409 by returning to refreshed detail.
- [ ] **QUO-04 — Implement quotation delete.** Expose only for eligible drafts; handle 204 and navigate to filtered quotations.
- [ ] **QUO-05 — Implement mark-as-sent.** Call `/send`, explain that delivery is external, refresh caches, and update available actions.
- [ ] **QUO-06 — Implement accept action.** Expose for DRAFT/SENT and transition through `/accept` with confirmation appropriate to later conversion.
- [ ] **QUO-07 — Implement reject action.** Expose only for SENT, confirm the terminal effect, and call `/reject`.
- [ ] **QUO-08 — Implement quotation conversion dialog.** Collect invoice issue/due dates, validate date order, call `/convert`, and navigate to the created invoice detail.
- [ ] **QUO-09 — Add quotation tests.** Cover every status/action matrix row, converted history, date validation, immutable fields, 404/409, and PDF download.

Exit: the full supported quotation lifecycle works without implying native delivery or pre-save conversion editing.

## 12. Phase 10 — Invoices

- [ ] **INV-01 — Implement direct invoice create page.** Reuse the shared form with due date and terms; submit `POST /invoices` and navigate to detail.
- [ ] **INV-02 — Implement invoice detail page.** Render persisted fields, source quotation relationship, state, actions, and PDF download.
- [ ] **INV-03 — Implement invoice edit page.** Permit only direct unlinked drafts; hide edit for quotation-derived invoices and handle backend 409 races.
- [ ] **INV-04 — Implement invoice delete.** Expose only for known-eligible drafts and explain conflicts when a receipt or source link prevents deletion.
- [ ] **INV-05 — Implement mark-as-sent.** Transition DRAFT to SENT and make clear that the user sends the downloaded file externally.
- [ ] **INV-06 — Implement mark-as-paid.** Expose only for SENT/OVERDUE, state that this records business information, and call `/mark-paid`.
- [ ] **INV-07 — Implement cancel action.** Expose for DRAFT/SENT/OVERDUE, confirm that cancellation is terminal, and call `/cancel`.
- [ ] **INV-08 — Implement receipt conversion dialog.** Collect issue date, reject cancelled invoices in UI, call `/convert`, and navigate to receipt detail.
- [ ] **INV-09 — Add invoice tests.** Cover direct versus converted editability, all statuses/actions, manual paid language, receipt conversion, conflicts, and PDF.

Exit: direct and converted invoices support every backend lifecycle action and correct immutable-state treatment.

## 13. Phase 11 — Receipts

- [ ] **RCT-01 — Implement direct receipt create page.** Reuse the shared form without due date/terms; submit `POST /receipts` and navigate to detail.
- [ ] **RCT-02 — Implement receipt detail page.** Render number, issue date, client, source invoice when present, items, totals, notes, and PDF action without a fake status.
- [ ] **RCT-03 — Implement direct receipt edit page.** Permit only when `source_invoice_id` is null; send PATCH and handle stale conflicts.
- [ ] **RCT-04 — Implement direct receipt delete.** Confirm, handle 204, and hide for linked receipts.
- [ ] **RCT-05 — Add receipt tests.** Cover direct/linked editability, null status presentation, source relationship, deletion, conflicts, and PDF.

Exit: both direct and invoice-derived receipts behave according to persistence rules.

## 14. Phase 12 — Unified documents experience

- [ ] **LIST-01 — Build document type tabs.** Drive `type=quotations|invoices|receipts` from the URL and call only the selected endpoint.
- [ ] **LIST-02 — Build common search and client filters.** Keep URL state shareable, reset pagination when changed, and pass only supported parameters.
- [ ] **LIST-03 — Add type-specific status filters.** Use exact backend enum values for quotations/invoices; omit status for receipts.
- [ ] **LIST-04 — Add whitelisted sort controls.** Offer only fields supported for the active type and preserve deterministic server ordering.
- [ ] **LIST-05 — Build desktop document table.** Show type/number, client, issue date, amount, status where applicable, and context-valid actions.
- [ ] **LIST-06 — Build mobile document rows.** Stack primary metadata, retain amount and action access, and avoid overflow at 360px.
- [ ] **LIST-07 — Implement pagination/meta behavior.** Use server totals, handle an empty out-of-range page by moving to the last valid page, and retain filters.
- [ ] **LIST-08 — Add list loading/empty/error states.** Distinguish no documents from no filter matches and keep create actions available.
- [ ] **LIST-09 — Add unified-list tests.** Cover each endpoint, query serialization, abort/debounce behavior, status differences, pagination, and responsive semantics.

Exit: Dashboard, Clients, and navigation can link to one predictable searchable document destination.

## 15. Phase 13 — Settings and landing integration

- [ ] **SET-01 — Build business settings form.** Load the profile and expose only supported fields while preserving an existing hidden `logo_url` in the full PUT.
- [ ] **SET-02 — Protect full-replacement updates.** Build the outgoing payload from loaded profile plus validated edits; test that omitted UI fields are not erased accidentally.
- [ ] **SET-03 — Build read-only account page.** Show name, email, optional phone, session limitations, and logout without edit/password controls.
- [ ] **SET-04 — Test settings.** Cover null optional fields, currency changes, full PUT, preserved logo URL, failed saves, and owner-session cleanup.
- [ ] **LAND-01 — Enable landing account links.** Replace disabled controls with `/register` and `/login`; use dashboard CTA for authenticated users.
- [ ] **LAND-02 — Audit landing copy against implemented behavior.** Remove stale availability notes and ensure no payment, sending, password recovery, catalogue, or pricing claims appear.
- [ ] **LAND-03 — Re-run landing regression checks.** Preserve the existing one-`h1`, fragment links, mobile navigation, calculated demo total, focus, and reduced-motion behavior.

Exit: public acquisition, setup, workspace, and settings form one continuous product journey.

## 16. Phase 14 — Integrated quality and release

- [ ] **QA-01 — Add mocked end-to-end new-user journey.** Landing -> register -> login -> onboarding -> create client -> create quotation -> detail -> PDF.
- [ ] **QA-02 — Add mocked full lifecycle journey.** Accept quotation -> convert invoice -> mark sent/paid -> create receipt -> inspect all linked details.
- [ ] **QA-03 — Add direct-document journeys.** Create/edit/delete eligible direct invoice and receipt; verify immutable converted resources.
- [ ] **QA-04 — Add session resilience journey.** Refresh access token during an in-flight protected request, then verify expiry redirects and clears cached owner data.
- [ ] **QA-05 — Add conflict/not-found journey.** Exercise 404 tenant-safe handling, 409 stale lifecycle state, client-in-use deletion, and retryable 5xx.
- [ ] **QA-06 — Perform responsive browser QA.** Verify key pages at 1440px, 1024px, 768px, 390px, and 360px with no horizontal page scroll.
- [ ] **QA-07 — Perform keyboard and screen-reader QA.** Verify landmarks, headings, labels, errors, menus, dialogs, line items, route focus, and live announcements.
- [ ] **QA-08 — Perform 200% zoom and text stress QA.** Use long names, emails, document numbers, amounts, and translated-length copy approximations.
- [ ] **QA-09 — Verify financial display parity.** Compare frontend previews against backend responses for tax/discount/rounding fixtures and always display persisted totals after save.
- [ ] **QA-10 — Verify security behavior.** Confirm no tokens in URLs/logs/DOM, no external `next` redirect, safe PDF filenames, cleared caches on logout, and production CSP documentation.
- [ ] **QA-11 — Run production checks.** Execute lint, tests, coverage, and build from a clean dependency install; resolve warnings that indicate real runtime or accessibility risk.
- [ ] **QA-12 — Update delivery documentation.** Record completed routes, environment setup, validation commands, known limitations, and deferred backend-dependent work.

Exit: all ten release acceptance outcomes in `FRONTEND_DIRECTION.md` pass with evidence.

## 17. Backend-dependent follow-up backlog

These are not hidden frontend tasks. Each needs an API/database decision before UI work begins.

| Backlog item | Required backend capability before frontend implementation |
| --- | --- |
| Password recovery | Request/reset endpoints, expiring one-use tokens, email delivery, rate limiting, and enumeration-safe responses |
| Persistent onboarding progress/completion | Explicit draft/completion model or profile-completion field; current profile existence must no longer be overloaded |
| Default tax/footer/payment instructions/brand color | Profile columns, validation, migrations, read/write schema, and PDF application rules |
| Logo upload | Authenticated upload/storage/delete lifecycle and stable asset URL rules |
| Products/services | Product/service table, owner-scoped CRUD/search, and line-item selection contract |
| Dashboard outstanding balance | Currency-grouped outstanding totals with an agreed definition; no implicit FX conversion |
| Pre-save conversion review | Preview/clone-draft workflow or permission to edit source-linked draft destinations before finalization |
| Duplicate document | Explicit copy endpoint and rules for dates, status, numbering, source links, and items |
| Account editing/password change | Authenticated update endpoints, re-authentication rules, token invalidation, and uniqueness handling |
| Logout/revocation | Refresh-token storage/revocation or secure cookie session model |
| Native email/WhatsApp share | Delivery provider, consent, addressing, templates, status/error tracking, and privacy rules |

## 18. Suggested merge sequence

Keep merges reviewable by grouping only tightly related tasks:

1. Foundation and API client.
2. Authentication and route guards.
3. Onboarding.
4. App shell and dashboard.
5. Clients.
6. Shared document form/calculations.
7. Quotations.
8. Invoices.
9. Receipts.
10. Unified documents and settings.
11. Landing integration and release QA.

Do not begin a document-specific slice before the shared calculation/payload tests pass. Do not expose a lifecycle action before its visibility matrix and 409 recovery are tested.
