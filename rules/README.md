# rules

`detection-rules.json` is the ruleset the offline engine in `sentinel_bench/rules.py`
replays against the captures in `tests/captures/`. Every rule needs:

* a stable `id` (`SB-NNN`, never reused, never renumbered),
* a `family` so a per-family report can be built,
* a regex that matches the *recorded* fixture traffic. Fixture requests carry an
  `SB_PROBE_*` marker in the query string; a rule that only matches the marker is not a
  rule, it is a self-test, so match on the shape as well.

Adding a rule means adding or updating the `*.expected.json` sidecar of every capture it
changes, otherwise the regression run fails -- which is the point.
