"""The offline detection-rule engine.

Rules live in ``rules/detection-rules.json``. Each rule is a regex over the decoded
payload text plus a severity and a family the rule belongs to. Matching is done over
recorded captures only: this module never opens a socket, and nothing may be added here
that does.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from urllib.parse import unquote_plus

DEFAULT_RULES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "rules", "detection-rules.json")


@dataclass(frozen=True)
class Rule:
    """One detection rule."""

    id: str
    name: str
    family: str
    severity: str
    pattern: str

    @property
    def regex(self):
        return re.compile(self.pattern, re.IGNORECASE)


@dataclass(frozen=True)
class Hit:
    """A rule that fired on a packet."""

    rule_id: str
    packet_index: int
    excerpt: str


def load_rules(path=None):
    """Load the ruleset. Returns rules in file order, which is the reporting order."""
    with open(path or DEFAULT_RULES, encoding="utf-8") as handle:
        payload = json.load(handle)
    return [Rule(**row) for row in payload["rules"]]


def normalise(text):
    """The forms a rule is matched against: the bytes as recorded, and percent-decoded.

    Query strings arrive encoded (``or%201%3D1``), so a rule written over the readable
    form would silently never fire. Decoding once here beats writing every rule twice.
    """
    decoded = unquote_plus(text)
    return (text,) if decoded == text else (text, decoded)


def match_packet(packet, rules):
    """Every rule that fires on one packet."""
    forms = normalise(packet.text)
    hits = []
    for rule in rules:
        for form in forms:
            found = rule.regex.search(form)
            if found:
                hits.append(Hit(rule_id=rule.id, packet_index=packet.index,
                                excerpt=found.group(0)[:60]))
                break
    return hits


def replay(packets, rules=None):
    """Replay an iterable of packets through the ruleset. -> list[Hit], in packet order."""
    rules = load_rules() if rules is None else rules
    hits = []
    for packet in packets:
        hits.extend(match_packet(packet, rules))
    return hits


def fired_rule_ids(packets, rules=None):
    """The set of rule ids that fired, which is what a regression test asserts over."""
    return sorted({hit.rule_id for hit in replay(packets, rules)})
