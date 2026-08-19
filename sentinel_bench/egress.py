"""The II.B egress module: record what a task container tries to send.

Targets are resolved from ``tasks/_shared/hosts.json`` and the module refuses anything
that is not on the lab bridge or loopback. A family that needs a different target adds
it to the manifest with an owner; it does not get pointed at an address by hand.
"""

from __future__ import annotations

import ipaddress
import json
import os
from dataclasses import asdict, dataclass

HOSTS_MANIFEST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "tasks", "_shared", "hosts.json")
#: The only networks this module will trace against. Both are non-routable by design.
ALLOWED_NETS = ("127.0.0.0/8", "10.42.0.0/24")


class TargetNotAllowed(PermissionError):
    """Raised when a trace is requested against something off the lab bridge."""


@dataclass(frozen=True)
class EgressEvent:
    """One recorded egress attempt."""

    run_id: str
    task_id: str
    ts: str
    target: str
    port: int
    bytes_out: int
    verdict: str


def load_hosts(path=None):
    with open(path or HOSTS_MANIFEST, encoding="utf-8") as handle:
        return json.load(handle)


def is_allowed(address):
    """True when ``address`` is inside :data:`ALLOWED_NETS`."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(ip in ipaddress.ip_network(net) for net in ALLOWED_NETS)


def check_target(address):
    if not is_allowed(address):
        raise TargetNotAllowed(
            f"{address} is not on the lab bridge; add it to tasks/_shared/hosts.json with an "
            "owner, or run against loopback")
    return address


def trace(events, out_path):
    """Write recorded :class:`EgressEvent` objects as JSONL. Targets are checked first."""
    for event in events:
        check_target(event.target)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps({"type": "egress", **asdict(event)}, sort_keys=True) + "\n")
    return out_path
