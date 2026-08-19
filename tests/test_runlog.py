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

def test_read_records_reads_multi_line_records(tmp_path, sample_records):
    """A record pretty-printed across lines is one record, not one per line."""
    path = tmp_path / "pretty.jsonl"
    path.write_text("".join(json.dumps(r, indent=2) + "\n" for r in sample_records),
                    encoding="utf-8")
    assert list(runlog.read_records(str(path))) == sample_records


def test_read_records_reads_mixed_line_shapes(tmp_path, sample_records):
    """Compact and multi-line records in one file, plus blank lines between them."""
    started, ok, failed, finished = sample_records
    path = tmp_path / "mixed.jsonl"
    path.write_text(
        json.dumps(started) + "\n"
        + json.dumps(ok, indent=2) + "\n"
        + "\n"
        + json.dumps(failed, indent=4) + "\n"
        + json.dumps(finished) + "\n",
        encoding="utf-8")
    assert list(runlog.read_records(str(path))) == sample_records


def test_read_records_keeps_embedded_newlines_in_strings(tmp_path):
    """A note containing a newline survives the round trip: the reader must not split
    records on newlines that live inside a JSON string."""
    record = {"type": "task_result", "run_id": "run-9002", "task_id": "II.A/stack-smash",
              "attempt": 1, "ts": "2026-07-31T21:09:00Z", "status": "error", "score": 0.0,
              "notes": "collector timed out\nartefacts partially written"}
    path = tmp_path / "notes.jsonl"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    assert list(runlog.read_records(str(path))) == [record]
    assert "\n" in list(runlog.read_records(str(path)))[0]["notes"]


def test_read_records_drops_truncated_multi_line_tail(tmp_path, sample_records):
    """A run killed part-way through writing a pretty-printed record: the complete
    records survive and only the tail is dropped."""
    path = tmp_path / "killed.jsonl"
    partial = json.dumps(sample_records[-1], indent=2).splitlines(keepends=True)[:3]
    path.write_text("".join(json.dumps(r, indent=2) + "\n" for r in sample_records[:-1])
                    + "".join(partial), encoding="utf-8")
    assert list(runlog.read_records(str(path))) == sample_records[:-1]


def test_read_records_resyncs_after_torn_multi_line_record(tmp_path, sample_records):
    """A torn record mid-file must not swallow the records after it."""
    started, ok, failed, finished = sample_records
    path = tmp_path / "torn.jsonl"
    path.write_text(
        json.dumps(started, indent=2) + "\n"
        + '{"type": "task_result", "run_id": "run-90\n'  # torn by an earlier crash
        + json.dumps(ok, indent=2) + "\n"
        + json.dumps(finished, indent=2) + "\n",
        encoding="utf-8")
    assert list(runlog.read_records(str(path))) == [started, ok, finished]


def test_read_records_yields_every_complete_prefix(tmp_path, sample_records):
    """Cut a pretty-printed log at every line boundary; each cut must yield exactly the
    records that are complete at that point.

    This pins both halves of the incomplete/malformed decision the reader makes: cutting
    early must never split one record into two, and must never hide a record that is
    already complete.
    """
    chunks = [json.dumps(r, indent=2) + "\n" for r in sample_records]
    text = "".join(chunks)
    complete_at = {}
    for count in range(len(chunks) + 1):
        complete_at[len("".join(chunks[:count]).splitlines())] = count
    path = tmp_path / "cut.jsonl"
    for stop in range(1, len(text.splitlines()) + 1):
        path.write_text("".join(text.splitlines(keepends=True)[:stop]), encoding="utf-8")
        expected = sample_records[:max(v for k, v in complete_at.items() if k <= stop)]
        assert list(runlog.read_records(str(path))) == expected, f"cut after {stop} lines"


def test_iter_events_reads_multi_line_records(tmp_path, sample_records):
    path = tmp_path / "pretty.jsonl"
    path.write_text("".join(json.dumps(r, indent=2) + "\n" for r in sample_records),
                    encoding="utf-8")
    assert list(runlog.iter_events(str(path))) == sample_records


def test_iter_events_still_raises_on_truncated_tail(tmp_path, sample_records):
    """The strict reader keeps its contract: a cut-off log is an error, not a short read."""
    path = tmp_path / "killed.jsonl"
    cut = '{\n  "type": "task_result",\n'  # killed part-way through the next record
    path.write_text(json.dumps(sample_records[0], indent=2) + "\n" + cut, encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        list(runlog.iter_events(str(path)))


def test_last_events_spans_multi_line_records(tmp_path, sample_records):
    path = tmp_path / "run.jsonl"
    path.write_text("".join(json.dumps(r, indent=2) + "\n" for r in sample_records),
                    encoding="utf-8")
    tail = runlog.last_events(str(path), 2)
    assert [r["type"] for r in tail] == ["task_result", "run_finished"]
