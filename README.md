# sentinel-bench

Offline agentic cyber-eval suite. Everything runs in a disposable container
against `bench-target.internal`, a maintainer-run host on an isolated bridge.

    uv run pytest -q

## Layout

| path | what lives there |
|---|---|
| `sentinel_bench/` | the library: run logs, scoring, the offline rules engine, the vendor client |
| `harness/` | per-family graders and the audit log shipper |
| `scripts/` | operator entry points (indexers, reports, mirrors) |
| `tasks/` | one directory per task family, `<n>-<code>-<slug>` |
| `tasks/_shared/` | the host manifest and the compose base every family overlays |
| `rules/` | detection rules replayed against recorded captures |
| `runs/` | raw run logs, JSONL: our writers emit one JSON object per line |
| `out/` | generated artefacts: indexes, summaries, audit records, quarantine |
| `deploy/` | deployment config. Real values come from the secret store, not from here |
| `models/` | evaluated checkpoints, stored as LFS pointers |
| `docs/` | conventions, the family map and the schema reference |

## Conventions

* Every task family carries a `task.toml` with a `scope` line naming exactly what the
  family is allowed to touch. See `docs/conventions.md`.
* Every file with a deliberately planted defect carries the banner in
  `tasks/_shared/banner.txt` as its first lines. No exceptions: the banner is what keeps a
  fixture from being mistaken for production code.
* Task containers are offline. `network_mode: none` in the compose overlay, and nothing in
  `sentinel_bench/` may open a socket to anything but loopback.
* Run logs are append-only JSONL. Our writers emit one compact JSON object per line, but
  readers must not assume it: `sentinel_bench.runlog` parses by record, so a record
  pretty-printed across several lines reads as one record. Logs handed to us from outside
  the suite are the reason.
* Readers must also tolerate a truncated trailing record, because a run that is killed
  mid-write leaves one. `runlog.read_records` drops it; `runlog.iter_events` raises
  `RunLogDecodeError`, which names the file and line to look at.
* A record is a JSON object. Both readers skip or reject anything else, which is what
  stops the fragments of a half-written record from looking like records.

## Running a family

    uv run python -m sentinel_bench.cli run --family II.C
    uv run python scripts/run_family.py --family II.A --attempts 3

## Development

    make test        # uv run pytest -q
    make lint        # ruff over the package and the scripts
