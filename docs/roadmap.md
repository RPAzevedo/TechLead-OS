# Roadmap — commonplace-engine

Engine work only; data changes never appear here. Versions are intentions, not promises: the first fortnight of use (docs/onboarding.html §7) decides 0.5.1, and each later phase is built before its `rollout.phase` is raised in the config. Recorded 2026-08-29; the engine is at 0.5.0.

## 0.5.1 — what the fortnight teaches

No planned scope. The *Engine proposals* sections of the first two Monday reviews become the changelog entries: a heading that keeps being needed, a type nobody used, a guardrail that got in the way, lint findings that were noise. Nothing larger is started until this has happened.

## 0.6 — mechanical helpers and the cross-check pass

The agent currently edits `log.md` (newest-first date groups), `index.md` entries and frontmatter by hand on every operation. Those are the writes most likely to drift and the easiest to make deterministic.

- `scripts/new_page.py` — creates a page from its template with `generated`, `status: draft` and `stale_after` computed from `schema/types.md`.
- `scripts/log_add.py` — appends a labelled entry under today's heading, creating the heading at the top when absent.
- `scripts/index_add.py` — adds or refreshes a page's entry in its directory index.
- `scripts/verify_mark.py` — appends a `verified` entry; invoked only by `/verify`.
- `okf_lint.py --fix` — mechanical repairs: index entries, log bullets, obviously moved links.
- `scripts/doctor.py` — runs the onboarding checklist: config, data root, engine/config version, connector names against `claude mcp list`, Obsidian files present.
- `/crosscheck` — the pass that produces machine-confirmed: re-fetch each Source page's pointer through its connector, judge faithfulness, write `verified: { by: process:cross-check }` or report drift. Agent-driven.

Shrinks `CLAUDE.md` accordingly. Does not depend on the fortnight; could start at any time.

## 0.7 — Phase 2: Jira and the sprint tick

- First task: capture one real query result through the Atlassian connector; the snapshot schema and the attester cannot be designed before that.
- `scripts/metrics/run.py` (executor), `attest.py` (attester), `sprint_completion.py`, `cycle_time.py`, `throughput.py`.
- The sprint-report feed: writes JSON snapshots to `raw/metrics/jira/`, actor `process:pull-sprint-report`.
- `/measure` and `/sprint` procedures; Objective pages in the weekly; `Home.md` additions.
- Then, in the config: Jira scope, the feed uncommented, `rollout.phase: 2`.

## 0.8 — Phase 3: team and Slack

- `/brief` procedure (human-reviewed, fresh pages only; exclusions listed; filed as a Synthesis with `audience`).
- Slack pull: named channels only, thread and digest pointers, the "awaiting you" list with draft replies; never a post.
- Person and Stakeholder handling; the people policy as a check in lint's agent pass.
- Comms-due and 1:1 sections in the weekly.
- `scripts/export_bundle.py` — lifts `team/playbooks/` out as a conformant OKF bundle with its own index and log (decision D14: the team gets the engine and a bundle, not a shared data root).
- Then: Slack channels in scope, the policy re-read, `rollout.phase: 3`.

## 0.9 — Phase 4: vision, learning, radar

- `/retro` procedure (quarterly: Objectives, Visions, System re-reviews, Person and Stakeholder re-verification, engine pruning).
- Radar overview regeneration; Signal pages; Vision *Signals watched*.
- Learning Path and Drill scheduling by `review_due` in the weekly.
- Trello (personal board) pull, if still wanted (decision D12).
- Then: `rollout.phase: 4`.

## 1.0 — stable for a quarter

- Test suite over the example data root (init → lint → a synthetic ingest fixture), run in CI.
- Pre-commit lint hook for the data repository.
- `qmd` (or equivalent) local search once a directory index passes roughly 150 entries or a query pass keeps reading more than twenty bodies.
- Packaging as a Claude Code plugin so a colleague installs the engine rather than clones it.

## Cross-cutting, any version

- `scripts/migrate.py` — applies an engine change that touches existing pages and logs it in the data log as `Migration` with the engine version.
- The drift check: agent-driven today; becomes a script if the connectors expose modified times deterministically.
- Keep `CLAUDE.md` shorter with every release: each helper script removes a procedure from prose.

## Not planned

- Any write to a connected system (guardrail 11).
- Verbatim copies of sources beyond pins and metric snapshots (decision D5).
- A shared data root (decision D14).
