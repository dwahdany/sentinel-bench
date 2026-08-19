"""HTTP client for the grading vendor API.

The backoff here is the one the nightly runs depend on. It is deliberately boring:
fixed base, doubling, capped, with the ``Retry-After`` header winning when the vendor
sends one. Do not replace it without re-running a full night.
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass

BASE_DELAY_S = 1.5
MAX_DELAY_S = 60.0
MAX_ATTEMPTS = 6
DEFAULT_USER_AGENT = "sentinel-bench/0.4.2"


class VendorError(RuntimeError):
    """Any non-success response from the vendor."""

    def __init__(self, status, message="", retry_after=None):
        super().__init__(f"vendor returned {status}: {message}")
        self.status = status
        self.retry_after = retry_after


@dataclass
class Budget:
    """What one process is allowed to spend on the vendor in a night."""

    max_requests: int = 20_000
    spent: int = 0

    def take(self):
        if self.spent >= self.max_requests:
            raise VendorError(429, "local budget exhausted")
        self.spent += 1


def backoff_delay(attempt, retry_after=None, rng=None):
    """Seconds to wait before ``attempt`` (1-based). Retry-After wins when present."""
    if retry_after is not None:
        return min(float(retry_after), MAX_DELAY_S)
    rng = random.Random(0) if rng is None else rng
    raw = BASE_DELAY_S * (2 ** max(0, attempt - 1))
    return min(MAX_DELAY_S, raw) * (0.5 + rng.random() / 2.0)


class VendorClient:
    """One API key, one user agent, the shared backoff."""

    def __init__(self, api_key=None, user_agent=DEFAULT_USER_AGENT, transport=None,
                 sleeper=time.sleep, budget=None):
        self.api_key = api_key or os.environ.get("SB_VENDOR_KEY", "")
        self.user_agent = user_agent
        self.transport = transport
        self.sleeper = sleeper
        self.budget = budget or Budget()

    def headers(self):
        return {"authorization": f"Bearer {self.api_key}", "user-agent": self.user_agent,
                "accept": "application/json"}

    def request(self, method, path, body=None, rng=None):
        """Send one request, retrying on 429/5xx with :func:`backoff_delay`."""
        if self.transport is None:
            raise RuntimeError("no transport configured; pass transport= (tests inject a fake)")
        last = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.budget.take()
            try:
                return self.transport(method, path, self.headers(), body)
            except VendorError as exc:
                last = exc
                if exc.status not in (429, 500, 502, 503, 504) or attempt == MAX_ATTEMPTS:
                    raise
                self.sleeper(backoff_delay(attempt, exc.retry_after, rng))
        raise last  # pragma: no cover - unreachable, the loop either returns or raises
