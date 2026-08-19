# out/runs

Per-run artefacts, one directory per run, named `<ISO start>-<run_id>`.

| file | what it is |
|---|---|
| `meta.json` | run identity: id, start, families, target |
| `target.jsonl` | the target-side request log. `label` is written by the fixture app |
| `attempts.jsonl` | beta attempt records: prompt, response, score, `user_id`, `org_id` |

`attempts.jsonl` contains text people typed. It is covered by the beta data notice,
which permits aggregate reporting; anything identified needs the research-data request
that ana@example.invalid owns. See `deploy/analytics.toml`.
