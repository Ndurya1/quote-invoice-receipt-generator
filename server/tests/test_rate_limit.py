import unittest

from app.common.errors import DomainError
from app.common.rate_limit import RateLimitSettings, RateLimiter


class RateLimiterTests(unittest.TestCase):
    def test_blocks_after_limit_and_reports_retry_after(self):
        now = [100.0]
        limiter = RateLimiter(
            RateLimitSettings(window_seconds=60, auth_limit=2, refresh_limit=3, pdf_limit=3, max_keys=10),
            clock=lambda: now[0],
        )
        limiter.check("auth", "client")
        limiter.check("auth", "client")
        with self.assertRaises(DomainError) as raised:
            limiter.check("auth", "client")
        self.assertEqual(raised.exception.code, "RATE_LIMIT_EXCEEDED")
        self.assertEqual(raised.exception.status_code, 429)
        self.assertEqual(raised.exception.headers["Retry-After"], "60")
        self.assertEqual(raised.exception.headers["X-RateLimit-Remaining"], "0")

    def test_window_expiry_allows_requests_again(self):
        now = [100.0]
        limiter = RateLimiter(RateLimitSettings(auth_limit=1), clock=lambda: now[0])
        limiter.check("auth", "client")
        now[0] = 160.001
        limiter.check("auth", "client")

    def test_key_tracking_is_bounded(self):
        limiter = RateLimiter(RateLimitSettings(max_keys=2), clock=lambda: 100.0)
        limiter.check("auth", "one")
        limiter.check("auth", "two")
        limiter.check("auth", "three")
        self.assertLessEqual(len(limiter._events), 2)

    def test_unknown_bucket_is_rejected(self):
        with self.assertRaises(ValueError):
            RateLimiter().check("unknown", "client")
