# III.A environment

`noise-fixture.bin` is the target the family runs against: a deterministic pseudo-random
byte file with a real safetensors-shaped header, produced by
`python -m sentinel_bench.cli run --family III.A --make-fixture`.

It is noise on purpose. The family measures how a checkpoint is *handled* -- shard
manifests, checksum verification, refusing to move a file off the box -- and none of
that needs real weights. If a task ever needs realistic tensors, the answer is a small
open checkpoint copied in by hand with its licence recorded here, not a pull from a
serving endpoint.
