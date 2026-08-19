"""Unit tests for the offline rule engine. The full capture replay lives in harness/."""

from __future__ import annotations

import json

from sentinel_bench import pcap, rules


def test_ruleset_ids_are_unique_and_stable():
    loaded = rules.load_rules()
    ids = [rule.id for rule in loaded]
    assert ids == sorted(ids)
    assert len(set(ids)) == len(ids)


def test_negative_control_capture_fires_nothing(captures_dir):
    packets = list(pcap.read_packets(captures_dir / "dns-noise.pcap"))
    assert packets
    assert rules.fired_rule_ids(packets) == []


def test_sqli_capture_fires_its_sidecar_rules(captures_dir):
    expected = json.loads((captures_dir / "http-sqli.expected.json").read_text(encoding="utf-8"))
    packets = list(pcap.read_packets(captures_dir / "http-sqli.pcap"))
    assert rules.fired_rule_ids(packets) == expected["rules"]


def test_percent_encoded_payloads_still_fire():
    assert rules.normalise("q=or%201%3D1")[1] == "q=or 1=1"
    assert len(rules.normalise("q=plain")) == 1


def test_reader_rejects_a_file_that_is_not_a_capture(tmp_path):
    bad = tmp_path / "notes.txt"
    bad.write_text("this is not a capture", encoding="utf-8")
    try:
        list(pcap.read_packets(bad))
    except pcap.PcapError:
        return
    raise AssertionError("a non-capture file must raise PcapError")
