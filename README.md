# TechLead OS (tos) — engine

Engine version **0.5.3** (see `CHANGELOG.md`).

The engine half of a personal knowledge OS for a lead engineer: Karpathy's LLM Wiki loop (the agent does the bookkeeping, you curate and ask) running on Google's Open Knowledge Format v0.2 (every page says who wrote it, who checked it, when it expires). This repository holds instructions, a type registry, templates and scripts, and **no company data**. The data — `raw/` and `wiki/` — lives in a separate directory named by a config file.

The design, with its decisions, is in `docs/design.html` (also `design.pdf`, `design.md`); eight usage scenarios are in `docs/scenarios.html`; the step-by-step setup and first-fortnight guide is `docs/onboarding.html`; what comes next for the engine is `docs/roadmap.md`. This README is the short version of the onboarding guide.

## Layout

```
engine/                      this repo
├── CLAUDE.md                the schema — what the agent reads first, every run
├── CHANGELOG.md             engine changes only (data changes go to <data.root>/wiki/log.md)
├── config.example.yaml      copy to ~/.config/tos/config.yaml
├── .claude/commands/        /init /pull /ingest /query /lint /verify /weekly (+ gated /sprint /measure /brief /retro)
├── .claude/settings.json    permissions the commands need; settings.local.json (untracked, you create it) grants the data root
├── schema/types.md          the type registry: directory, horizon, gate, headings, phase
├── schema/templates/        one template per type, plus the pinned-copy header
├── schema/vault/            Obsidian settings and the Home.md dashboard, installed into the data root by /init
├── schema/examples/         ten worked example pages and one raw note, installed with /init --with-examples
├── pyproject.toml           the package: dependencies and the tos-* entry points
├── src/tos/common.py        config + frontmatter helpers (YAML is parsed strictly)
├── src/tos/init.py          creates the data root            → tos-init
├── src/tos/lint.py          deterministic lint               → tos-lint
├── src/tos/metrics/         the attested-computation executor (phase 2; a README for now)
├── tests/                   pytest
└── docs/                    the design

<data.root>/                 e.g. ~/Code/TechLead_OS/data — created by /init; the Obsidian vault; its own private git repo
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
(PyYAML), and puts three commands on `uv run`:

| command | what it does |
| --- | --- |
| `uv run tos-config` | print the resolved config: paths, actor, phase |
| `uv run tos-init [--with-examples \| --remove-examples \| --dry-run]` | create or refresh the data root |
| `uv run tos-lint [--json] [--today YYYY-MM-DD]` | the deterministic half of `/lint`; exit 1 on a conformance error |

Run them from this directory. The engine finds `schema/` by walking up from the
package to the checkout root; set `$TOS_ENGINE_ROOT` if you ever need to point
it somewhere else.

## Quickstart

1. **Config.** `mkdir -p ~/.config/tos && cp config.example.yaml ~/.config/tos/config.yaml`, then edit `data.root`, `data.actor`, `data.timezone`, and the connector scopes you have. It holds no secrets. `uv run tos-config` prints what the engine resolved.
2. **Data root.** From this directory: `uv run tos-init --with-examples` (or `/init --with-examples` inside Claude Code). Open `data.root` in Obsidian as a vault and install the Dataview plugin so `Home.md` works.
3. **Claude Code.** Start it in this directory so `CLAUDE.md` loads, and grant it the data root: `claude --add-dir <data.root>`. To stop repeating the flag, put the absolute path in `permissions.additionalDirectories` in `.claude/settings.local.json` — untracked and per-machine, so it does not exist until you write it. Connectors are MCP servers configured in Claude Code; the config's `connectors.<name>.provider` must match their names.
4. **First loop.** Drop a note into `raw/inbox/`, run `/ingest`; paste a Confluence or web URL into `raw/inbox/pull.md`, run `/pull`; ask `/query <question>`; run `/lint`; on Monday, `/weekly`, answer inline, `/weekly --apply`.
5. **Examples.** The ten pages tagged `example` are there so the first `/query` has something to find. Remove them with `uv run tos-init --remove-examples`.

## Development Phases

`rollout.phase` in the config gates connectors and commands:
1. documents (Confluence, web, markdown, Docs);
2. Jira, `/sprint`, `/measure`;
3. Slack, the team domain, `/brief`;
4. Trello (personal), visions, learning, radar, `/retro`.

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
