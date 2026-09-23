# Release QA checklist

Phase 14 validates the implemented frontend against the product direction. Automated tests run without a backend by using deterministic preview stores and mocked API responses. Developer preview requires `VITE_AUTH_PREVIEW=true` in development.

## Automated checks

From `client/invoice-client`:

```sh
npm.cmd run lint
npm.cmd test
npm.cmd run test:coverage
npm.cmd run build
```

The automated suite covers onboarding-to-quotation setup, quotation-to-invoice-to-receipt relationships, direct invoice and receipt editing, session refresh coordination, session expiry cleanup, error contracts, financial rounding, safe PDF filenames, internal redirects, and landing account actions.

## Developer preview routes

- `/`
- `/register`
- `/login`
- `/onboarding/business`
- `/onboarding/defaults`
- `/dashboard`
- `/documents`
- `/clients`
- `/settings/business`
- `/settings/account`
- `/documents/quotations/new`
- `/documents/invoices/new`
- `/documents/receipts/new`

## Manual responsive and accessibility pass

Verify the landing page, dashboard, clients, documents, settings, and each document canvas at 1440px, 1024px, 768px, 390px, and 360px. There must be no horizontal page scroll, clipped actions, or inaccessible dialogs.

Check keyboard navigation for skip links, mobile navigation, account menus, form errors, client selectors, line-item controls, action menus, dialogs, and route focus. Confirm one meaningful `h1` per page, labelled controls, visible focus, live loading/error states, and sensible reading order.

At 200% zoom, use long business names, client names, emails, document numbers, notes, and large amounts. Confirm text wraps without hiding actions or changing persisted totals.

## Security and product boundaries

Confirm tokens never appear in URLs, page copy, logs, or document links; external `next` values are rejected; PDF filenames remain safe; logout clears local session and owner-scoped cache; and the product does not claim to send documents, process payments, provide password recovery, or perform currency conversion.

## Known limitation

The repository does not currently include Playwright or Cypress. Responsive, screen-reader, and visual checks above remain a manual browser QA pass until a browser automation dependency and CI environment are approved.
