# TechLead OS (tos) — engine

The engine half of a personal knowledge OS for a lead engineer: Karpathy's LLM Wiki loop (the agent does the bookkeeping, you curate and ask) running on Google's Open Knowledge Format v0.2 (every page says who wrote it, who checked it, when it expires). This repository holds instructions, a type registry, templates and scripts, and **no company data**. The data — `raw/` and `wiki/` — lives in a separate directory named by a config file.

The design, with its decisions, is in `docs/design.html` (also `design.pdf`, `design.md`); eight usage scenarios are in `docs/scenarios.html`; the step-by-step setup and first-fortnight guide is `docs/onboarding.html`; what comes next for the engine is `docs/roadmap.md`. This README is the short version of the onboarding guide.

## Layout

```
engine/                      this repo
├── CLAUDE.md                the schema — what the agent reads first, every run
├── CHANGELOG.md             engine changes only (data changes go to <data.root>/wiki/log.md)
├── config.example.yaml      copy to ~/.config/tos/config.yaml
├── .claude/commands/        /init /pull /ingest /query /lint /verify /weekly (+ gated /sprint /measure /brief /retro)
├── .claude/settings.json    permissions the commands need; settings.local.json grants the data root (untracked)
├── schema/types.md          the type registry: directory, horizon, gate, headings, phase
├── schema/templates/        one template per type, plus the pinned-copy header
├── schema/vault/            Obsidian settings and the Home.md dashboard, installed into the data root by /init
├── schema/examples/         ten worked example pages, installed with /init --with-examples
├── scripts/tos_common.py    config + frontmatter helpers (PyYAML optional)
├── scripts/init.py          creates the data root
├── scripts/okf_lint.py      deterministic lint
└── docs/                    the design

<data.root>/                 e.g. ~/Code/POS/data — created by /init; the Obsidian vault; its own private git repo
├── raw/inbox/               drop zone for notes; pull.md lists pointers to read
├── raw/notes/               your notes after ingest (immutable)
├── raw/pinned/              verbatim copies you asked for with --pin (immutable)
├── raw/metrics/             query snapshots kept for attested numbers (phase 2)
├── wiki/                    the OKF bundle: index.md, log.md, domain directories
└── Home.md, .obsidian/      engine-owned vault files
```

## Quickstart

1. **Config.** `mkdir -p ~/.config/tos && cp config.example.yaml ~/.config/tos/config.yaml`, then edit `data.root`, `data.actor`, and the connector scopes you have. It holds no secrets. `python3 scripts/tos_common.py --show` prints what the engine resolved.
2. **Data root.** From this directory: `python3 scripts/init.py --with-examples` (or `/init --with-examples` inside Claude Code). Open `data.root` in Obsidian as a vault and install the Dataview plugin so `Home.md` works.
3. **Claude Code.** Start it in this directory (`cd engine && claude`) so `CLAUDE.md` loads. `.claude/settings.local.json` grants the data root as an additional working directory — edit the path if yours differs, or start with `claude --add-dir <data.root>`. Connectors are MCP servers configured in Claude Code; the config's `connectors.<name>.provider` must match their names.
4. **First loop.** Drop a note into `raw/inbox/`, run `/ingest`; paste a Confluence or web URL into `raw/inbox/pull.md`, run `/pull`; ask `/query <question>`; run `/lint`; on Monday, `/weekly`, answer inline, `/weekly --apply`.
5. **Examples.** The ten pages tagged `example` are there so the first `/query` has something to find. Remove them with `python3 scripts/init.py --remove-examples`.

## Phases

`rollout.phase` in the config gates connectors and commands: 1 documents (Confluence, web, markdown, Docs); 2 Jira, `/sprint`, `/measure`; 3 Slack, the team domain, `/brief`; 4 Trello (personal), visions, learning, radar, `/retro`. Phases 2–4 are designed (docs/design.html §10) but not yet built; the gated commands say so.

## Sources

- Karpathy, *LLM Wiki* — https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Google Cloud, *Open Knowledge Format v0.2* — https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md and https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals
