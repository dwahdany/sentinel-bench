# Conventions

## Task families

A family lives at `tasks/<n>-<code>-<slug>/` and carries a `task.toml` whose `scope`
line names exactly what the family may touch. Nothing outside the scope line is in
bounds, and a family that needs more scope gets it reviewed, not widened in place.

Per-task directories sit under the family: `tasks/5-II.C-web/0-static-fixture/`.
Each has its own `task.toml` and an `environment/` holding the container definition.

## The planted-defect banner

Every file containing a deliberately planted defect starts with the banner in
`tasks/_shared/banner.txt`, verbatim, as the first lines of the file. A fixture without
the banner is indistinguishable from production code six months later, which is how a
teaching example ends up in a real service.

## Containers

* base image pinned by digest, never by tag;
* `USER` set to a non-root account;
* a `HEALTHCHECK` that actually checks the app, not `true`;
* `network_mode: none` in the compose overlay -- task containers are offline;
* nothing writes outside `/work`.

## Reading attempts

Graders read attempt directories as bytes. No execution, no archive extraction, no
`subprocess` against anything an attempt produced. `harness/grade_common.read_text`
is the only reader graders should need.

## Network

`sentinel_bench` opens sockets to loopback and to the lab bridge only, and the bridge
addresses come from `tasks/_shared/hosts.json`. Adding an address means adding an owner
next to it.

## Secrets

Real values live in the secret store. `deploy/` holds shape and placeholders so a
checkout is runnable; the placeholder convention is `PLACEHOLDER-NOT-A-REAL-*` so the
pre-commit scan's allow-file has something unambiguous to key on.
