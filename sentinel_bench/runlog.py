"""Run-log helpers. Normally one JSON object per line, newline-terminated.

The event dataclasses below are the schema of record. ``docs/schema.md`` is generated
from them, so a field added here is a documentation change too.

Both readers parse by *record*, not by line: a record whose JSON is pretty-printed
across several lines is read as one record, and several records on one line are read as
several. Our own writers still emit one compact object per line; the tolerance is for
logs that reach us from elsewhere.

A run that is killed mid-write leaves a truncated final record. :func:`read_records` is
the record-safe reader every consumer should use: it drops the truncated tail, and drops
a torn record mid-file without losing the records after it. :func:`iter_events` is the
strict one and raises :class:`RunLogDecodeError`, which names the file and the line the
bad record starts on.

Every record is a JSON object. Both readers enforce it, which is what keeps the fragments
of a torn record from being mistaken for records of their own.
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


class RunLogDecodeError(json.JSONDecodeError):
    """A record in a run log could not be read.

    Subclasses :class:`json.JSONDecodeError` so callers that already catch that keep
    working, but carries the *file* path and line rather than an offset into whatever
    buffer the reader happened to be holding, because "line 3 column 5" of a buffered
    record is useless when you are looking for the problem in a 40 MB log.
    """

    def __init__(self, message, doc, pos, lineno, colno):
        ValueError.__init__(self, message)
        self.msg = message
        self.doc = doc
        self.pos = pos
        self.lineno = lineno
        self.colno = colno

    def __reduce__(self):
        return (self.__class__, (self.msg, self.doc, self.pos, self.lineno, self.colno))


def _could_continue(buffer, err):
    """True if ``buffer`` is a proper prefix of some valid JSON value.

    Distinguishes "this record is not finished yet" (keep buffering the next line) from
    "this text can never parse" (a torn write; resync). Getting it wrong in the first
    direction splits one record in two; wrong in the second direction makes a torn line
    swallow every record after it, so both are checked against real prefixes in
    ``tests/test_runlog.py``.

    An unterminated string is always a cut-off record. A string the writer died inside
    *after* the newline reached the buffer reports ``Invalid control character`` instead,
    and that is deliberately NOT treated as a prefix: it is indistinguishable from a torn
    record mid-file, and calling it a prefix would buffer -- and so swallow -- every
    record after it. The object guard in :func:`_scan` is what stops the fragments of such
    a record from being mistaken for records. Otherwise the buffer is a prefix only if the
    decoder ran out of input, i.e. it failed at the very end of the text rather than at
    some earlier byte it could not make sense of.
    """
    if err.msg.startswith("Unterminated string"):
        return True
    return err.msg.startswith("Expecting") and err.pos >= len(buffer.rstrip())


def _position(buffer, start_line, pos):
    """Map an offset in ``buffer`` to a 1-based (line, column) in the file."""
    pos = min(pos, len(buffer))
    line = start_line + buffer.count("\n", 0, pos)
    column = pos - (buffer.rfind("\n", 0, pos) + 1) + 1
    return line, column


def _error(reason, err, path, buffer, start_line, pos):
    """Build a :class:`RunLogDecodeError` that says where in the file to look."""
    line, column = _position(buffer, start_line, pos)
    where = f"{path}:{line}" if path else f"line {line}"
    detail = f": {err.msg}" if err is not None else ""
    message = f"{where} column {column}: {reason} (record starts at line {start_line}){detail}"
    return RunLogDecodeError(message, buffer, pos, line, column)


def _scan(handle, strict, path=None):
    """Yield records from ``handle``, buffering lines until each record is complete.

    ``strict`` raises on anything it cannot read; otherwise the unreadable record is
    dropped and reading resumes at the next line.
    """
    pending = ""
    start_line = 1
    truncation = None
    for lineno, line in enumerate(handle, 1):
        if not pending:
            start_line = lineno
        pending += line
        while True:
            head = len(pending) - len(pending.lstrip())
            if head == len(pending):  # blank or whitespace only
                pending = ""
                break
            try:
                record, consumed = _DECODER.raw_decode(pending, head)
            except json.JSONDecodeError as err:
                if _could_continue(pending, err):
                    truncation = err  # a later line may still complete it
                    break
                if strict:
                    reason = ("truncated record at end of file" if not handle.read().strip()
                              else "malformed record")
                    raise _error(reason, err, path, pending, start_line, err.pos) from None
                pending, start_line = _resync(pending, head, start_line)
                continue
            if not isinstance(record, dict):
                # Every record is a JSON object. Without this check resyncing inside a
                # torn record hands back its fragments: ``"notes": "..."`` starts with a
                # valid JSON string, so the reader would emit the bare scalar ``"notes"``
                # as a record and consumers would fail on record.get() instead.
                if strict:
                    reason = f"expected a JSON object, got {type(record).__name__}"
                    raise _error(reason, None, path, pending, start_line, head)
                pending, start_line = _resync(pending, head, start_line)
                continue
            yield record
            start_line += pending.count("\n", 0, consumed)
            pending = pending[consumed:]
    if pending.strip() and strict:
        raise _error("truncated record at end of file", truncation, path, pending, start_line,
                     truncation.pos if truncation else 0)


def _resync(pending, head, start_line):
    """Drop the first buffered line and report the line the remainder now starts on.

    Dropping a line rather than the whole buffer is what keeps a torn record from taking
    the records after it down with it.
    """
    newline = pending.find("\n", head)
    if newline < 0:
        return "", start_line
    return pending[newline + 1:], start_line + pending.count("\n", 0, newline + 1)


def iter_events(path):
    """Yield every record in ``path``. Strict: anything unreadable raises.

    Includes a truncated final record: for this reader a cut-off log is an error, and the
    :class:`RunLogDecodeError` names the file and line the bad record starts on.
    """
    with open(path, encoding="utf-8") as handle:
        yield from _scan(handle, strict=True, path=path)


def read_records(path):
    """Record-safe reader: yields every COMPLETE record and ignores a truncated tail.

    A killed run leaves a partial final record. Dropping it silently is correct; crashing
    on it means one dead run poisons every report built over the log. A torn record
    mid-file is likewise skipped, and the records after it are still read. Use
    :func:`iter_events` when you want the truncation to be an error instead.
    """
    with open(path, encoding="utf-8") as handle:
        yield from _scan(handle, strict=False, path=path)


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
