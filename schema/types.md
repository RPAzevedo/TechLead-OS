# Type registry

OKF leaves `type` producer-defined. This registry is the engine's set. **From** is the rollout phase in which the type first appears (`rollout.phase` in the config); **Horizon** feeds `stale_after` (`generated.at` + horizon; `—` means the page is a record and never expires); **Stable requires** is the gate before `status: stable` (H = human-reviewed, M = machine-confirmed, `—` = may be stable on write). Body headings are the template's H1 sections, in order.

| Type | From | Lives in | Horizon | Stable requires | Body headings |
|---|---|---|---|---|---|
| Source | P1 | `sources/` | — | M (cross-check re-fetches the source) | Summary · Key claims · Relevance · Open questions |
| Concept | P1 | `concepts/` | 365 d | H | Definition · How it works · Where it shows up · Open questions |
| Decision | P1 | `design/decisions/` | — | H | Context · Options · Decision · Consequences · Standards applied |
| RFC | P1 | `design/rfcs/` | 30 d while draft, then — | H | Summary · Options · Review notes · Standards check · Outcome |
| Project | P1 | `delivery/projects/` | 30 d | H | Problem · Expected impact · Status · Components & owners · Next · Risks · Decisions · Weekly log |
| Initiative | P1 | `delivery/initiatives/` | 30 d | H | Problem statement · Status · Timeline · Stakeholders · Dependencies · My stance · Open questions |
| System | P1 | `systems/` | 90 d | H | Purpose · Ownership · Operational standards · KTLO · Dependencies · Runbooks & links |
| Question | P1 | `questions/` | 60 d | — | Question · What we know · Who can resolve it · Resolution |
| Synthesis | P1 | `syntheses/` | 90 d | H | Claim · Evidence · Counterpoints · What would change my mind |
| Review | P1 | `reviews/` | — | — | generated sections (see the weekly command) |
| Objective | P1 | `delivery/objectives/` | 90 d | H | Objective · Key results · Sprint goals · Status |
| Attested Computation | P2 | `delivery/metrics/`, `systems/metrics/` | 180 d | H (the human authors it) | Computation · Examples |
| Person | P3 | `team/people/` | 90 d | H, always | Role · Growth focus · Ownership delegated · Agreed actions · Thread |
| Stakeholder | P3 | `team/stakeholders/` | 90 d | H, always | Role & needs · Positions · Cadence & last contact · Thread |
| Playbook | P3 | `team/playbooks/` | 180 d | H | When to use · Steps · Examples · Anti-patterns |
| Vision | P4 | `design/visions/` | 180 d | H | Vision · Principles · Plan · Business alignment · Signals watched |
| Learning Path | P4 | `learning/paths/` | 90 d | H | Goal · Sequence · Exit criteria · Progress |
| Signal | P4 | `radar/signals/` | 30 d | — | What happened · Why it matters to us · Links |
| Team | P4 | `team/team.md` | 90 d | H | Mission · People · Rituals · Focus |
| Drill | P4 | `learning/drills/` | by `review_due` | — | Questions · Answers |

## Extension fields

Ordinary frontmatter keys; OKF consumers must not reject unknown keys.

| Field | Types | Meaning |
|---|---|---|
| `owner` | Project, Initiative, System, Learning Path | actor string of the owner — the work's owner, not necessarily the human |
| `role` | Project | the human's relationship to the project: lead or support |
| `stage` | Project, Initiative | Project: one of discovery, build, pilot, rollout, paused, done — paused and done end its active life. Initiative: free text |
| `priority` | Project | positive integer, 1 = highest, unique and contiguous across active projects; written only by `/tos-weekly --apply`, absent before a project's first Monday and after it leaves active |
| `level` | Objective | company or team |
| `team` | Objective | the team whose objective it is, as a slug; required at `level: team`, absent at `level: company` |
| `quarter` | Objective | `YYYY-Qn`, e.g. 2026-Q3 |
| `next_checkpoint` | Project, Initiative | `YYYY-MM-DD`; the weekly review flags it once passed |
| `superseded_by` | Decision, RFC | relative link to the page that replaced it |
| `audience` | Synthesis (briefs) | who the synthesis was written for |
| `review_due` | Drill | `YYYY-MM-DD` |
| `pinned` | Source | `true` if a verbatim copy exists under `raw/pinned/` |

## Projects and objectives

A Project is **active** when `status` is not `deprecated` and `stage` is not `paused` or `done`. Active projects are ranked by `priority` and carry a weekly record; they surface in the weekly review's portfolio section rather than in the verify and expiry queues. The *Weekly log* is written only by `/tos-weekly --apply`: one `## YYYY-Www` entry per week with movement, newest first, bold-label bullets from **Progress**, **Challenges & risks**, **Blockers & support needed**, **Open questions & decisions**, **Notes**; a silent week writes no entry. A Project links the objective(s) it advances from *Expected impact*; a team Objective names its `team` and links its company objective — of the same quarter — from *Objective*. The links are ordinary body links, no frontmatter field. Objective slugs are quarter-prefixed (`2026-q3-<slug>`).

## Status lifecycle

`draft` (written by the agent, or a proposal) → `stable` (the gate above is met) → `deprecated` (superseded; keep the page, say what replaced it). Always explicit: OKF treats a missing `status` as `stable`.

## Shared directories

`concepts/`, `sources/`, `syntheses/`, `questions/`, `reviews/`, `radar/` are shared across the five domains (`delivery/`, `team/`, `systems/`, `design/`, `learning/`). Every directory carries an `index.md`.
