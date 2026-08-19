# out/audit

The audit record, one file per month, append-only. This is what the Thursday review and
any incident reconstruction are built from, so it is tracked in git rather than treated
as a build product.

* written only by `harness/audit.py`;
* a wrong record is superseded by an appended `correction`, never edited or deleted;
* `manifest.json` carries a sha256 per file and `scripts/verify_audit.py` checks it. A
  mismatch means the file was edited in place.
