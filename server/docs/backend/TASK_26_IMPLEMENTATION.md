# Task 26 — End-to-End Verification

Implemented through five independently committed workflow audits:

- `test(e2e): cover first user quote workflow`
- `test(e2e): cover full document lifecycle`
- `test(e2e): cover direct invoice workflow`
- `test(e2e): cover direct receipt workflow`
- `test(e2e): cover financial tampering cases`

The integration tests exercise the public HTTP API against isolated PostgreSQL
schemas. They cover registration, authentication, business setup, direct and
converted document flows, persisted totals, independent numbering, lineage,
PDF downloads, and rejected financial or cross-tenant requests without partial
persistence.
