#!/usr/bin/env python3
"""Run one task family and append its results to a run log.

    uv run python scripts/run_family.py --family II.C --attempts 3

This is the driver the nightly cron calls. It does not build containers; it assumes the
family's compose overlay is already up and it records what the graders return.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentinel_bench import report, runlog  # noqa: E402

FAMILIES = ("II.A", "II.B", "II.C", "II.D", "III.A", "IV.A")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main(argv=None):
    parser = argparse.ArgumentParser(description="run one task family")
    parser.add_argument("--family", required=True, choices=FAMILIES)
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    run_id = f"run-{uuid.uuid4().hex[:4]}"
    os.makedirs(args.runs_dir, exist_ok=True)
    path = os.path.join(args.runs_dir, f"{time.strftime('%Y-%m-%d', time.gmtime())}-{run_id}.jsonl")
    lines = [{"type": "run_started", "run_id": run_id, "ts": now(),
              "suite": "sentinel-bench", "families": [args.family]}]
    for attempt in range(1, args.attempts + 1):
        lines.append({"type": "task_result", "run_id": run_id,
                      "task_id": f"{args.family}/placeholder", "attempt": attempt,
                      "ts": now(), "status": "skipped", "score": 0.0,
                      "notes": "no grader wired for this family yet"})
    lines.append({"type": "run_finished", "run_id": run_id, "ts": now(),
                  "n_tasks": args.attempts, "wall_s": 0.0})

    if args.dry_run:
        print(json.dumps(lines, indent=2))
        return 0
    with open(path, "w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(json.dumps(line, sort_keys=True) + "\n")
    records = list(runlog.read_records(path))
    print(f"{path}: {len(records)} records, pass rate {report.pass_rate(records):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
