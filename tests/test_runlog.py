"""Run-log reader tests.

NOTE: `test_read_records_tolerates_truncated_tail` writes to a fixed path under
/tmp/sentinel-bench. It predates the tmp_path fixture and has not been moved yet.
"""

from __future__ import annotations

import json
import os

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
