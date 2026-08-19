# Task families

| code | slug | what it measures | grader |
|---|---|---|---|
| II.A | pwn | binary exploitation against a planted, offline target | by hand |
| II.B | egress | what a task container tries to send, traced on loopback | by hand |
| II.C | web | injection defects planted in a fixture web app | `harness/grade_iic.py` |
| II.D | artifacts | triage of the sample artefacts a run collects | by hand |
| III.A | weights | handling of a checkpoint fixture, offline | by hand |
| IV.A | refusal | whether a model under test declines what it should | by hand |

Numbering in `tasks/` (`2-II.A-pwn`, `5-II.C-web`, ...) is the run order, not a
priority. It is stable: the number is never reused after a family is retired.
