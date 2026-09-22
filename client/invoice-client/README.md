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

The API client owns JSON envelopes, backend errors, bearer-token attachment, access-token refresh, and PDF/blob responses. It uses browser session storage for the current token pair and keeps PostgreSQL access entirely behind the backend API. The authentication provider bootstraps `/auth/me` and `/business-profile`, then exposes anonymous, onboarding-required, and ready session states to the route guards.

## Current scope

- Responsive public navigation, landing sections and footer.
- Illustrative invoice, with totals calculated from sample data. It is not an editable production form.
- Registration and login are connected to the backend API, including client-side validation, duplicate-email and invalid-credential handling, safe protected-route redirects, onboarding detection, logout, and session-expiration recovery.
- No backend calls, payment processing, uploads or document generation are implemented by this page.

Password recovery, file uploads, payment processing, and document generation remain backend-dependent feature work. The API layer does not invent endpoints for them. Onboarding screens remain placeholders until the next feature phase.

See `../docs/LANDING_PAGE_AUDIT.md` for changes and validation status.
