"""Small, bounded request rate limiter for security-sensitive endpoints.

The limiter is intentionally process-local. Deployments with more than one
application process must also enforce the same limits at their edge or use a
shared store; see the backend rate-limiting notes.
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable

from fastapi import Request

from app.common.errors import DomainError


@dataclass(frozen=True)
class RateLimitSettings:
    window_seconds: int = 60
    auth_limit: int = 10
    refresh_limit: int = 60
    pdf_limit: int = 30
    max_keys: int = 10_000


class RateLimiter:
    """Thread-safe sliding-window limiter with bounded memory."""

    def __init__(
        self,
        settings: RateLimitSettings | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings or RateLimitSettings()
        self._clock = clock
        self._events: dict[tuple[str, str], deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, bucket: str, key: str) -> None:
        limit = self._limit_for(bucket)
        now = self._clock()
        cutoff = now - self.settings.window_seconds
        event_key = (bucket, key)

        with self._lock:
            events = self._events.get(event_key)
            if events is None:
                if len(self._events) >= self.settings.max_keys:
                    self._evict_oldest()
                events = deque()
                self._events[event_key] = events
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, math.ceil(events[0] + self.settings.window_seconds - now))
                raise DomainError(
                    "RATE_LIMIT_EXCEEDED",
                    "Too many requests. Please try again later.",
                    status_code=429,
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )
            events.append(now)

    def _limit_for(self, bucket: str) -> int:
        if bucket == "auth":
            return self.settings.auth_limit
        if bucket == "refresh":
            return self.settings.refresh_limit
        if bucket == "pdf":
            return self.settings.pdf_limit
        raise ValueError(f"Unknown rate-limit bucket: {bucket}")

    def _evict_oldest(self) -> None:
        oldest_key = min(
            self._events,
            key=lambda key: self._events[key][-1] if self._events[key] else float("-inf"),
        )
        del self._events[oldest_key]


def request_rate_limit_key(request: Request) -> str:
    """Return the directly observed peer address; proxy headers are untrusted."""

    return request.client.host if request.client else "unknown"


def rate_limit(bucket: str):
    """Build a FastAPI dependency for a named limiter bucket."""

    def dependency(request: Request) -> None:
        limiter: RateLimiter = request.app.state.rate_limiter
        limiter.check(bucket, request_rate_limit_key(request))

    return dependency
