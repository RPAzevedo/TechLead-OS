# Changelog — tos-engine

Engine changes only. Data changes are logged in `<data.root>/wiki/log.md`; a data migration caused by an engine change is logged there as `Migration` with the engine version.

## 0.7.0 — 2026-08-30

**Projects become the first-class entity: each carries the problem it solves, your role, a weekly-ranked priority and a weekly log — and Objectives move to phase 1 to hold the quarter's company and team OKRs.**

- A Project page now opens with *Problem* and *Expected impact* in place of *Goal*, and closes with a *Weekly log*: one dated entry per week of movement — progress, challenges and risks, blockers and the support you need, open questions and decisions, and the notes that carry the nuance. New frontmatter: `role` (lead or support, independent of `owner`), `priority`, and a closed `stage` vocabulary that adds `paused`.
- `/tos-weekly` opens with **Projects — ranked portfolio**: every active project in priority order with its role, stage, trust tier and rank movement, and its week drafted for you from the log, the week's sources and git. You answer inline — rank, corrections, `objective:`, `verify` — and an unanswered row means the entry is accepted and the rank kept. `--apply` writes the entries, renumbers priorities, reorders the projects index, and re-verifies what you asked it to. A week with no movement writes nothing, so a quiet project keeps its verification.
- Active projects leave the verify, expiry and checkpoint queues: they surface in their portfolio rows instead, which is also where they are re-verified. Lint and `Home.md` follow the same rule.
- Objective is a phase-1 type, with `level` (company or team) and `quarter`, and quarter-prefixed slugs. Projects link the objective they advance from *Expected impact*; a team objective links its company objective. Both are ordinary body links — no new frontmatter relation.
- `tos-lint` gains two check groups: project fields — including a missing `stage`, which is what makes a project active — priorities that collide or leave a gap, and weekly-log shape, repeats, future dates and currency — every dated entry has to carry at least one `- **Label**: …` bullet, colon and content included, since a week with nothing to say writes no entry, and the log's shape is checked whatever the stage while currency and alignment are asked of active projects only; objective fields, and a nudge — only once objectives exist — when a lead project's *Expected impact* links no live objective, or a team objective's *Objective* section links no company objective **from its own quarter**. The alignment has to be in that section: a mention elsewhere on the page is not the link. Neither affects the exit code, and a fresh `--with-examples` bundle stays quiet. The dead registry-parsing fallback in `load_registry()` is gone, and an eleventh example page ships.
- `review.weekly_log_grace_days` (default 16) sets how long an active project may stay silent before lint says so. A config written for `engine: "0.6"` prints a drift note until it is set to `"0.7"`.
- Existing Project pages need a migration: *Goal* becomes *Problem* plus *Expected impact*, and an empty *Weekly log* is appended; `role`, `priority` and the objective links are seeded by the first 0.7.0 Monday rather than guessed. Log it in the data log as `Migration` with the engine version.

## 0.6.0 — 2026-08-30

**Every command is now `/tos-<verb>`, and the README lists all eleven.**

- The eleven operations are invoked as `/tos-init`, `/tos-pull`, `/tos-ingest`, `/tos-query`,
  `/tos-lint`, `/tos-verify`, `/tos-weekly`, `/tos-sprint`, `/tos-measure`, `/tos-brief` and
  `/tos-retro`. `/init` no longer shadows Claude Code's built-in command, and the set is
  identifiable in a session that also has personal or plugin commands loaded.
- `README.md` has a **Commands** table: each command with its arguments, what it does and the
  rollout phase that enables it. `tests/test_commands.py` fails if a command file is added without
  the prefix or without a row in that table. `.claude/` now ships in the sdist, so the command files
  are part of the released artifact and its test suite passes from an extracted tarball.
- `docs/onboarding.html` and `docs/roadmap.md` use the new names. The design record keeps the old
  ones and says so in a notice under its title: `docs/design.md`, `docs/design.html` and
  `docs/scenarios.html`. `docs/design.pdf` is gone — it was a browser print of `design.html` with no
  build script behind it, so it could only ever go stale; read the HTML.
- A config written for `engine: "0.5"` prints a drift note until it is set to `"0.6"`. Nothing else
  in the config changes, and no data migration is needed.

## 0.5.4 — 2026-08-30

**Setup no longer assumes where the engine and the data root live, and the snippets you are meant to type can be copied.**

- `docs/onboarding.html` starts from a `git clone` into a directory you choose and keeps the two
  locations in `$TOS_ENGINE` and `$TOS_DATA`, set once in steps 1 and 2. Every command reaches the
  tools as `uv run --directory "$TOS_ENGINE" tos-…`, so none of them depends on the shell still
  being in the engine directory, and the expected-output blocks no longer print one machine's home
  directory and actor.
- `config.example.yaml` ships `CHANGE_ME` placeholders for `data.root` and `data.actor` and an empty
  `md` scope, so copying it forces a deliberate choice rather than inheriting someone else's layout.
  `README.md` matches.
- The onboarding page's thirteen terminal, prompt and settings snippets have copy buttons, which
  omit the explanatory comments and Claude Code's `>` prompt marker. The page still works, and
  prints, with JavaScript off.

## 0.5.3 — 2026-08-30

**The dashboard stops counting the bundle's own index files, and the setup docs match what the tools print.**

- `schema/vault/Home.md`: *Unverified, newest first* and *Open questions* filtered only on a field
  being absent (`!verified`, `status != "deprecated"`), and Dataview matches those against the
  frontmatter-less `index.md` and `log.md` files that `/init` creates — so the first table filled its
  ten-row limit with index files and *Open questions* listed `questions/index.md`. Both now require
  the field to be present, the idiom the other six queries already used. Re-run `/init` to reinstall
  the dashboard in an existing data root.
- `docs/onboarding.html` and `README.md` now match the engine: the expected `tos-config` and
  `tos-lint` output (both still carried a parser line that 0.5.2 removed), what `Home.md` shows on
  day one, which commands write a log line and a commit, and `.claude/settings.local.json`, which is
  untracked and yours to create rather than something the repository ships.

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
