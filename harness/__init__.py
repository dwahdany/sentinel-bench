"""Per-family graders and the audit shipper.

A grader is a module named ``grade_<family>.py`` exposing ``grade(attempt_dir) -> dict``
with keys ``score`` (float in [0, 1]), ``evidence`` (list of strings) and ``notes``.
Shared helpers live in ``grade_common.py``.
"""
