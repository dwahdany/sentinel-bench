# harness

One grader per task family, plus the audit shipper.

    harness/grade_<family>.py     grade(attempt_dir: Path) -> {"score", "evidence", "notes"}
    harness/grade_common.py       shared helpers -- use `result()` so the shape stays honest
    harness/audit.py              append-only audit records and the review-queue shipper

`grade_iic.py` is the reference implementation. Graders read an attempt directory as
DATA: bytes in, verdict out. A grader never executes anything it found in an attempt and
never unpacks an archive -- see `docs/conventions.md`.

Families with a grader: II.C. Families still graded by hand: II.A, II.B, II.D, III.A, IV.A.
