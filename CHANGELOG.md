# Changelog — tos-engine

Engine changes only. Data changes are logged in `<data.root>/wiki/log.md`; a data migration caused by an engine change is logged there as `Migration` with the engine version.

## 0.5.2 — 2026-08-29

**Malformed YAML is now a conformance error, and the engine installs as a package.**

- Frontmatter is parsed with PyYAML, now a required dependency; the permissive built-in fallback
  parser is gone. `load_yaml()` raises `YamlError` on anything malformed — no line is ever silently
  dropped, so a page with `tags: [a, b` no longer passes lint.
- `split_frontmatter()` distinguishes absent, empty and unparseable frontmatter; non-mapping
  frontmatter and an unclosed `---` fence are errors too. `tos-lint` reports unparseable pages and
  indexes under `conformance` and exits 1; a malformed config stops instead of half-parsing.
- Packaging (**breaking**): `pyproject.toml` + `uv.lock`; `scripts/*.py` → `src/tos/` (`common.py`,
  `init.py`, `lint.py`). Install with `uv sync`; run `uv run tos-config`, `uv run tos-init`,
  `uv run tos-lint` from this checkout — the old `python3 scripts/…` invocations are gone.
  `schema/` stays at the repository root, found by walking up from the package;
  `$TOS_ENGINE_ROOT` overrides it.
- Tests (`uv run pytest`): the malformed-frontmatter regression, the frontmatter contract, every
  shipped schema page, and init → lint end to end. `uv run ruff check` for style.
- `schema/examples/design/rfcs/example-media-pipeline-v2.md` had an unquoted `: ` in its title —
  invalid frontmatter the old parser had been hiding. Quoted.
- Docs, command files and settings follow the new paths; `docs/design.pdf` is a generated artifact
  and was not regenerated.

## 0.5.1 — 2026-08-29

Renamed from Commonplace to **TechLead OS**, short form `tos`. No behaviour change.

- Config path `~/.config/tos/config.yaml`; environment variable `TOS_CONFIG`.
- `scripts/pos_common.py` → `scripts/tos_common.py`.
- Titles and text across `CLAUDE.md`, the commands, the docs and the published pages; the bundle-root index title.
- Decision D8 in the design records the rename and the reason.

## 0.5.0 — 2026-08-29

Initial engine, the Phase 0/1 thin slice of the v0.5 design (docs/design.html):

- `CLAUDE.md` — the schema: read-config-first, the two trees, the OKF v0.2 page contract, operations, guardrails, the people policy.
- `config.example.yaml` — data root, actor, timezone, rollout phase, connector providers and scopes, feeds, review settings; no secrets.
- Commands: `/init`, `/pull`, `/ingest`, `/query`, `/lint`, `/verify`, `/weekly`; `/sprint`, `/measure`, `/brief`, `/retro` present but gated on `rollout.phase`.
- `schema/types.md` — twenty types with phase, directory, horizon, gate and headings; `schema/templates/` — one per type plus the pinned-copy header.
- `schema/vault/` — Obsidian settings and the `Home.md` Dataview dashboard, installed into the data root by `/init`.
- `schema/examples/` — ten worked example pages (one per Phase 1 type) and one example note, installed with `/init --with-examples`, removable with `--remove-examples`.
- `scripts/tos_common.py` (config, frontmatter, dates; PyYAML optional), `scripts/init.py`, `scripts/okf_lint.py`.
- `docs/` — the design page (HTML, PDF, markdown).

Not yet built (later phases): `scripts/metrics/` executor and attester, the sprint tick, briefs, the quarterly retro, Slack/Jira/Trello pull procedures. The order is in `docs/roadmap.md`.
