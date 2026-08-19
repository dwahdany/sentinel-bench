# Changelog

All notable changes to sentinel-bench. Anything that changes what an automated run is
allowed to do gets an entry here, including changes described as internal.

## [Unreleased]
### Fixed
- `runlog.read_records` and `runlog.iter_events` parse by record instead of by line, so a
  record whose JSON is pretty-printed across several lines is read as one record. Our
  writers still emit one compact object per line; externally produced logs do not always.
  A torn record mid-file is still skipped by `read_records` without swallowing the records
  after it.
- Both readers now require a record to be a JSON object. A record torn mid-string leaves
  fragments like `"notes": "..."` that are valid JSON values on their own, so without this
  the readers could hand a bare string back as a record and consumers would fail on
  `record.get(...)`.
### Added
- `runlog.RunLogDecodeError`, raised by `iter_events`. Subclasses `json.JSONDecodeError`,
  so existing handlers still catch it, but names the file and the line the bad record
  starts on and says whether the record was truncated at end of file or malformed.

## [0.4.2] - 2026-07-28
### Added
- `sentinel_bench/egress.py`: the II.B egress module, loopback and lab bridge only.
- `rules/detection-rules.json` v3: SB-006, DNS TXT tunnelling.
### Fixed
- `runlog.read_records` no longer raises on the truncated final line a killed run leaves.

## [0.4.1] - 2026-07-11
### Changed
- `deploy/agent-policy.yaml` v4: `delete_path` moved from `auto_allow` to
  `requires_confirmation` for the operator role, after the June incident where a
  retention job and a cleanup task ran in the same window.
### Added
- `docs/conventions.md`: the planted-defect banner is now mandatory.

## [0.4.0] - 2026-06-19
### Added
- `harness/audit.py` and the append-only audit log under `out/audit/`.
- `tasks/_shared/hosts.json`: the lab-bridge host manifest, owners required.
### Removed
- The ad-hoc `scan.sh` subnet sweep. Targets come from the manifest now.

## [0.3.0] - 2026-05-22
### Added
- `harness/grade_iic.py`, the first wired grader.
- The II.C static fixture control task.
