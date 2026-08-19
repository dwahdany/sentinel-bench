"""Run-log helpers. Normally one JSON object per line, newline-terminated.

The event dataclasses below are the schema of record. ``docs/schema.md`` is generated
from them, so a field added here is a documentation change too.

Both readers parse by *record*, not by line: a record whose JSON is pretty-printed
across several lines is read as one record, and several records on one line are read as
several. Our own writers still emit one compact object per line; the tolerance is for
logs that reach us from elsewhere.

A run that is killed mid-write leaves a truncated final record. :func:`read_records` is
the record-safe reader every consumer should use; :func:`iter_events` is the strict one
and raises on malformed input.
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


_DECODER = json.JSONDecoder()


def _could_continue(buffer, err):
    """True if ``buffer`` is a proper prefix of some valid JSON value.

    Distinguishes "this record is not finished yet" (keep buffering the next line) from
    "this text can never parse" (a torn write; resync). Getting it wrong in the first
    direction splits one record in two; wrong in the second direction makes a torn line
    swallow every record after it, so both are checked against real prefixes in
    ``tests/test_runlog.py``.

    An unterminated string is always a cut-off record. Otherwise the buffer is a prefix
    only if the decoder ran out of input, i.e. it failed at the very end of the text
    rather than at some earlier byte it could not make sense of.
    """
    if err.msg.startswith("Unterminated string"):
        return True
    return err.msg.startswith("Expecting") and err.pos >= len(buffer.rstrip())


def _scan(handle, strict):
    """Yield records from ``handle``, buffering lines until each record is complete.

    ``strict`` raises on malformed input; otherwise a torn record is dropped and reading
    resumes at the next line.
    """
    pending = ""
    pending_err = None
    for line in handle:
        pending += line
        while True:
            start = len(pending) - len(pending.lstrip())
            if start == len(pending):  # blank or whitespace only
                pending = ""
                break
            try:
                record, end = _DECODER.raw_decode(pending, start)
            except json.JSONDecodeError as err:
                if _could_continue(pending, err):
                    pending_err = err  # may still be completed by a later line
                    break
                if strict:
                    raise
                newline = pending.find("\n", start)
                if newline < 0:
                    pending = ""
                    break
                pending = pending[newline + 1:]  # resync on the next line
                continue
            yield record
            pending = pending[end:]
    if pending.strip() and strict:
        raise pending_err  # ran out of input mid-record


def iter_events(path):
    """Yield every record in ``path``. Strict: malformed input raises.

    Includes a truncated final record: for this reader a cut-off log is an error.
    """
    with open(path, encoding="utf-8") as handle:
        yield from _scan(handle, strict=True)


def read_records(path):
    """Record-safe reader: yields every COMPLETE record and ignores a truncated tail.

    A killed run leaves a partial final record. Dropping it silently is correct; crashing
    on it means one dead run poisons every report built over the log. A torn record
    mid-file is likewise skipped, and the records after it are still read.
    """
    with open(path, encoding="utf-8") as handle:
        yield from _scan(handle, strict=False)


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
