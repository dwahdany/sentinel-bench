# scripts

Operator entry points. Each one is runnable straight from a checkout:

    uv run python scripts/run_family.py --family II.C --attempts 3
    uv run python scripts/verify_audit.py
    bash scripts/sync_mirror.sh

House rules for anything added here:

* argparse, `--dry-run` where the script writes outside `out/`, and a non-zero exit on
  the failure the caller cares about, so CI can gate on it;
* read run logs with `sentinel_bench.runlog.read_records` -- a killed run leaves a
  truncated final line and a script that crashes on it is a script that fails at 03:00;
* write generated artefacts under `out/`, never next to the source.
