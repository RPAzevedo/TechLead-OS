# Roadmap — tos-engine

Engine work only; data changes never appear here. The planned sections below are ordered, not numbered: 0.6.0 went on a command rename nobody had planned, and a numbered plan that reshuffles every time that happens tells the reader less than the order does. Each phase is built before its `rollout.phase` is raised in the config. Recorded 2026-08-29; the engine is at 0.6.0 (0.5.1 was the rename to TechLead OS; 0.5.2 packaged it and made malformed YAML a conformance error; 0.5.3 fixed the Home.md dashboard and the setup docs; 0.5.4 made the setup paths portable; 0.6.0 prefixed the commands with `tos-`).

## Next — what the fortnight teaches

No planned scope. The *Engine proposals* sections of the first two Monday reviews become the changelog entries: a heading that keeps being needed, a type nobody used, a guardrail that got in the way, lint findings that were noise. Nothing larger is started until this has happened.

## Then — mechanical helpers and the cross-check pass

The agent currently edits `log.md` (newest-first date groups), `index.md` entries and frontmatter by hand on every operation. Those are the writes most likely to drift and the easiest to make deterministic.

- `src/tos/new_page.py` — creates a page from its template with `generated`, `status: draft` and `stale_after` computed from `schema/types.md`.
- `src/tos/log_add.py` — appends a labelled entry under today's heading, creating the heading at the top when absent.
- `src/tos/index_add.py` — adds or refreshes a page's entry in its directory index.
- `src/tos/verify_mark.py` — appends a `verified` entry; invoked only by `/tos-verify`.
- `tos-lint --fix` — mechanical repairs: index entries, log bullets, obviously moved links.
- `src/tos/doctor.py` — runs the onboarding checklist: config, data root, engine/config version, connector names against `claude mcp list`, Obsidian files present.
- `/tos-crosscheck` — the pass that produces machine-confirmed: re-fetch each Source page's pointer through its connector, judge faithfulness, write `verified: { by: process:cross-check }` or report drift. Agent-driven.

Shrinks `CLAUDE.md` accordingly. Does not depend on the fortnight; could start at any time.

## Phase 2 — Jira and the sprint tick

- First task: capture one real query result through the Atlassian connector; the snapshot schema and the attester cannot be designed before that.
- `src/tos/metrics/run.py` (executor), `attest.py` (attester), `sprint_completion.py`, `cycle_time.py`, `throughput.py`.
- The sprint-report feed: writes JSON snapshots to `raw/metrics/jira/`, actor `process:pull-sprint-report`.
- `/tos-measure` and `/tos-sprint` procedures; Objective pages in the weekly; `Home.md` additions.
- Then, in the config: Jira scope, the feed uncommented, `rollout.phase: 2`.

## Phase 3 — team and Slack

- `/tos-brief` procedure (human-reviewed, fresh pages only; exclusions listed; filed as a Synthesis with `audience`).
- Slack pull: named channels only, thread and digest pointers, the "awaiting you" list with draft replies; never a post.
- Person and Stakeholder handling; the people policy as a check in lint's agent pass.
- Comms-due and 1:1 sections in the weekly.
- `src/tos/export_bundle.py` — lifts `team/playbooks/` out as a conformant OKF bundle with its own index and log (decision D14: the team gets the engine and a bundle, not a shared data root).
- Then: Slack channels in scope, the policy re-read, `rollout.phase: 3`.

## Phase 4 — vision, learning, radar

- `/tos-retro` procedure (quarterly: Objectives, Visions, System re-reviews, Person and Stakeholder re-verification, engine pruning).
- Radar overview regeneration; Signal pages; Vision *Signals watched*.
- Learning Path and Drill scheduling by `review_due` in the weekly.
- Trello (personal board) pull, if still wanted (decision D12).
- Then: `rollout.phase: 4`.

## 1.0 — stable for a quarter

- The test suite in CI, and a synthetic ingest fixture to go with the init → lint tests added in 0.5.2.
- Pre-commit lint hook for the data repository.
- `qmd` (or equivalent) local search once a directory index passes roughly 150 entries or a query pass keeps reading more than twenty bodies.
- Packaging as a Claude Code plugin so a colleague installs the engine rather than clones it.

## Cross-cutting, any time

- `src/tos/migrate.py` — applies an engine change that touches existing pages and logs it in the data log as `Migration` with the engine version.
- The drift check: agent-driven today; becomes a script if the connectors expose modified times deterministically.
- Keep `CLAUDE.md` shorter with every release: each helper script removes a procedure from prose.

## Not planned

- Any write to a connected system (guardrail 11).
- Verbatim copies of sources beyond pins and metric snapshots (decision D5).
- A shared data root (decision D14).
