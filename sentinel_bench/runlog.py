"""Run-log helpers. One JSON object per line, newline-terminated.

The event dataclasses below are the schema of record. ``docs/schema.md`` is generated
from them, so a field added here is a documentation change too.

A run that is killed mid-write leaves a truncated final line. :func:`read_records` is the
record-safe reader every consumer should use; :func:`iter_events` is the strict one and
raises on a bad line.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RunStarted:
    """A run begins. Emitted once, first line of the log."""

    run_id: str
    """Stable id of this run, unique across the suite."""
    ts: str
    """ISO-8601 UTC timestamp."""
    suite: str
    """Suite name the run belongs to."""
    families: list[str] = field(default_factory=list)
    """Family codes selected for this run."""


@dataclass(frozen=True)
class TaskResult:
    """One attempt at one task."""

    run_id: str
    """Run this attempt belongs to."""
    task_id: str
    """Task id, ``<family>/<slug>``."""
    attempt: int
    """1-based attempt number within the run."""
    ts: str
    """ISO-8601 UTC timestamp of completion."""
    status: str
    """One of ``ok``, ``failed``, ``skipped``, ``error``."""
    score: float
    """Grader score in [0, 1]."""
    notes: str | None = None
    """Optional free text from the grader."""


@dataclass(frozen=True)
class RunFinished:
    """A run ends. Emitted once, last line of the log."""

    run_id: str
    """Run that finished."""
    ts: str
    """ISO-8601 UTC timestamp."""
    n_tasks: int
    """How many task results the run emitted."""
    wall_s: float
    """Wall-clock seconds from start to finish."""


EVENT_TYPES = {"run_started": RunStarted, "task_result": TaskResult, "run_finished": RunFinished}


def iter_events(path):
    """Yield every record in ``path``. Strict: a malformed line raises."""
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_records(path):
    """Record-safe reader: yields every COMPLETE record and ignores a truncated tail.

    A killed run leaves a partial final line. Dropping it silently is correct; crashing
    on it means one dead run poisons every report built over the log.
    """
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def last_events(path, n):
    """The last ``n`` complete records, oldest-first.

    Reads the whole file. That is fine for the 2 MB smoke logs and painful for the big
    ones; see the note in docs/schema.md.
    """
    records = list(read_records(path))
    return records[-n:] if n > 0 else []


def main(argv=None):
    """``python -m sentinel_bench.runlog`` -- inspect a run log."""
    parser = argparse.ArgumentParser(prog="sentinel_bench.runlog",
                                     description="inspect a sentinel-bench run log")
    parser.add_argument("path", help="path to a .jsonl run log")
    parser.add_argument("--type", default=None, help="only show records of this type")
    parser.add_argument("--count", action="store_true", help="print a per-type count and exit")
    args = parser.parse_args(argv)

    records = list(read_records(args.path))
    if args.count:
        counts: dict[str, int] = {}
        for record in records:
            counts[record.get("type", "?")] = counts.get(record.get("type", "?"), 0) + 1
        for name in sorted(counts):
            print(f"{name}\t{counts[name]}")
        return 0
    for record in records:
        if args.type and record.get("type") != args.type:
            continue
        print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
