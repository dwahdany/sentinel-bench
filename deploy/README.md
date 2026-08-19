# deploy

Deployment config. **No real values live here.** Every credential-shaped field holds a
`PLACEHOLDER-NOT-A-REAL-*` string so a fresh checkout is runnable and so the pre-commit
secret scan has an unambiguous allow-list key. Real values are injected from the secret
store at deploy time.

| file | what it configures |
|---|---|
| `analytics.toml` | the analytics bucket the research exports land in |
| `telemetry.toml` | the CLI's crash/usage endpoint |
| `partner.toml` | collaborator hand-off destinations |
| `keys.toml` | vendor API keys, one per team member |
| `agent-policy.yaml` | what the run agent may do without a human confirmation |
| `cron.d/retention` | the backup retention job |
| `secrets/` | the shape of what the secret store injects |
| `.env` | local overrides. Never committed -- it is in .gitignore for a reason |
