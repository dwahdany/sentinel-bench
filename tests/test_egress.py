"""The II.B egress module only ever traces the lab bridge or loopback."""

from __future__ import annotations

import json

import pytest

from sentinel_bench import egress


def test_lab_bridge_and_loopback_are_allowed():
    assert egress.is_allowed("10.42.0.11")
    assert egress.is_allowed("127.0.0.1")


def test_everything_else_is_refused():
    assert not egress.is_allowed("203.0.113.9")
    with pytest.raises(egress.TargetNotAllowed):
        egress.check_target("203.0.113.9")


def test_trace_writes_jsonl(tmp_path):
    event = egress.EgressEvent(run_id="run-9001", task_id="II.B/loopback",
                               ts="2026-08-05T22:00:00Z", target="127.0.0.1", port=8080,
                               bytes_out=512, verdict="allowed")
    out = egress.trace([event], str(tmp_path / "egress.jsonl"))
    line = json.loads(open(out, encoding="utf-8").read().strip())
    assert line["type"] == "egress" and line["target"] == "127.0.0.1"


def test_the_host_manifest_only_lists_bridge_addresses():
    for host in egress.load_hosts()["hosts"]:
        assert egress.is_allowed(host["address"]), host
