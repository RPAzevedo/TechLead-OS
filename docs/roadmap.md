# Roadmap — tos-engine

Engine work only; data changes never appear here. The planned sections below are ordered, not numbered: 0.6.0 went on a command rename nobody had planned, and a numbered plan that reshuffles every time that happens tells the reader less than the order does. Each phase is built before its `rollout.phase` is raised in the config. Recorded 2026-08-29, last revised 2026-09-01; the engine is at 0.9.0 (0.5.1 was the rename to TechLead OS; 0.5.2 packaged it and made malformed YAML a conformance error; 0.5.3 fixed the Home.md dashboard and the setup docs; 0.5.4 made the setup paths portable; 0.6.0 prefixed the commands with `tos-`; 0.7.0 made Project the first-class entity and moved Objective to phase 1; 0.7.1–0.7.3 denied the connectors' write tools and fixed the two defects phase 2 would have hit; 0.8.0 turned the bookkeeping writes — page creation, log bullets, index entries, verified entries — into scripts, gave lint `--fix` and a registry-wide headings check, and added `tos-doctor`; 0.9.0 gave Project and Initiative their four connector pointers — the Slack channel, the Jira epic, the Confluence page, the RFC — and Initiative its first lint block).

## Next — what the fortnight teaches

No planned scope. The *Engine proposals* sections of the first two Monday reviews become the changelog entries: a heading that keeps being needed, a type nobody used, a guardrail that got in the way, lint findings that were noise. Nothing larger is started until this has happened.

## Then — the cross-check pass

The mechanical helpers shipped in 0.8.0; what remains of this section is the pass that consumes them:

- `/tos-crosscheck` — the pass that produces machine-confirmed: re-fetch each Source page's pointer through its connector, judge faithfulness, write the entry with `tos-verify-mark --by process:cross-check` (which already accepts it) or report drift. Agent-driven; a command file and a README row, nothing more. Deferred from 0.8.0 because it is the one helper that needs live connectors and judgement.

Does not depend on the fortnight; could start at any time.

## Phase 2 — Jira and the sprint tick

- First task: capture one real query result through the Atlassian connector; the snapshot schema and the attester cannot be designed before that.
- `src/tos/metrics/run.py` (executor), `attest.py` (attester), `sprint_completion.py`, `cycle_time.py`, `throughput.py`.
- The sprint-report feed: writes JSON snapshots to `raw/metrics/jira/`, actor `process:pull-sprint-report`.
- `/tos-measure` and `/tos-sprint` procedures; sprint goals drafted against the (now phase-1) Objective pages; `Home.md` additions.
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
