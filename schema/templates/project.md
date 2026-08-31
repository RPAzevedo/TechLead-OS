---
type: Project
title: <Title>
description: <One sentence.>
tags: []
resource: <repo or doc URI>
owner: human:<id>
role: <lead|support>
stage: <discovery|build|pilot|rollout|paused|done>
# priority: assigned by /tos-weekly --apply — never set at creation
next_checkpoint: YYYY-MM-DD
sources:
  - id: <source-id>
    resource: <URL, permalink, or raw/notes/… path>
    title: <Human label>
    author: <name or actor>
    last_modified: <the source's own time or version>
generated: { by: claude-code/<model-id>, at: <ISO-8601 with offset> }
# verified: never set by /tos-ingest — see CLAUDE.md §4.6
status: draft
stale_after: <generated.at + 30 d, as YYYY-MM-DD>
---

<!-- Project · lives in delivery/projects/ · phase 1. Something the team delivers. Problem and Expected
     impact say what it solves and what changes if it succeeds; Expected impact links the objective (OKR)
     it advances. Status/Next/Risks/Decisions are the current state; the Weekly log is the record, written
     only by /tos-weekly --apply. -->

# Problem

…

# Expected impact

…

# Status

…

# Components & owners

…

# Next

…

# Risks

…

# Decisions

…

# Weekly log

<!-- One ## YYYY-Www entry per week with movement, newest first; a silent week writes nothing.
     Bold-label bullets, empty labels omitted: **Progress** · **Challenges & risks** ·
     **Blockers & support needed** (name who the support is needed from) · **Open questions & decisions** ·
     **Notes** (tradeoffs, team dynamics — the human's own notes, work content only, CLAUDE.md §5;
     qualitative only, no unattested numbers). -->

[^<source-id>]: <Human label>
