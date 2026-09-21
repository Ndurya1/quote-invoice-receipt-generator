# DocuFlow client

React, Vite, Tailwind CSS and React Router landing page for connected quotations, invoices and receipts.

## Local development

From `client/invoice-client`:

```sh
npm ci
npm run dev
npm run lint
npm run build
```

On Windows PowerShell with script execution disabled, use `npm.cmd` instead of `npm`.

The public landing page is `/`. Design requirements live in `../docs/LANDING_AUTH_ONBOARDING_DESIGN_SPEC.md`, with shared tokens in `../docs/DASHBOARD_DESIGN_SPEC.md`. The formal specification takes precedence over conflicting draft copy.

## Current scope

- Responsive public navigation, landing sections and footer.
- Illustrative invoice, with totals calculated from sample data. It is not an editable production form.
- Account actions are visibly disabled with an availability note. Registration, login and onboarding are not implemented in this design pass, so the account-creation acceptance criterion is outstanding.
- No backend calls, payment processing, uploads or document generation are implemented by this page.

See `../docs/LANDING_PAGE_AUDIT.md` for changes and validation status.
