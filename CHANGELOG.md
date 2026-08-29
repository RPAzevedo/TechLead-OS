# Changelog — commonplace-engine

Engine changes only. Data changes are logged in `<data.root>/wiki/log.md`; a data migration caused by an engine change is logged there as `Migration` with the engine version.

## 0.5.0 — 2026-08-29

Initial engine, the Phase 0/1 thin slice of the v0.5 design (docs/design.html):

- `CLAUDE.md` — the schema: read-config-first, the two trees, the OKF v0.2 page contract, operations, guardrails, the people policy.
- `config.example.yaml` — data root, actor, timezone, rollout phase, connector providers and scopes, feeds, review settings; no secrets.
- Commands: `/init`, `/pull`, `/ingest`, `/query`, `/lint`, `/verify`, `/weekly`; `/sprint`, `/measure`, `/brief`, `/retro` present but gated on `rollout.phase`.
- `schema/types.md` — twenty types with phase, directory, horizon, gate and headings; `schema/templates/` — one per type plus the pinned-copy header.
- `schema/vault/` — Obsidian settings and the `Home.md` Dataview dashboard, installed into the data root by `/init`.
- `schema/examples/` — ten worked example pages (one per Phase 1 type) and one example note, installed with `/init --with-examples`, removable with `--remove-examples`.
- `scripts/pos_common.py` (config, frontmatter, dates; PyYAML optional), `scripts/init.py`, `scripts/okf_lint.py`.
- `docs/` — the design page (HTML, PDF, markdown).

Not yet built (later phases): `scripts/metrics/` executor and attester, the sprint tick, briefs, the quarterly retro, Slack/Jira/Trello pull procedures.
