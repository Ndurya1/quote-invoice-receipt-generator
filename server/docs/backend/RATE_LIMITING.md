# Rate limiting

The API applies a sliding-window limit by directly observed client address to
registration, login, refresh-token, and PDF-generation endpoints. The default
limits are:

- Authentication endpoints: 10 requests per 60 seconds.
- Refresh-token endpoint: 60 requests per 60 seconds.
- PDF endpoints: 30 requests per 60 seconds.

Limits can be changed with `RATE_LIMIT_WINDOW_SECONDS`,
`AUTH_RATE_LIMIT_PER_WINDOW`, `PDF_RATE_LIMIT_PER_WINDOW`, and
`REFRESH_RATE_LIMIT_PER_WINDOW`, and `RATE_LIMIT_MAX_KEYS`. Values must be
positive integers.

When a limit is exceeded, the API returns the normal error envelope with code
`RATE_LIMIT_EXCEEDED`, status `429`, and a `Retry-After` header. Proxy headers
such as `X-Forwarded-For` are not trusted by the application, preventing a
client from bypassing the limiter by supplying a forged address.

The current limiter is process-local and bounded in memory. A multi-worker or
multi-instance production deployment must additionally enforce equivalent
limits at its trusted edge, or replace the in-process store with a shared
store such as Redis, so requests cannot bypass limits by reaching another
worker.
