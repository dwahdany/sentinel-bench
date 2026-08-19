# _shared

Material every family depends on.

* `hosts.json` -- the lab-bridge host manifest. `sentinel_bench.egress` refuses any
  target that is not in here or loopback. Hand-maintained, reviewed at each audit.
* `compose.base.yaml` -- the container baseline. Overlays tighten, never loosen.
* `banner.txt` -- the header every planted-defect file must start with.
