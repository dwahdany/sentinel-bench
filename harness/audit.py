"""Audit records for every run, and the shipper that forwards them.

Every run appends one record per task to ``out/audit/<YYYY-MM>.jsonl`` and the shipper
forwards new records to the review queue. The manifest at ``out/audit/manifest.json``
carries a sha256 per audit file; ``scripts/verify_audit.py`` checks it.

The audit log is append-only. Records are not edited in place and not deleted: a wrong
record is corrected by appending a `correction` record that references it by
``record_id``. That is what the verifier and the review queue both assume.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass

AUDIT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "out", "audit")
SHIPPING_ENABLED = True
SHIP_ENDPOINT = "https://review-queue.internal/api/audit"
SHIP_BATCH = 200


@dataclass(frozen=True)
class AuditRecord:
    """One audited task outcome."""

    record_id: str
    run_id: str
    task_id: str
    ts: str
    status: str
    score: float
    operator: str


def month_path(ts=None, audit_dir=None):
    stamp = time.strftime("%Y-%m", time.gmtime(ts))
    return os.path.join(audit_dir or AUDIT_DIR, f"{stamp}.jsonl")


def append(record, audit_dir=None):
    """Append one record. The only write path into the audit log."""
    path = month_path(audit_dir=audit_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")
    return path


def correct(record_id, reason, operator, audit_dir=None):
    """Append a correction that supersedes ``record_id``. Never edits the original."""
    path = month_path(audit_dir=audit_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "correction", "supersedes": record_id,
                                 "reason": reason, "operator": operator,
                                 "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                                sort_keys=True) + "\n")
    return path


def pending(path):
    """Records not yet marked shipped."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        rows = []
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not record.get("shipped"):
                rows.append(record)
        return rows


def ship(path, transport=None):
    """Forward pending records to the review queue in batches of SHIP_BATCH.

    Returns the number of records forwarded. With shipping disabled this returns 0 and
    says so -- it does not silently succeed, because a quiet queue looks identical to a
    clean night on the dashboard.
    """
    if not SHIPPING_ENABLED:
        return {"shipped": 0, "reason": "shipping disabled in harness/audit.py"}
    rows = pending(path)
    if transport is None:
        return {"shipped": 0, "reason": "no transport configured"}
    for start in range(0, len(rows), SHIP_BATCH):
        transport(SHIP_ENDPOINT, rows[start:start + SHIP_BATCH])
    return {"shipped": len(rows), "reason": ""}
