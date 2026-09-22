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

## API configuration

The frontend talks to the backend through `/api/v1` by default. Set `VITE_API_BASE_URL` when the API is hosted at another origin:

```sh
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

The API client owns JSON envelopes, backend errors, bearer-token attachment, access-token refresh, and PDF/blob responses. It uses browser session storage for the current token pair and keeps PostgreSQL access entirely behind the backend API.

## Current scope

- Responsive public navigation, landing sections and footer.
- Illustrative invoice, with totals calculated from sample data. It is not an editable production form.
- Account actions are visibly disabled with an availability note. Registration, login and onboarding are not implemented in this design pass, so the account-creation acceptance criterion is outstanding.
- No backend calls, payment processing, uploads or document generation are implemented by this page.

Password recovery, file uploads, payment processing, and document generation remain backend-dependent feature work. The API layer does not invent endpoints for them.

See `../docs/LANDING_PAGE_AUDIT.md` for changes and validation status.
