# Type registry

OKF leaves `type` producer-defined. This registry is the engine's set. **From** is the rollout phase in which the type first appears (`rollout.phase` in the config); **Horizon** feeds `stale_after` (`generated.at` + horizon; `—` means the page is a record and never expires); **Stable requires** is the gate before `status: stable` (H = human-reviewed, M = machine-confirmed, `—` = may be stable on write). Body headings are the template's H1 sections, in order.

| Type | From | Lives in | Horizon | Stable requires | Body headings |
|---|---|---|---|---|---|
| Source | P1 | `sources/` | — | M (cross-check re-fetches the source) | Summary · Key claims · Relevance · Open questions |
| Concept | P1 | `concepts/` | 365 d | H | Definition · How it works · Where it shows up · Open questions |
| Decision | P1 | `design/decisions/` | — | H | Context · Options · Decision · Consequences · Standards applied |
| RFC | P1 | `design/rfcs/` | 30 d while draft, then — | H | Summary · Options · Review notes · Standards check · Outcome |
| Project | P1 | `delivery/projects/` | 30 d | H | Goal · Status · Components & owners · Next · Risks · Decisions |
| Initiative | P1 | `delivery/initiatives/` | 30 d | H | Problem statement · Status · Timeline · Stakeholders · Dependencies · My stance · Open questions |
| System | P1 | `systems/` | 90 d | H | Purpose · Ownership · Operational standards · KTLO · Dependencies · Runbooks & links |
| Question | P1 | `questions/` | 60 d | — | Question · What we know · Who can resolve it · Resolution |
| Synthesis | P1 | `syntheses/` | 90 d | H | Claim · Evidence · Counterpoints · What would change my mind |
| Review | P1 | `reviews/` | — | — | generated sections (see the weekly command) |
| Objective | P2 | `delivery/objectives/` | 90 d | H | Objective · Key results · Sprint goals · Status |
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
| `owner` | Project, Initiative, System, Learning Path | actor string of the owner |
| `stage` | Project, Initiative | free text: discovery, build, pilot, rollout, done |
| `next_checkpoint` | Project, Initiative | `YYYY-MM-DD`; the weekly review flags it once passed |
| `superseded_by` | Decision, RFC | relative link to the page that replaced it |
| `audience` | Synthesis (briefs) | who the synthesis was written for |
| `review_due` | Drill | `YYYY-MM-DD` |
| `pinned` | Source | `true` if a verbatim copy exists under `raw/pinned/` |

## Status lifecycle

`draft` (written by the agent, or a proposal) → `stable` (the gate above is met) → `deprecated` (superseded; keep the page, say what replaced it). Always explicit: OKF treats a missing `status` as `stable`.

## Shared directories

`concepts/`, `sources/`, `syntheses/`, `questions/`, `reviews/`, `radar/` are shared across the five domains (`delivery/`, `team/`, `systems/`, `design/`, `learning/`). Every directory carries an `index.md`.
