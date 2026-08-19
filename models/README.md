# models

Checkpoints under evaluation. One directory per checkpoint, shards stored as git-lfs
pointers so a plain clone stays small:

    git lfs pull --include "models/helios-eval-v2/*"

`helios-eval-v2` is a fine-tune of `helios-eval-v1`, eight shards, about 14 GiB. Its
licence is internal, evaluation use only, and it is not redistributable -- the line is in
`config.json` under `sentinel_bench.licence` and it applies to any copy of the files,
including one made for a collaborator.
