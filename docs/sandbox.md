# Sandbox notes

Task containers run offline and unprivileged. The compose base is
`tasks/_shared/compose.base.yaml`; a family overlays it and may only make the sandbox
tighter, never looser.

Current baseline:

| control | value |
|---|---|
| network | `network_mode: none` |
| filesystem | `read_only: true`, one `tmpfs` at `/work` |
| capabilities | `cap_drop: [ALL]` |
| user | non-root, uid 10001 |
| pids | `pids_limit: 256` |

## Syscall notes

We do not ship a seccomp profile yet, so containers run under the runtime default. The
open question is which syscalls the runner actually needs: the Python interpreter's
startup set, plus whatever the fixture app uses. Record findings here as they are
measured -- a deny-by-default profile is only safe once that list is written down.

Known so far, from strace of the II.C fixture:

* interpreter startup: `execve`, `mmap`, `mprotect`, `openat`, `read`, `close`, `fstat`,
  `brk`, `rt_sigaction`, `futex`;
* the app: `socket`/`bind`/`listen` on loopback, `accept4`, `epoll_*`, `write`;
* the HEALTHCHECK: `clone3`, `wait4`, `pipe2`.
