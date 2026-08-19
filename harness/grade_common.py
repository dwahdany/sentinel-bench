"""Helpers every family grader uses."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def result(score, evidence=None, notes=""):
    """The grader return shape. Every grader must go through here."""
    score = float(score)
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"score {score} outside [0, 1]")
    return {"score": score, "evidence": list(evidence or []), "notes": str(notes)}


def iter_files(attempt_dir):
    """Every regular file under an attempt directory, in a stable order."""
    root = Path(attempt_dir)
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def read_text(path, limit=1_000_000):
    """Bytes -> text, leniently. Graders read attempts as data, never as code."""
    with open(path, "rb") as handle:
        return handle.read(limit).decode("utf-8", "replace")


def sha256_file(path, chunk=65536):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def relative(path, attempt_dir):
    return os.path.relpath(str(path), str(attempt_dir))
