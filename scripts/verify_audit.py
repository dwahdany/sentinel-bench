#!/usr/bin/env python3
"""Verify out/audit/manifest.json against the audit files on disk.

    uv run python scripts/verify_audit.py

Exits non-zero when a checksum does not match. The manifest is what the review queue
trusts, so a mismatch means either a file was edited in place -- which the append-only
rule forbids -- or the manifest is stale.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.grade_common import sha256_file  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="verify the audit manifest")
    parser.add_argument("--audit-dir", default="out/audit")
    args = parser.parse_args(argv)

    manifest_path = os.path.join(args.audit_dir, "manifest.json")
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)

    bad = 0
    for name, entry in sorted(manifest["files"].items()):
        path = os.path.join(args.audit_dir, name)
        if not os.path.exists(path):
            print(f"MISSING  {name}")
            bad += 1
            continue
        actual = sha256_file(path)
        if actual != entry["sha256"]:
            print(f"MISMATCH {name}\n  manifest {entry['sha256']}\n  on disk  {actual}")
            bad += 1
        else:
            print(f"ok       {name}  {entry['records']} records")
    if bad:
        print(f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
