# TechLead OS (tos) — engine

Engine version **0.7.3** (see `CHANGELOG.md`).

The engine half of a personal knowledge OS for a lead engineer: Karpathy's LLM Wiki loop (the agent does the bookkeeping, you curate and ask) running on Google's Open Knowledge Format v0.2 (every page says who wrote it, who checked it, when it expires). This repository holds instructions, a type registry, templates and scripts, and **no company data**. The data — `raw/` and `wiki/` — lives in a separate directory named by a config file.

The design, with its decisions, is in `docs/design.html` (also `design.md`); eight usage scenarios are in `docs/scenarios.html`; the step-by-step setup and first-fortnight guide is `docs/onboarding.html`; what comes next for the engine is `docs/roadmap.md`. This README is the short version of the onboarding guide.

## Layout

```
engine/                      this repo
├── CLAUDE.md                the schema — what the agent reads first, every run
├── CHANGELOG.md             engine changes only (data changes go to <data.root>/wiki/log.md)
├── config.example.yaml      copy to ~/.config/tos/config.yaml
├── .claude/commands/        one file per operation, all named tos-* — see Commands below
├── .claude/settings.json    permissions the commands need, and the connector write-tool denies; settings.local.json (untracked, you create it) grants the data root
├── schema/types.md          the type registry: directory, horizon, gate, headings, phase
├── schema/templates/        one template per type, plus the pinned-copy header
├── schema/vault/            Obsidian settings and the Home.md dashboard, installed into the data root by /tos-init
├── schema/examples/         eleven worked example pages and one raw note, installed with /tos-init --with-examples
├── pyproject.toml           the package: dependencies and the tos-* entry points
├── src/tos/common.py        config + frontmatter + registry helpers (YAML is parsed strictly)
├── src/tos/bundle.py        the write-side helpers: log bullets, index entries, frontmatter edits
├── src/tos/init.py          creates the data root            → tos-init
├── src/tos/lint.py          deterministic lint and --fix     → tos-lint
├── src/tos/new_page.py      page from template + registry    → tos-new
├── src/tos/log_add.py       canonical log bullet             → tos-log
├── src/tos/index_add.py     add/refresh an index entry       → tos-index
├── src/tos/verify_mark.py   verified entries, gates enforced → tos-verify-mark
├── src/tos/doctor.py        onboarding checklist             → tos-doctor
├── src/tos/metrics/         the attested-computation executor (phase 2; a README for now)
├── tests/                   pytest
└── docs/                    the design

<data.root>/                 wherever you point data.root — created by /tos-init; the Obsidian vault; its own private git repo
├── raw/inbox/               drop zone for notes; pull.md lists pointers to read
├── raw/notes/               your notes after ingest (immutable)
├── raw/pinned/              verbatim copies you asked for with --pin (immutable)
├── raw/metrics/             query snapshots kept for attested numbers (phase 2)
├── raw/assets/              images referenced by notes and pages
├── wiki/                    the OKF bundle: index.md, log.md, domain directories
└── Home.md, .obsidian/      engine-owned vault files
```

## Install

Requires [uv](https://docs.astral.sh/uv/) (`brew install uv`) and git. uv fetches
the Python in `.python-version` itself, so nothing else has to be installed.

```
uv sync
```

That creates `.venv`, installs the engine editable with its dependencies
(PyYAML), and puts the commands on `uv run`:

| command | what it does |
| --- | --- |
| `uv run tos-config` | print the resolved config: paths, actor, phase |
| `uv run tos-init [--with-examples \| --remove-examples \| --dry-run]` | create or refresh the data root |
| `uv run tos-lint [--json] [--fix] [--today YYYY-MM-DD]` | the deterministic half of `/tos-lint`; `--fix` repairs the mechanical findings; exit 1 on a conformance error |
| `uv run tos-new <Type> <slug> --title "…" […]` | create a page from its template, frontmatter computed from the registry, indexed |
| `uv run tos-log <Label> <text…> [--date …]` | append a bullet to wiki/log.md in the canonical shape, newest first |
| `uv run tos-index <page.md> […]` | add or refresh the page's line in its directory index (`--deprecated` moves it) |
| `uv run tos-verify-mark <page.md> --by <actor> […]` | append a `verified` entry — `process:*` freely, `human:` only via `/tos-verify` |
| `uv run tos-doctor [--json]` | the onboarding checklist: config, layout, git, connector names vs `claude mcp list` |

Run them from this directory. The engine finds `schema/` by walking up from the
package to the checkout root; set `$TOS_ENGINE_ROOT` if you ever need to point
it somewhere else.

## Commands

Every operation is a slash command in Claude Code, named `/tos-<verb>` so it does
not collide with Claude Code's own `/init` and is recognisable in a session with
other commands loaded. The full procedure for each is in
`.claude/commands/tos-<verb>.md`.

| command | what it does | phase |
| --- | --- | --- |
| `/tos-init [--with-examples \| --remove-examples \| --dry-run]` | create or refresh the data root described by the config (runs `tos-init`) | 1 |
| `/tos-pull <pointer \| feed-name> [--pin]` | read a source through a connector and write its Source page; no verbatim copy unless `--pin` | 1 |
| `/tos-ingest [path]` | turn the notes in `raw/inbox/` (or one file) into wiki pages | 1 |
| `/tos-query <question>` | answer from the wiki, citing each page with its trust tier and age | 1 |
| `/tos-lint [--fix]` | health-check the bundle: the `tos-lint` script, then the agent pass | 1 |
| `/tos-verify <page> \| --queue` | promote a page you have read — the only way a `human:*` verification is ever written | 1 |
| `/tos-weekly [--apply]` | the Monday tick: the ranked project portfolio, then lint, queues, expiries, RFCs, systems, questions; `--apply` writes each project's weekly entry and executes your inline answers | 1 |
| `/tos-sprint` | sprint-boundary review with attested metrics | 2 |
| `/tos-measure` | run an Attested Computation over a metric snapshot | 2 |
| `/tos-brief` | outbound update for an audience, from human-reviewed pages only | 3 |
| `/tos-retro` | quarterly retro: objectives, visions, systems, people re-verification, engine pruning | 4 |

The commands above phase 1 exist but refuse to run until `rollout.phase` in the
config reaches their phase.

## Connector safety

Guardrail 11 says connectors are read-only. `.claude/settings.json` enforces it: `permissions.deny` lists the
write-capable tools of the Google Drive, Slack and Atlassian servers — creating, updating, sharing, trashing,
posting, commenting, transitioning — so the harness refuses the call rather than trusting the agent to decline.
Reads are untouched, so `/tos-pull` works as before.

Permission rules match a tool by its exact name, and MCP tool names are `mcp__<server>__<tool>`, where `<server>`
is whatever you called the server in Claude Code. **A name that matches nothing is silently ignored** — it raises no
error and appears to work. That is not hypothetical: the Atlassian entries added in 0.7.1 guarded `atlassian` and
`claude_ai_Atlassian`, and the servers on the first real install turned out to be `claude_ai_Jira` and
`plugin_atlassian_atlassian`, so not one of them was ever in force.

The list therefore covers nine server names across the three connectors: `claude_ai_Google_Drive` and `gdrive`;
`slack` and `claude_ai_Slack`; `atlassian`, `claude_ai_Atlassian`, `claude_ai_Jira`, `claude_ai_Confluence` and
`plugin_atlassian_atlassian`. An entry naming a server you do not have costs nothing, so breadth is cheap and a gap
is not.

**Confirm it against your own install rather than trusting this list.** The Google Drive entries were verified
against a live server, and the two Atlassian servers above were observed on one — but only their *read* tools were
seen directly. Every write-tool name here is inferred from the server's own vocabulary, which is the same kind of
assumption that made the 0.7.1 entries inert. After wiring a connector, ask Claude Code which tools that server
exposes, and add any this list misses.

## Quickstart

1. **Config.** `mkdir -p ~/.config/tos && cp config.example.yaml ~/.config/tos/config.yaml`, then replace the `CHANGE_ME` placeholders in `data.root` (anywhere you like — it need not sit next to the engine) and `data.actor`, and set `data.timezone` and the connector scopes you have. It holds no secrets. `uv run tos-config` prints what the engine resolved.
2. **Data root.** `uv run --directory <this repo> tos-init --with-examples` (or `/tos-init --with-examples` inside Claude Code). Open `data.root` in Obsidian as a vault and install the Dataview plugin so `Home.md` works.
3. **Claude Code.** Start it in this directory so `CLAUDE.md` loads, and grant it the data root: `claude --add-dir <data.root>`. To stop repeating the flag, put the absolute path in `permissions.additionalDirectories` in `.claude/settings.local.json` — untracked and per-machine, so it does not exist until you write it. Connectors are MCP servers configured in Claude Code; the config's `connectors.<name>.provider` must match their names.
4. **First loop.** Drop a note into `raw/inbox/`, run `/tos-ingest`; paste a Confluence or web URL into `raw/inbox/pull.md`, run `/tos-pull`; ask `/tos-query <question>`; run `/tos-lint`; on Monday, `/tos-weekly`, answer inline, `/tos-weekly --apply`.
5. **Examples.** The eleven pages tagged `example` are there so the first `/tos-query` has something to find. Remove them with `uv run tos-init --remove-examples`.

## Development Phases

`rollout.phase` in the config gates connectors and commands:
1. documents (Confluence, web, markdown, Docs);
2. Jira, `/tos-sprint`, `/tos-measure`;
3. Slack, the team domain, `/tos-brief`;
4. Trello (personal), visions, learning, radar, `/tos-retro`.

Phases 2–4 are designed ([docs/design.html §10](docs/design.html)) but not yet built; the gated commands say so.

## Development

```
uv run pytest          # frontmatter contract, every shipped page, init → lint end to end
uv run ruff check      # lint
```

`tests/test_yaml.py` is the regression guard for OKF conformance: malformed
frontmatter must be reported, never silently dropped.

## Sources

- Karpathy, *LLM Wiki* — https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Google Cloud, *Open Knowledge Format v0.2* — https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md and https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals
