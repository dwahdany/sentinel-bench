# runs

Raw run logs, one JSON object per line, one file per run. Named
`<YYYY-MM-DD>-<slug>.jsonl`. Append-only while a run is live, immutable afterwards.

A run killed mid-write leaves a truncated final record, so read these with
`sentinel_bench.runlog.read_records`, never with a plain `json.loads` per line. That
reader also accepts records pretty-printed across several lines, which is what logs
handed to us from outside the suite sometimes look like -- our own writers do not
produce them.
