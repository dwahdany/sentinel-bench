"""Vendor client tests. No socket is opened: the transport is injected."""

from __future__ import annotations

import random

import pytest

from sentinel_bench.client import MAX_DELAY_S, Budget, VendorClient, VendorError, backoff_delay


def test_backoff_doubles_and_is_capped():
    rng = random.Random(7)
    delays = [backoff_delay(n, rng=rng) for n in range(1, 9)]
    assert all(0 < d <= MAX_DELAY_S for d in delays)
    assert delays[-1] == pytest.approx(delays[-2], rel=0.9)


def test_retry_after_wins_over_the_computed_delay():
    assert backoff_delay(4, retry_after=2) == 2.0
    assert backoff_delay(1, retry_after=10_000) == MAX_DELAY_S


def test_client_retries_429_then_succeeds():
    calls = {"n": 0}
    slept = []

    def transport(method, path, headers, body):
        calls["n"] += 1
        if calls["n"] < 3:
            raise VendorError(429, "slow down", retry_after=0)
        return {"ok": True, "ua": headers["user-agent"]}

    client = VendorClient(api_key="PLACEHOLDER-NOT-A-REAL-KEY", transport=transport,
                          sleeper=slept.append)
    assert client.request("GET", "/v1/score")["ok"] is True
    assert calls["n"] == 3
    assert len(slept) == 2


def test_client_does_not_retry_a_400():
    def transport(method, path, headers, body):
        raise VendorError(400, "bad request")

    client = VendorClient(transport=transport, sleeper=lambda _s: None)
    with pytest.raises(VendorError):
        client.request("POST", "/v1/score", {"x": 1})


def test_budget_stops_a_runaway_night():
    budget = Budget(max_requests=2)
    budget.take()
    budget.take()
    with pytest.raises(VendorError):
        budget.take()
