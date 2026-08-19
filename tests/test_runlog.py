"""Run-log reader tests.

NOTE: `test_read_records_tolerates_truncated_tail` writes to a fixed path under
/tmp/sentinel-bench. It predates the tmp_path fixture and has not been moved yet.
"""

from __future__ import annotations

import json
import os

import pytest

from sentinel_bench import runlog

SCRATCH = "/tmp/sentinel-bench"


def test_read_records_tolerates_truncated_tail(sample_records):
    os.makedirs(SCRATCH, exist_ok=True)
    path = os.path.join(SCRATCH, "partial.jsonl")
    with open(path, "w", encoding="utf-8") as handle:
        for record in sample_records:
            handle.write(json.dumps(record) + "\n")
        handle.write('{"type": "task_result", "run_id": "run-90')  # killed mid-write
    assert len(list(runlog.read_records(path))) == len(sample_records)


def test_last_events_returns_oldest_first(tmp_path, sample_records):
    path = tmp_path / "run.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in sample_records) + "\n", encoding="utf-8")
    tail = runlog.last_events(str(path), 2)
    assert [r["type"] for r in tail] == ["task_result", "run_finished"]


def test_event_types_cover_every_dataclass():
    assert set(runlog.EVENT_TYPES) == {"run_started", "task_result", "run_finished"}


def test_read_records_reads_multiline_records(tmp_path, sample_records):
    """A pretty-printed record spans several lines and still reads as one record."""
    path = tmp_path / "multiline.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in sample_records:
            handle.write(json.dumps(record, indent=2) + "\n")
    assert list(runlog.read_records(str(path))) == sample_records


def test_read_records_reads_mixed_line_styles(tmp_path, sample_records):
    """One-per-line and pretty-printed records in the same log both read."""
    path = tmp_path / "mixed.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for index, record in enumerate(sample_records):
            indent = 2 if index % 2 else None
            handle.write(json.dumps(record, indent=indent) + "\n")
    assert list(runlog.read_records(str(path))) == sample_records


def test_read_records_drops_truncated_multiline_tail(tmp_path, sample_records):
    """A run killed mid-write leaves a partial record, pretty-printed or not."""
    path = tmp_path / "multiline-partial.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in sample_records:
            handle.write(json.dumps(record, indent=2) + "\n")
        handle.write('{\n  "type": "task_result",\n  "run_id": "run-90')  # killed mid-write
    assert list(runlog.read_records(str(path))) == sample_records


def test_read_records_resyncs_after_a_malformed_record(tmp_path, sample_records):
    """A malformed record in the middle costs that record only, not the rest of the log."""
    path = tmp_path / "malformed-middle.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(sample_records[0], indent=2) + "\n")
        handle.write("}{ not a record at all\n")
        handle.write(json.dumps(sample_records[-1], indent=2) + "\n")
    assert list(runlog.read_records(str(path))) == [sample_records[0], sample_records[-1]]


def test_iter_events_reads_multiline_records(tmp_path, sample_records):
    """The strict reader accepts multi-line records too -- they are valid logs."""
    path = tmp_path / "multiline.jsonl"
    path.write_text("".join(json.dumps(r, indent=2) + "\n" for r in sample_records),
                    encoding="utf-8")
    assert list(runlog.iter_events(str(path))) == sample_records


def test_iter_events_still_raises_on_a_truncated_tail(tmp_path, sample_records):
    """Strict stays strict: the tail a killed run leaves is not silently dropped here."""
    path = tmp_path / "partial.jsonl"
    path.write_text(json.dumps(sample_records[0]) + '\n{"type": "task_res',
                    encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        list(runlog.iter_events(str(path)))


def test_read_records_costs_only_the_bad_line(tmp_path, sample_records):
    """An unterminated string cannot span lines, so it ends at its own newline.

    The reader must not treat the following record as the rest of it.
    """
    path = tmp_path / "unterminated.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(sample_records[0]) + "\n")
        handle.write('{"type": "task_result", "notes": "unclosed\n')
        handle.write(json.dumps(sample_records[-1]) + "\n")
    assert list(runlog.read_records(str(path))) == [sample_records[0], sample_records[-1]]
