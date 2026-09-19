"""Conservative monotonic rate limiting for Settrade requests."""

from __future__ import annotations

import threading
import time


class RateLimiter:
    """Token-spacing limiter; it never intentionally tests a server limit."""

    def __init__(self, requests_per_second: float = 3.0, clock=time.monotonic) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        self.requests_per_second = float(requests_per_second)
        self._interval = 1.0 / self.requests_per_second
        self._clock = clock
        self._next_allowed = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> float:
        """Wait until a request is allowed and return the wait duration."""
        with self._lock:
            now = self._clock()
            wait = max(0.0, self._next_allowed - now)
            if wait:
                time.sleep(wait)
                now = self._clock()
            self._next_allowed = max(self._next_allowed, now) + self._interval
            return wait
