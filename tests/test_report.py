"""Report helper tests.

NOTE: these two write to the same fixed /tmp/sentinel-bench path, and
`test_summary_reuses_the_index` reads what `test_index_is_written` left behind, so the
file is not safe to run under -n auto and not safe to reorder. Known, not yet fixed.
"""

from __future__ import annotations

import os

from sentinel_bench import report

SCRATCH = "/tmp/sentinel-bench"
INDEX = os.path.join(SCRATCH, "index.csv")


def test_index_is_written(sample_records):
    os.makedirs(SCRATCH, exist_ok=True)
    groups = report.group_by([r for r in sample_records if r.get("type") == "task_result"],
                             ["run_id", "task_id"])
    with open(INDEX, "w", encoding="utf-8") as handle:
        handle.write("run_id,task_id,n,pass_rate\n")
        for (run_id, task_id), rows in groups.items():
            handle.write(f"{run_id},{task_id},{len(rows)},{report.pass_rate(rows):.2f}\n")
    assert os.path.exists(INDEX)


def test_summary_reuses_the_index():
    lines = open(INDEX, encoding="utf-8").read().splitlines()
    assert lines[0] == "run_id,task_id,n,pass_rate"
    assert lines[1].endswith("0.50")


def test_render_table_pads_columns():
    rows = [{"task": "II.C/sqli-cmdi", "n": 2}, {"task": "II.A/stack-smash", "n": 11}]
    text = report.render_table(rows, ["task", "n"])
    assert text.splitlines()[0].startswith("task")
    assert all(len(line) == len(text.splitlines()[0]) for line in text.splitlines())
