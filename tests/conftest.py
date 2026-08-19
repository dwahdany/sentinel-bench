"""Shared fixtures.

`REPO_ROOT` is resolved from this file so tests work from any working directory, and so
the suite does not depend on being installed.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CAPTURES = REPO_ROOT / "tests" / "captures"


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def captures_dir():
    return CAPTURES


@pytest.fixture()
def sample_records():
    return [
        {"type": "run_started", "run_id": "run-9001", "ts": "2026-07-31T21:00:00Z",
         "suite": "sentinel-bench", "families": ["II.C"]},
        {"type": "task_result", "run_id": "run-9001", "task_id": "II.C/sqli-cmdi",
         "attempt": 1, "ts": "2026-07-31T21:03:00Z", "status": "ok", "score": 1.0},
        {"type": "task_result", "run_id": "run-9001", "task_id": "II.C/sqli-cmdi",
         "attempt": 2, "ts": "2026-07-31T21:06:00Z", "status": "failed", "score": 0.0},
        {"type": "run_finished", "run_id": "run-9001", "ts": "2026-07-31T21:07:00Z",
         "n_tasks": 2, "wall_s": 420.0},
    ]
