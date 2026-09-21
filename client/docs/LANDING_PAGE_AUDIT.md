# Landing-page design audit and implementation

Date: 21 September 2026
Branch: feature/landing-page

## Baseline and scope

The frontend worktree initially contained only the server. The existing, untracked React/Vite client and design documents were copied from the main workspace without changing that original client. Dependencies and build output are excluded from Git.

The user approved a landing-page design pass, with authentication outside scope. The formal landing specification governs layout and constraints where content_copy.md differs: four workflow steps and no more than three benefits.

## Changes

| Requirement | Original finding | Implementation |
| --- | --- | --- |
| Shared visual system | Mixed default greens, inconsistent type and spacing | Shared color tokens, warm canvas, 8px controls, 12px surfaces, 48px buttons, responsive gutters and section spacing |
| Public header | Solid informational links, missing Get started, invalid login anchor | Quiet anchor links, account actions, accessible mobile disclosure, Escape/outside-click dismissal |
| Hero | Left-aligned copy, no invoice demonstration | Centered copy, secondary workflow link, wide invoice illustration and workflow cue |
| Invoice demonstration | Missing | Two sample line items, business/client metadata, dates, discount/tax/subtotal/total; totals derived from quantities and rates; mobile stacked layout |
| Problem comparison | Text and unrelated stock photo | Manual versus connected workflow comparison |
| Workflow | Three steps with equal emphasis | Four connected steps, stronger conversion emphasis, vertical mobile sequence |
| Benefits | Four benefit blocks | Three open columns, stacked on mobile |
| Document showcase | Missing | Distinct quotation, invoice and receipt references sharing client/job/amount; recorded-payment clarification and direct-creation note |
| Final CTA/footer | Uncontained CTA, broken links | Accent-soft final section, compact bordered footer, valid anchors |
| Accessibility | Three h1 elements, no main/skip link, non-keyboard menu toggle | One h1, semantic landmarks, skip link, native menu button with expanded state, hidden collapsed navigation, shared focus treatment, reduced-motion rule |
| Starter content | Unused imports/state and generic metadata | Clean app entry, branded title/description/favicon and project README |

## Known acceptance gap

Registration and login routes do not exist. Account buttons are disabled and accompanied by an availability note instead of dead links or simulated account success. This is a design preview, not a launch-ready acquisition funnel. Implement real authentication and onboarding, then enable the account actions, before marking the primary-CTA requirement complete.

## Validation

- ESLint: passed with zero errors (baseline had nine).
- Production Vite build: passed.
- Sample calculation: 24,000 + 3 × 6,000 = 42,000 subtotal; minus 2,000 discount; 16% tax = 6,400; total = KES 46,400.00.
- Source review: mobile reflow at the 767px breakpoint; tablet rules through 1023px; semantic focus/menu handling; reduced-motion override.
- Browser QA could not run: browser inventory was empty and the browser tool returned “No browser is available.” Desktop/tablet/360px screenshots, keyboard interactions, 200% text zoom, and rendered contrast/overflow remain unverified. Source rules are not a substitute for those checks.

## Local environment notes

A dependency copy ran out of disk space and was removed. The frontend worktree currently uses an ignored node_modules junction to the existing main-workspace dependencies. A fresh checkout should run npm ci normally.

The Sites build wrapper failed to locate npm on this Windows setup; the project's own npm.cmd run build completed successfully. No deployment or backend changes were made.

Additional checks: local HTTP response 200; server-rendered React smoke check passed for exactly one h1, KES 46,400.00 total, valid fragment targets, and hidden collapsed navigation. These checks do not verify browser layout or interactions.
