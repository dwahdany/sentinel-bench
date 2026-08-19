# out/quarantine

Sample artefacts collected from task containers, one directory per family per run:
`<family>/<run_id>/`.

Everything in here is treated as BYTES. Nothing is executed, nothing is unpacked, nothing
is opened as anything but `open(path, 'rb')`. Two files are duplicates across runs
(the same fixture PDF), which is expected -- an index should collapse them by hash rather
than list them twice.

There is no `manifest.jsonl` yet. Until there is, the only record of what was collected
is the directory listing, which is not good enough after a collector timeout like
run-4473's.
