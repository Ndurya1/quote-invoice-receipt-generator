# Dashboard Design Specification

## 1. Scope

This specification covers only the authenticated dashboard for the invoice generator. It is the first screen a freelancer or small service business sees after signing in.

The dashboard is an overview and launch point—not an analytics product. It should answer three questions quickly:

1. What documents need my attention?
2. What have I worked on recently?
3. How do I create or find a document?

The product generates and manages quotations, invoices, and receipts. It does not process or settle payments. Amounts and paid states shown here come from documents and user-recorded business information.

---

## 2. Product and User Interpretation

### Primary users

- Freelancers
- Independent professionals
- Small service businesses without dedicated finance staff

### Primary job to be done

Create and send a professional quotation, invoice, or receipt with as little repetitive work as possible.

### Dashboard archetype

Lightweight workflow dashboard with moderate whitespace and low data density.

### Expected usage

- Short, task-focused sessions
- Mostly desktop during document creation
- Frequent mobile visits to check, find, or share an existing document

---

## 3. Content Hierarchy

### Primary

- Create a quotation
- Create an invoice
- See documents requiring attention, especially outstanding or overdue invoices

### Secondary

- Open a recent document
- View all documents
- Understand the current quotation, outstanding-invoice, and paid-invoice totals

### Tertiary

- Navigate to clients, saved products/services, and settings
- Access the account menu
- View document dates, references, and statuses

The first visual read should be the page title and document-creation actions. The second should be the outstanding amount. Recent documents should become the main working area below them.

---

## 4. Art Direction

- Calm, precise, and approachable rather than corporate or accounting-heavy.
- A warm white canvas and paper-white work surfaces connect the interface to the documents it produces.
- Deep ink text and a restrained green accent create trust without copying the bright lime treatment in the references.
- Thin structural borders and whitespace do most of the grouping; shadows are reserved for overlays.
- Document numbers and monetary values use tabular numerals for fast scanning.
- Corners are softly squared rather than heavily rounded; the application should feel practical, not toy-like.
- No dashboard chart: the MVP has no trend question important enough to justify one.

### Reference translation

Keep from the supplied screenshots:

- spacious document-oriented composition;
- strong separation between document information and totals;
- restrained neutral palette with one green emphasis color;
- readable form and financial typography;
- visible relationship between quotation, invoice, and receipt artifacts.

Do not copy:

- the invoice form layout onto the dashboard;
- oversized rounded containers;
- bright lime across large areas;
- dense line-item controls;
- dark PDF-preview framing.

---

## 5. Design Tokens

These are starting tokens for implementation and may be adjusted slightly during visual QA.

### Color

| Role | Token | Value | Use |
|---|---|---:|---|
| Canvas | `--color-bg` | `#F6F7F4` | Application background |
| Surface | `--color-surface` | `#FFFFFF` | Main work surfaces |
| Soft surface | `--color-surface-soft` | `#EEF1EC` | Quiet grouped areas and hover states |
| Ink | `--color-text` | `#182019` | Primary text |
| Secondary ink | `--color-text-secondary` | `#536057` | Supporting text |
| Muted ink | `--color-text-muted` | `#768078` | Nonessential metadata |
| Subtle border | `--color-border` | `#DDE2DC` | Dividers and controls |
| Strong border | `--color-border-strong` | `#BBC4BC` | Focused structure |
| Accent | `--color-accent` | `#245C3A` | Primary actions and selected navigation |
| Accent hover | `--color-accent-hover` | `#19472C` | Hover/pressed primary actions |
| Accent soft | `--color-accent-soft` | `#E1EFE5` | Selected navigation and quiet emphasis |
| Success | `--color-success` | `#217A45` | Paid status |
| Warning | `--color-warning` | `#9A6412` | Due soon |
| Danger | `--color-danger` | `#B13A32` | Overdue/cancelled/destructive actions |
| Focus | `--color-focus` | `#4B8B62` | Keyboard focus ring |

Status must always include text; color alone is not sufficient.

### Typography

- Primary family: Inter, Geist, or an equivalent neutral sans-serif already available in the project.
- Page title: 28px/34px, 650 weight.
- Section title: 18px/26px, 600 weight.
- Metric value: 26px/32px, 600 weight, tabular numerals.
- Body and table content: 15–16px/22–24px, 400–500 weight.
- Labels and navigation: 14px/20px, 500–600 weight.
- Metadata: 13px/18px, 400–500 weight.
- Document references and aligned amounts: tabular numerals; monospace is optional only for document numbers.

### Spacing

Use the shared scale: `4, 8, 12, 16, 24, 32, 48, 64`.

### Shape and depth

- Control radius: 8px
- Surface radius: 12px
- Status badge radius: 999px
- Buttons: 8px, not pill-shaped
- Routine surfaces: border only, no shadow
- Menus/dialogs: subtle shadow, e.g. `0 12px 32px rgb(20 30 23 / 0.12)`

### Motion

- Fast interaction: 120ms
- Standard transition: 200ms
- Use opacity/color/short translate transitions only
- Respect `prefers-reduced-motion`

---

## 6. Desktop Page Shell

### Sidebar

- Fixed left rail, approximately 224px wide.
- White surface with a right border; it should visually recede.
- Product mark/name at the top.
- Main navigation:
  - Dashboard
  - Documents
  - Clients
  - Products & services
- Settings and account block anchored toward the bottom.
- Selected item uses an accent-soft background, accent text, and medium weight—no large colored icon tile.

`Documents` is the single top-level destination for quotations, invoices, and receipts. Their individual filters belong inside the Documents screen, preventing an unnecessarily long sidebar.

### Main region

- Fluid content region with a maximum width around 1,280px.
- Desktop gutter: 32px; large desktop gutter: 48px.
- Top padding: 32px.
- No oversized top bar. Account controls can occupy the top-right of the page header.

---

## 7. Dashboard Composition

### A. Page header

Left:

- Heading: `Dashboard`
- Contextual greeting below: `Good morning, Muhammad.`

Right:

- Primary button: `Create document`
- Opens a menu containing:
  - `Create quotation`
  - `Create invoice`
  - `Create receipt`

Because creating a receipt without a preceding invoice is allowed, it remains available, but quotation and invoice appear first.

### B. Quick-start row

Directly below the heading, expose the three product actions promised by the product direction:

- `New quotation` — primary emphasis
- `New invoice` — secondary outlined action
- `View documents` — tertiary text/ghost action

On desktop these form one compact horizontal group, not three large feature cards. This row can replace the header dropdown at narrower widths; do not display duplicate actions simultaneously.

### C. Overview band

Use one shared bordered surface divided into four columns rather than four floating cards.

| Metric | Display | Interaction |
|---|---|---|
| Outstanding balance | Formatted currency total from unpaid/partially settled invoices | Opens filtered outstanding invoices |
| Outstanding invoices | Count | Opens filtered outstanding invoices |
| Paid invoices | Count | Opens filtered paid invoices |
| Quotations | Count | Opens quotations |

`Outstanding balance` receives the strongest type treatment. The other metrics provide context and should not visually compete with it.

For businesses that use multiple currencies, do not add unlike currencies together. Display each currency as a separate line or show the business’s configured reporting currency only when conversion rules exist.

### D. Recent documents

This is the dashboard’s main work area.

Header:

- Section title: `Recent documents`
- Filter control: `All`, `Quotations`, `Invoices`, `Receipts`
- Link: `View all`

Desktop table columns:

| Column | Purpose |
|---|---|
| Document | Type plus document number, e.g. `Invoice · INV-0021` |
| Client | Client/business name |
| Date | Issue date |
| Amount | Right-aligned formatted grand total |
| Status | Draft, Sent, Accepted, Declined, Outstanding, Paid, Overdue, Cancelled, as supported by the document type |
| Action | Overflow menu with context-specific actions |

Row behavior:

- Clicking the row opens the document detail view.
- The overflow menu must not trigger row navigation.
- Show a maximum of five recent documents on the dashboard.
- Avoid checkboxes, bulk actions, column sorting, and search here; those belong on the full Documents screen.

Contextual row actions may include `Open`, `Download PDF`, `Duplicate`, and valid conversions such as `Convert to invoice` or `Create receipt`. Only display actions allowed by that document’s current state.

### E. Attention note

If overdue invoices exist, show one compact inline notice above the recent-documents table:

`2 invoices are overdue` + `Review invoices`

This is a narrow warning strip, not a permanent dashboard card. Hide it when there is nothing actionable.

---

## 8. Suggested Desktop Wireframe

```text
┌───────────────┬─────────────────────────────────────────────────────────┐
│ Product       │ Dashboard                          [Create document ▾] │
│               │ Good morning, Muhammad.                                │
│ Dashboard     │                                                         │
│ Documents     │ [New quotation] [New invoice]  View documents          │
│ Clients       │                                                         │
│ Products      │ ┌────────────┬────────────┬───────────┬──────────────┐ │
│ & services    │ │Outstanding │Outstanding │Paid       │Quotations    │ │
│               │ │KES 84,500  │3 invoices │8 invoices │6 total       │ │
│               │ └────────────┴────────────┴───────────┴──────────────┘ │
│               │                                                         │
│               │ 2 invoices are overdue                 Review invoices │
│ Settings      │                                                         │
│ Account       │ Recent documents     [All | Quotes | Invoices | Receipts]│
│               │ ─────────────────────────────────────────────────────── │
│               │ Invoice · INV-0021  Future Hope  Sep 12  KES 52,500 ...│
│               │ Quote · QUO-0018    Acme Studio  Sep 10  KES 18,000 ...│
│               │ Receipt · REC-0011  Juma & Co.   Sep 09  KES 30,000 ...│
└───────────────┴─────────────────────────────────────────────────────────┘
```

Amounts and names above are explicitly sample data for design/development previews, not production defaults.

---

## 9. Responsive Transformations

### Tablet: 768–1023px

- Sidebar collapses to a 72px icon rail if the project uses persistent navigation; otherwise it becomes a drawer.
- Main gutter reduces to 24px.
- Overview band becomes a 2×2 grid while remaining one shared surface.
- Recent-documents table hides the separate date column first; date moves below the document number.
- Preserve amount and status because they drive scanning and action.

### Mobile: below 768px

- Replace sidebar with a compact top header and four-item bottom navigation:
  - Home
  - Documents
  - Clients
  - More
- `More` contains Products & services, Settings, and account actions.
- Page gutter: 16px.
- Header title reduces to 24px.
- Display one full-width primary `New quotation` button and a smaller `New invoice` action beside or beneath it depending on available width.
- Move `Create receipt` into the create menu to keep the first viewport focused.
- Overview metrics become two columns. Outstanding balance spans both columns and appears first.
- Convert each recent-document row into a compact stacked row:
  - first line: type/number and amount;
  - second line: client;
  - third line: date and status.
- Bottom navigation must not cover the final row; reserve safe-area and bar height.
- Avoid horizontal scrolling on the dashboard.

At 360px, long client names truncate to one line with the full value available on the detail screen. Amounts never overlap status labels.

---

## 10. Component Behavior and States

### Buttons and menus

- Visible keyboard focus ring.
- Menus close on selection, Escape, or outside click.
- Loading labels remain stable in width where possible, e.g. `Creating…`.
- Disable document creation only when required business-profile data is missing; explain the reason near the disabled action.

### Metric cells

- Entire cell may be clickable if it has a clear hover and focus state.
- Show a label plus value; never rely on an icon alone.
- Loading uses quiet text-line skeletons without layout movement.

### Recent-document rows

- Hover uses the soft surface token.
- Focus-within receives a visible outline.
- Status badges use subtle tinted backgrounds and readable text.
- Monetary values are right-aligned on desktop and use tabular numerals.

### Empty state: new account

Do not show meaningless zero cards and an empty table as the entire experience.

Show:

- Heading: `Create your first quotation`
- Supporting text: `Your business details will be reused on future quotations, invoices and receipts.`
- Primary action: `Create quotation`
- Secondary action: `Create invoice`

Keep the overview band visible with honest zero values, but replace the recent-documents table body with this compact empty state.

### Error state

If dashboard data fails to load:

- Keep navigation and creation actions available.
- Show: `We couldn’t load your document summary. Your documents are safe.`
- Provide `Try again` locally within the failed region.
- If recent documents and metrics fail independently, show separate regional errors rather than failing the whole page.

### Success state

After creating or converting a document, navigate to its detail/preview screen. When the user returns, place the newest document first and optionally show one restrained confirmation toast. Do not use success animations on the dashboard.

### Permission/profile state

If the business profile is incomplete, display one actionable setup strip:

`Add your business details before creating a document.` + `Complete setup`

Do not show both the setup strip and overdue strip with equal prominence; setup takes precedence because it blocks the primary task.

---

## 11. Data and Copy Rules

- Use `Quotation`, `Invoice`, and `Receipt` as the formal document names.
- Use `New quotation` in action copy rather than mixing `quote` and `quotation` throughout the interface.
- A quotation converts into a new, linked invoice; the original quotation remains unchanged.
- A receipt can be created directly or from an invoice according to product rules.
- Do not use `payment processed`, `payout`, `wallet`, `transaction success`, or similar platform-payment language.
- `Paid` describes an invoice status recorded by the user/business; it does not claim the platform settled funds.
- Format monetary values with both currency and thousands separators, e.g. `KES 52,500.00`. Decimals may be hidden only through a consistent business-level preference.
- Use absolute dates in document rows, e.g. `12 Sep 2026`, rather than ambiguous numeric dates.

---

## 12. Accessibility Requirements

- Semantic `nav`, `main`, headings, table, buttons, and menu controls.
- Skip link to main content on desktop.
- Minimum 44×44px touch targets on mobile.
- Visible focus for all interactive elements.
- Table overflow menu has an accessible name containing the document reference.
- Status is represented by text as well as color.
- Currency is available to assistive technology and never communicated using a flag alone.
- Skeleton/loading states use appropriate live-region behavior without repeatedly announcing changes.
- At 200% text zoom, dashboard content must reflow without clipping or loss of actions.

---

## 13. Dashboard Component Map

```text
DashboardPage
├── AppShell
│   ├── Sidebar / MobileHeader
│   └── MobileBottomNav
├── DashboardHeader
│   └── CreateDocumentMenu
├── QuickActions
├── ProfileSetupNotice (conditional)
├── OverviewBand
│   └── MetricCell × 4
├── OverdueNotice (conditional)
└── RecentDocumentsSection
    ├── DocumentTypeFilter
    ├── RecentDocumentsTable (desktop/tablet)
    ├── RecentDocumentList (mobile)
    └── DashboardEmptyState / RegionalError
```

Keep components aligned to actual behavioral boundaries. Do not extract one-off wrappers into generic components merely for abstraction.

---

## 14. Implementation Boundaries for This Slice

### Include

- Responsive app shell
- Dashboard header and creation entry points
- Four dashboard metrics
- Conditional setup/overdue notices
- Recent document filtering and rows
- Loading, empty, regional error, hover, focus, and menu states
- Navigation hooks/placeholders for dashboard actions

### Exclude for now

- Invoice/quotation/receipt creation forms
- Full Documents screen
- Client and product/service management screens
- PDF preview implementation
- Authentication screens
- Charts and trend analytics
- Platform payment processing
- Advanced reporting, exports, bulk actions, and dashboard customization

---

## 15. Acceptance Checklist

- A first-time user can identify how to create a quotation within five seconds.
- A returning user can identify outstanding invoice value and open recent work without scrolling on a typical laptop viewport.
- The dashboard contains no chart, card wall, or duplicated creation controls.
- Recent documents show at most five rows.
- Quotations, invoices, and receipts are visually identifiable without three unrelated design systems.
- The dashboard never implies that the product processes money.
- Mixed-currency balances are not incorrectly summed.
- Desktop, tablet, 360px mobile, keyboard navigation, long client names, loading, empty, and error states are accounted for.
- The visual system uses one accent, restrained radii, structural borders, and minimal shadow.
