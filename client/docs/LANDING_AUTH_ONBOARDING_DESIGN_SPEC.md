# Landing, Authentication, and Onboarding Design Specification

## 1. Purpose

This document defines the design direction, layout constraints, responsive behavior, content hierarchy, interaction states, and implementation boundaries for the public landing page, authentication screens, and initial business onboarding of the plug-and-send quotation, invoice, and receipt product.

It extends the visual system established in `DASHBOARD_DESIGN_SPEC.md` while adapting that system to three different interface archetypes:

- **Landing page:** spacious marketing and product explanation.
- **Authentication:** quiet, focused account access.
- **Onboarding:** short, guided business setup.

The product is a lightweight document-generation and document-lifecycle tool for freelancers and small service businesses. It is not an accounting suite, ERP, POS, payment gateway, or financial dashboard.

The core product promise is:

> **Enter your business information once. Create a quotation, turn it into an invoice, and generate a receipt without typing everything again.**

---

## 2. Product Truths That Must Shape the Screens

1. The main workflow is `Business setup → Quotation → Invoice → Receipt`.
2. Quotation, invoice, and receipt are connected documents, not unrelated generators.
3. A user may also create an invoice or receipt directly where product rules permit.
4. The platform generates and manages documents; it does not process or settle money.
5. Line-item quantity and rate/amount are entered by the user. The system calculates line totals, discounts, taxes, and grand totals.
6. Saved business information should reduce later re-entry.
7. The primary users value speed and simplicity more than accounting depth.
8. The product must work comfortably on mobile, including onboarding.

### Language constraints

- Use **quotation**, **invoice**, and **receipt** as the formal document names.
- Use **Create quotation** rather than switching inconsistently between “quote” and “quotation.”
- Do not use language such as `process payments`, `get paid through us`, `wallet`, `payout`, `payment success`, or `secure checkout`.
- When a paid amount or status is shown, make it clear that it is business information recorded by the user, not money handled by the platform.
- Do not market the product as generic accounting software.

---

## 3. Cross-Screen Visual System

### 3.1 Art direction

The interface should feel calm, precise, lightweight, and approachable. It should look professional enough for business documents without appearing corporate, institutional, or accounting-heavy.

- Warm-white backgrounds should evoke paper without using literal paper textures.
- White surfaces should feel like practical work areas rather than floating decorative cards.
- Deep ink text should carry most of the visual weight.
- Restrained dark green should identify important actions and selected states.
- Thin borders and whitespace should create structure.
- Shadows should be reserved for overlays and the hero’s elevated invoice-form demonstration.
- Corners should remain softly squared, not excessively rounded.
- Decorative gradients, glassmorphism, floating blobs, and dashboard-style chart imagery are excluded.

### 3.2 Shared tokens

| Role | Token | Value | Constraint |
|---|---|---:|---|
| Canvas | `--color-bg` | `#F6F7F4` | Default page background |
| Surface | `--color-surface` | `#FFFFFF` | Forms and primary work surfaces |
| Soft surface | `--color-surface-soft` | `#EEF1EC` | Quiet grouping and hover states |
| Ink | `--color-text` | `#182019` | Headings and primary content |
| Secondary ink | `--color-text-secondary` | `#536057` | Descriptions and helper text |
| Muted ink | `--color-text-muted` | `#768078` | Low-priority metadata |
| Border | `--color-border` | `#DDE2DC` | Dividers and controls |
| Strong border | `--color-border-strong` | `#BBC4BC` | Focused or emphasized structure |
| Accent | `--color-accent` | `#245C3A` | Primary buttons and active states |
| Accent hover | `--color-accent-hover` | `#19472C` | Hover and pressed actions |
| Accent soft | `--color-accent-soft` | `#E1EFE5` | Quiet emphasis |
| Success | `--color-success` | `#217A45` | Completed/success state |
| Warning | `--color-warning` | `#9A6412` | Attention state |
| Danger | `--color-danger` | `#B13A32` | Validation and destructive state |
| Focus | `--color-focus` | `#4B8B62` | Keyboard focus ring |

### 3.3 Typography

- Use Inter, Geist, or an equivalent neutral sans-serif already available in the project.
- Landing display heading: `48–56px / 1.06–1.12`, weight `650–700` on desktop.
- Landing display heading on mobile: `36–40px / 1.08–1.15`.
- Landing section heading: `32–40px / 1.15–1.22`, weight `600–650`.
- Authentication/onboarding page title: `28–32px / 1.2`, weight `650`.
- Body: `16–18px / 1.5–1.65` on marketing pages; `15–16px / 1.45–1.55` in forms.
- Labels and navigation: `14px / 20px`, weight `500–600`.
- Metadata and helper text: `13px / 18px`.
- Financial values use tabular numerals.
- Limit hero copy to roughly 12 words in the headline and two short lines in the supporting paragraph.

### 3.4 Shape, controls, and depth

- Input and button radius: `8px`.
- Standard surface radius: `12px`.
- Buttons must not be pill-shaped.
- Default input height: `44–48px`.
- Primary buttons use a solid accent background.
- Secondary buttons use a white or transparent background with a structural border.
- Links use text treatment; do not turn every link into a button.
- Routine cards use borders rather than shadows.
- Overlays may use `0 12px 32px rgb(20 30 23 / 0.12)`.
- The invoice-form demonstration may use a quieter wide shadow to separate it from the hero canvas, but it must still look like software rather than a floating poster.

### 3.5 Motion

- Fast interaction: `120ms`.
- Standard transition: `200ms`.
- Use opacity, color, border, and short translate transitions only.
- Do not animate financial totals continuously.
- Do not use scroll-jacking, parallax, auto-playing carousels, or looping decorative motion.
- Respect `prefers-reduced-motion`.

---

## 4. Global Whitespace Constraints

Whitespace is a structural requirement, especially on the landing page. It must establish clarity and confidence rather than merely fill unused space.

### Landing-page spacing

- Main content width: `min(1200px, calc(100% - gutters))`.
- Desktop horizontal gutter: `48–64px`; wide desktop: up to `80px`.
- Tablet horizontal gutter: `32px`.
- Mobile horizontal gutter: `20px`; never below `16px`.
- Hero top spacing below navigation: `80–112px` on desktop and `48–64px` on mobile.
- Hero copy-to-form gap: `56–80px` on desktop and `40–56px` on mobile.
- Major section vertical spacing: `112–160px` on desktop, `80–112px` on tablet, and `64–88px` on mobile.
- Section heading-to-content gap: `40–64px`.
- Never stack unrelated bordered sections directly against each other.
- Avoid filling every open area with badges, icons, decorative marks, or secondary copy.
- A landing-page section should communicate one primary idea. If it needs two unrelated headings, split it.

### Authentication/onboarding spacing

- These screens may be denser than the landing page but must remain calm.
- Use `24–32px` between major form groups.
- Use `16px` between related fields and `8px` between a field label and control.
- Keep at least `32px` between the title block and the first field.
- Keep at least `24px` between the final field and primary action.
- Do not compress screens vertically just to keep everything above the fold; scrolling is preferable to cramped controls.

---

## 5. Screen Inventory and Route Intent

| Screen | Suggested route | Primary purpose |
|---|---|---|
| Landing page | `/` | Explain the connected document workflow and drive account creation |
| Registration | `/register` | Create the minimum viable user account |
| Login | `/login` | Return an existing user to their workspace |
| Forgot password | `/forgot-password` | Request password recovery, if supported by the authentication backend |
| Reset password | `/reset-password/:token` | Set a new password, if supported by the authentication backend |
| Business setup | `/onboarding/business` | Save reusable business identity and document defaults |
| Setup completion | part of onboarding | Confirm readiness and start the first document |

Password recovery screens are part of the visual specification but should only ship when the backend supports the full recovery flow. Do not place a non-functional “Forgot password?” link in production.

---

## 6. Landing Page

### 6.1 Landing-page objective

Within the first viewport, a visitor should understand:

1. The product creates professional quotations, invoices, and receipts.
2. The key advantage is not typing the same information again.
3. The next action is to create an account and begin with a document.

The landing page should not attempt to document every field or feature. It should tell a short product story: **set up once → create → convert → send**.

### 6.2 Public navigation

#### Content

- Product mark/name on the left.
- Optional anchor links: `How it works`, `Features`.
- `Log in` as a quiet text or outlined action.
- `Get started` as the single solid primary action.

#### Constraints

- Maximum two informational navigation links before account actions.
- Do not add `Solutions`, `Resources`, `Company`, or complex mega-menus for the MVP.
- Navigation height should be approximately `72–80px` on desktop and `64px` on mobile.
- Use the warm canvas or a lightly translucent matching background; avoid a heavy contrasting header bar.
- Sticky navigation is optional. If sticky, add a bottom border after scroll rather than a large shadow.
- Mobile navigation may collapse informational links, but `Log in` or `Get started` must remain discoverable.

### 6.3 Hero copy

#### Recommended hierarchy

- Optional quiet eyebrow: `Quotations, invoices and receipts—connected.`
- Headline: `Create it once. Carry it from quotation to receipt.`
- Supporting copy: `Save your business details, build a professional document in minutes, and reuse the same job instead of starting again.`
- Primary action: `Create your first quotation`
- Secondary action: `See how it works`
- Quiet supporting note where truthful: `No accounting setup required.`

#### Constraints

- The headline must communicate reduced repetition or connected documents, not merely “beautiful invoices.”
- Do not place more than two CTAs in the hero.
- Do not use fabricated user counts, ratings, logos, testimonials, or claims such as “trusted by thousands.”
- Do not introduce pricing language until pricing actually exists.
- Keep the copy block centered with a maximum width around `760px` so the composition can breathe.
- Primary and secondary CTAs should sit on one row on desktop and stack at narrow mobile widths.
- The invoice form below the copy is the dominant proof of the product; no competing illustration should appear beside the headline.

### 6.4 Hero invoice-form demonstration

The typical SaaS dashboard screenshot at the bottom of the hero is replaced with a simplified invoice form. This is the landing page’s main product demonstration.

#### Purpose

- Show how little effort is required to create a useful document.
- Make quantity, rate, and automatic totals understandable at a glance.
- Visually connect the marketing promise to the real application UI.

#### Visible content

- Document switch or label: `Quotation`, `Invoice`, `Receipt`, with `Invoice` used for the initial static example.
- Business identity area with a restrained logo placeholder and sample business details.
- `Bill to` client field.
- Issue date and due date.
- A compact line-item table with two sample rows.
- Columns: description, quantity, rate, amount.
- Subtotal, discount, tax, and total.
- A visible but non-functional preview CTA such as `Preview document` only if the entire hero form is presented as an interactive demo.
- A small workflow cue below or adjacent: `Quotation → Invoice → Receipt`.

#### Form constraints

- The hero form is a curated demonstration, not the complete production form.
- Show enough fields to communicate value but avoid dense settings, terms editors, payment instructions, upload controls, overflow menus, and all advanced options.
- Limit the desktop example to approximately two line items.
- The form should be approximately `960–1080px` wide, centered, and visually separated from the background.
- Keep at least `48px` of clear canvas around the form on large screens.
- On desktop, the form may slightly extend below the first viewport to encourage scrolling, but the headline and both CTAs must remain visible without relying on the form.
- On mobile, do not scale a desktop screenshot until text becomes unreadable. Recompose the form: stack metadata, show description on one row and quantity/rate beneath it, then keep the totals visible.
- Mobile may show one line item and a partial second item to preserve legibility.
- The total must be system-calculated in the demonstration; do not present total as a manually editable field.
- Use realistic sample information clearly understood as demonstration data. Do not use real customer information.
- If fields appear editable, they must have real hover, focus, typing, and recalculation behavior. If they are not interactive, avoid misleading active cursors and controls.
- The form must not suggest that the platform processes payment.

### 6.5 Problem section

#### Message

Contrast the repetitive manual workflow with the connected product workflow.

- Manual: `Open an old file → re-enter details → export → repeat later`.
- Product: `Create quotation → convert to invoice → generate receipt`.

#### Constraints

- Use one two-column comparison on desktop and a vertical sequence on mobile.
- Keep the language grounded in user effort rather than abstract productivity claims.
- Do not use six separate pain-point cards.
- A small number of structural arrows or document icons is acceptable; they should support reading rather than decorate empty space.
- Preserve generous top and bottom whitespace so the comparison feels like a clear pause after the hero.

### 6.6 How it works

#### Steps

1. `Set up your business once`
2. `Create a quotation or invoice`
3. `Convert and reuse the details`
4. `Download and send the PDF`

#### Constraints

- Use a connected horizontal sequence on desktop and a vertical sequence on mobile.
- Limit each step to a short heading and one sentence.
- Steps should read as one lifecycle, not four unrelated feature cards.
- Give the conversion step the strongest visual emphasis because it differentiates the product.
- Do not introduce a payment-processing step.
- Do not use screenshots for every step; one document-chain visual or restrained UI fragments are enough.

### 6.7 Core benefits

Use no more than three benefits:

- `Your business details, already filled in`
- `Documents that stay connected`
- `Professional PDFs without rebuilding templates`

#### Constraints

- Prefer one open three-column row over large floating cards.
- Use a small line icon or document mark, not colorful illustrations.
- Each benefit receives one concise paragraph.
- Do not repeat the same explanation already used in “How it works.”
- Avoid claiming features outside the implementation, including native WhatsApp delivery, automated reminders, online payment links, eTIMS integration, or advanced accounting.

### 6.8 Product workflow showcase

Show one transaction moving through three document states:

`Quotation #QUO-0012 → Invoice #INV-0008 → Receipt #REC-0004`

#### Constraints

- Make the linked relationship visible through shared client/job information.
- The original quotation remains visually distinct; conversion does not look like renaming the same file.
- Keep the showcase document-oriented and readable; do not turn it into an analytics dashboard.
- On mobile, use a stacked timeline with short connector lines.
- Avoid implying that every receipt must originate from an invoice if direct receipt creation remains supported.

### 6.9 Final CTA

#### Content

- Heading: `Create the document. Reuse the work.`
- Supporting sentence focused on setting up once and creating the first quotation.
- Primary action: `Get started`
- Secondary text link: `Log in`

#### Constraints

- Use a contained accent-soft or paper-white section rather than a full bright-green block.
- Preserve at least `72–96px` vertical padding on desktop.
- Do not add urgency, countdowns, false scarcity, or unsupported “free forever” language.
- Keep only one primary action.

### 6.10 Footer

- Product mark/name.
- One-sentence product description.
- Links required for navigation or compliance: `Log in`, `Create account`, `Privacy`, and `Terms` when those pages exist.
- Optional copyright line.

#### Constraints

- Keep the footer compact and low-density.
- Do not fabricate company addresses, support channels, social links, or legal pages.
- Use a top border and generous padding; avoid a dark oversized footer unless the final brand system explicitly requires it.

---

## 7. Registration Screen

### 7.1 Objective

Create the minimum account required to begin onboarding, with as little interruption as possible.

### 7.2 Content hierarchy

1. Product mark with a link back to the landing page.
2. Heading: `Create your account`
3. Supporting text: `Set up your business once, then reuse the details on every document.`
4. Name field, if required by the account schema.
5. Email field.
6. Password field.
7. Password requirements shown before failure.
8. Primary action: `Create account`
9. Existing-account link: `Already have an account? Log in`
10. Terms acknowledgement only if required and linked to real pages.

### 7.3 Layout constraints

- Use a centered form column with a maximum width of `420–460px`.
- The page may use a subtle two-region layout on large desktop, but the form must remain the dominant region.
- Any secondary region should reinforce the product promise with one quiet document-chain visual; it must not become another landing page.
- On tablet and mobile, use a single-column layout.
- Keep the form surface border-only or place the form directly on the canvas. Avoid a small floating card inside a large empty background unless the surrounding composition is intentional.
- Do not place social-login buttons unless those providers are implemented.
- Do not request business information during registration; that belongs to onboarding.
- Do not request phone number, address, currency, tax information, or logo at this stage.

### 7.4 Interaction constraints

- Show validation beside the relevant field, not in a generic toast.
- Preserve entered values after a recoverable server error, except passwords where security rules require clearing.
- Password reveal control requires an accessible label and at least a `44×44px` target.
- Submit on Enter when the form is valid.
- Loading action copy: `Creating account…`; prevent duplicate submission.
- On success, establish the authenticated session and move directly into business setup.
- If the email already exists, explain the next step and provide a `Log in` link.
- Do not reveal whether unrelated email addresses exist through inconsistent recovery messaging.

---

## 8. Login Screen

### 8.1 Objective

Return an existing user to the product with minimal friction.

### 8.2 Content hierarchy

1. Product mark.
2. Heading: `Welcome back`
3. Supporting text: `Log in to continue with your documents.`
4. Email field.
5. Password field with reveal control.
6. `Forgot password?` link only when recovery is implemented.
7. Primary action: `Log in`
8. Registration link: `New here? Create an account`

### 8.3 Layout and behavior constraints

- Reuse the same authentication shell and form width as registration.
- Keep the screen visibly simpler than registration.
- Do not show dashboard metrics, document lists, or testimonials beside the form.
- The primary action should span the form width on mobile.
- Use one neutral error message for invalid credentials: `Email or password is incorrect.`
- Maintain a visible focus state and sensible keyboard order.
- Loading action copy: `Logging in…`; prevent repeated requests.
- If the account has no completed business profile, route to onboarding after login.
- If onboarding is complete, route to the dashboard or the originally requested protected screen.
- Do not include a `Remember me` checkbox unless session behavior genuinely supports it.

---

## 9. Forgot-Password Screen

### 9.1 Objective

Allow a user to request recovery without exposing account existence.

### 9.2 Constraints

- Use the same authentication shell.
- Include one email field and one primary action: `Send reset link`.
- Supporting copy should explain where the link will be sent and that it may take a moment.
- After submission, show the same confirmation whether or not the email is registered.
- Confirmation example: `If an account exists for that email, we’ve sent password-reset instructions.`
- Provide a clear route back to login.
- Do not add phone/SMS recovery unless implemented.
- Do not show success as a transient toast only; the submitted state should remain visible on the page.

---

## 10. Reset-Password Screen

### 10.1 Objective

Let a user choose a new password from a valid recovery link.

### 10.2 Constraints

- New password and confirm-password fields only.
- Display password requirements before submission.
- Show expired or invalid-link errors as a dedicated page state with a `Request another link` action.
- Do not place the user inside the application until the reset and authentication behavior has completed securely.
- On success, show a stable confirmation and a `Log in` action.
- Password mismatch is a field-level error.
- Use the same form width, control styling, and spacing as other authentication screens.

---

## 11. Business Onboarding

### 11.1 Objective

Collect the reusable business information necessary to create the first professional document. The flow should feel like preparation for a concrete result, not administrative account configuration.

### 11.2 Flow structure

Use a short two-step onboarding flow:

1. **Business details** — identity and contact information.
2. **Document defaults** — currency, tax default, and optional document information supported by the MVP.

A final completion state launches the user into document creation.

Two steps are preferred because one long form feels heavier, while four or more steps exaggerate a small setup task.

### 11.3 Onboarding shell

- Product mark in a quiet top bar.
- `Step 1 of 2` text and a simple progress indicator.
- Main form column: maximum `640px`.
- Optional desktop preview column: maximum `420px`, showing how entered information appears on a document.
- Desktop content container: approximately `1100px` maximum.
- On mobile, hide or move the live preview below the form; it must not reduce field width.
- Provide `Save and continue` as the primary action.
- Provide `Back` on step two.
- A `Save and finish later` action is allowed only if partial profile persistence is implemented.
- Do not provide a generic skip action for information required to create a document.

### 11.4 Step 1 — Business details

#### Fields

- Business or freelancer name — required.
- Email — prefills from the account where appropriate and remains editable if business contact email differs.
- Phone number — optional unless business rules require it.
- Address — optional.
- Tax or registration identifier — optional and clearly labeled.
- Logo — optional.

#### Constraints

- Make it explicit that an individual freelancer can use their own name; “business” must not imply a registered company is required.
- Required fields should be few and marked consistently.
- Logo upload must remain optional and should not block progress.
- Logo guidance should specify accepted type and size only when those rules are implemented.
- Do not ask for client information, line items, or document numbers here.
- Avoid two-column field layouts below `768px`.
- On desktop, only naturally paired short fields may share a row; business name and address remain full-width.
- The preview updates quietly as the user types, without animation or layout shift.
- If the user leaves and returns, restore saved progress.

### 11.5 Step 2 — Document defaults

#### Fields

- Default currency — required if the MVP supports multiple currencies; otherwise use the fixed product currency and omit the control.
- Default tax rate — optional, with `No default tax` as a valid state.
- Default notes/footer — optional where supported.
- Payment instructions — optional business text only where supported; it must not look like payment integration setup.
- Brand accent color — optional only if lightweight branding is in the implemented MVP.

#### Constraints

- Use plain explanations of how defaults work: they prefill future documents and can be changed on an individual document.
- Never combine unlike currencies or suggest foreign-exchange conversion.
- Currency selection uses currency codes such as `KES`, `USD`, `EUR`, and `GBP`; do not rely on flags.
- Tax inputs must clarify whether the value is a percentage.
- The UI must not imply tax filing, tax validation, or eTIMS integration.
- Payment-instruction fields are free text for the generated document, not a gateway connection.
- Advanced numbering, template design, and accounting preferences are excluded from initial onboarding.
- Optional fields may sit inside one collapsible `Additional defaults` group if the step becomes visually long; required controls must never be collapsed.

### 11.6 Completion state

#### Content

- Heading: `Your business details are ready`
- Supporting text: `They’ll be reused on future quotations, invoices and receipts.`
- Primary action: `Create your first quotation`
- Secondary action: `Go to dashboard`

#### Constraints

- Keep the completion state compact; do not turn it into a celebration screen.
- A small check mark is sufficient. Do not use confetti or long animations.
- The primary action should align with the product’s first-time empty state.
- The user must be able to edit business information later from Settings.
- If setup is incomplete, the dashboard should show the existing actionable setup notice rather than silently failing document creation.

---

## 12. Responsive Rules

### Desktop: `≥ 1024px`

- Landing content maximum width: approximately `1200px`.
- Hero is vertically composed: centered copy above the wide invoice form.
- Major landing sections use `112–160px` vertical separation.
- Authentication may use a restrained split layout, with the form side occupying at least half the usable width.
- Onboarding may use form plus document-preview columns.

### Tablet: `768–1023px`

- Horizontal gutters: `32px`.
- Landing hero form remains wide but simplifies secondary metadata.
- Three-column benefit content may become a two-plus-one grid or stack; avoid narrow text columns.
- Authentication becomes a single centered column.
- Onboarding preview moves beneath the active step if both columns become cramped.

### Mobile: `< 768px`

- Horizontal gutters: `20px`, minimum `16px`.
- Navigation keeps the brand and one clear account action; secondary links move into a compact menu.
- Hero copy is left-aligned or centered consistently; do not mix alignment within the same block.
- Hero CTAs stack at narrow widths and become full-width when needed.
- Invoice demonstration must reflow; it may not use horizontal scrolling as the default experience.
- Landing sections use `64–88px` vertical separation.
- All form controls use the full available width.
- Minimum interactive target: `44×44px`.
- Keep the primary onboarding action visible after the form content, not as a bottom bar that covers fields.
- Respect safe areas and prevent fixed elements from obscuring validation messages.

### Small mobile: `360px`

- No content clipping or horizontal page scroll.
- Long business names and emails wrap or truncate without overlapping controls.
- Password reveal icons remain independently operable.
- Currency, tax, and totals remain readable with tabular numerals.
- The hero form can omit low-priority sample fields but must preserve client, line item, and total.

---

## 13. Form and Validation System

### Field anatomy

Each form field should include:

1. Visible label.
2. Control.
3. Optional helper text.
4. Error message when invalid.

Placeholders are examples, not replacements for labels.

### Validation constraints

- Validate required fields after blur or attempted submission; do not show every field as invalid on initial load.
- Errors should explain how to correct the input.
- Use danger color, text, and an error icon where helpful; never color alone.
- Move focus to the first invalid field after submission and provide an error summary only for long onboarding forms.
- Server errors that are not field-specific appear in a restrained inline alert above the action area.
- Preserve form values after server errors.
- Do not use destructive red styling for ordinary helper text.

### Loading and success

- Keep button widths stable when labels change.
- Disable only the action being processed, not unrelated navigation.
- Use inline spinners or text changes; avoid full-screen loading overlays for form submission.
- Do not announce success solely through color or a disappearing toast.

---

## 14. Accessibility Constraints

- Use semantic `header`, `nav`, `main`, `section`, `form`, and `footer` landmarks.
- Maintain one clear `h1` per screen.
- Provide a skip link on the landing page.
- Every input has a programmatically associated visible label.
- Error messages are associated with their fields using accessible descriptions.
- Keyboard focus uses the shared focus token and remains visible against all surfaces.
- Keyboard order follows visual order.
- Password reveal controls communicate current state.
- Progress in onboarding includes text such as `Step 1 of 2`; do not rely only on a visual bar.
- All text and essential controls meet WCAG AA contrast.
- At 200% text zoom, content reflows without loss of actions or overlap.
- Respect reduced-motion preferences.
- The hero invoice demonstration must not create a confusing set of focusable controls if it is purely illustrative.

---

## 15. States to Design

### Landing page

- Default desktop, tablet, and mobile.
- Mobile navigation open.
- Hero form default and focused state if interactive.
- Hero form recalculated total if interactive.
- Reduced-motion behavior.

### Registration

- Default.
- Field validation errors.
- Email already registered.
- Submitting.
- General server/network error.

### Login

- Default.
- Incorrect credentials.
- Submitting.
- Session-expired message when redirected from a protected screen.
- General server/network error.

### Password recovery, if implemented

- Request form.
- Submitted confirmation.
- Valid reset form.
- Invalid/expired token.
- Successful reset.

### Onboarding

- Step 1 default, partially completed, validation error, and saving.
- Step 2 default, validation error, and saving.
- Logo upload idle, uploading, success, invalid file, and failure.
- Completion state.
- Resume-incomplete-setup state.
- Preview hidden or moved on small screens.

---

## 16. Component Boundaries

```text
PublicExperience
├── LandingPage
│   ├── PublicHeader
│   ├── Hero
│   │   └── InvoiceFormDemo
│   ├── ProblemComparison
│   ├── WorkflowSteps
│   ├── CoreBenefits
│   ├── DocumentChainShowcase
│   ├── FinalCTA
│   └── PublicFooter
├── AuthShell
│   ├── RegisterForm
│   ├── LoginForm
│   ├── ForgotPasswordForm
│   └── ResetPasswordForm
└── OnboardingShell
    ├── OnboardingProgress
    ├── BusinessDetailsStep
    ├── DocumentDefaultsStep
    ├── BusinessDocumentPreview
    └── SetupComplete
```

Extract components around behavior and reuse. Do not create a generic card component for every bordered rectangle or split one-off landing sections into meaningless wrappers.

---

## 17. Implementation Boundaries

### Include

- Responsive landing page.
- Public navigation and footer.
- Invoice-form hero demonstration.
- Registration and login.
- Password recovery screens only when supported end-to-end.
- Two-step business onboarding.
- Loading, validation, error, success, and incomplete-setup states.
- Accessibility and responsive transformations.
- Navigation from registration to onboarding and from completed onboarding to document creation or dashboard.

### Exclude

- Dashboard implementation, which is specified separately.
- Full production quotation/invoice/receipt creation forms inside the landing page.
- Pricing tables until pricing has been defined.
- Fabricated testimonials, client logos, usage counts, or ratings.
- Payment processing, wallets, M-Pesa integration, or payout language.
- Native email or WhatsApp sending unless implemented later.
- Accounting reports, charts, ledgers, inventory, payroll, recurring invoices, tax filing, and eTIMS integration.
- Advanced template builders and unrestricted branding controls.
- Social authentication unless implemented.
- Decorative animations that do not explain product behavior.

---

## 18. Acceptance Checklist

### Landing page

- The first viewport explains connected quotation-to-invoice-to-receipt reuse.
- The hero uses an invoice form rather than a dashboard screenshot.
- The page has visibly generous whitespace at desktop, tablet, and mobile sizes.
- Each major section communicates one primary idea.
- There are no unsupported claims, fabricated social proof, or payment-processing implications.
- The invoice demonstration remains readable at `360px` without desktop-scale shrinking.
- The primary CTA consistently starts account creation.

### Authentication

- Registration asks only for account information.
- Login is shorter than registration and contains no irrelevant marketing clutter.
- Every field has a label, focus state, validation, and accessible error association.
- Loading prevents duplicate requests without blocking unrelated navigation.
- Successful registration enters onboarding.
- Successful login routes according to onboarding completion.
- Non-functional social login, password recovery, and “Remember me” controls are absent.

### Onboarding

- The flow contains no more than two setup steps before completion.
- A freelancer can use a personal name without being forced to present as a registered company.
- Required information is kept minimal.
- Business identity and document defaults are clearly separated.
- Optional logo, tax, and document text do not block progress.
- Currency uses codes rather than flags and does not imply exchange conversion.
- Payment instructions, if present, are clearly document text rather than gateway setup.
- Completion offers `Create your first quotation` as the primary next action.
- Incomplete setup can be resumed without losing saved progress.

### Visual consistency

- Landing, authentication, onboarding, and dashboard share the same colors, typography roles, radii, borders, button hierarchy, focus treatment, and form behavior.
- Landing page is substantially more spacious than the dashboard.
- Authentication is quiet and focused.
- Onboarding is structured but not administrative or accounting-heavy.
- Shadows remain exceptional rather than becoming the default grouping mechanism.

