---
type: Attested Computation
title: <Title>
description: <One sentence.>
tags: []
runtime: python
parameters:
  - { name: snapshot, type: path, required: true }
computation: <relative path to the script>
executor:
  resource: <relative path to scripts/metrics/run.py>
  receipt: [computation_sha256, snapshot_sha256, parameters, rows, fetched_at]
attester:
  resource: <relative path to scripts/metrics/attest.py>
sources:
  - id: <source-id>
    resource: <URL, permalink, or raw/notes/… path>
    title: <Human label>
    author: <name or actor>
    last_modified: <the source's own time or version>
generated: { by: claude-code/<model-id>, at: <ISO-8601 with offset> }
# verified: never set by /ingest — see CLAUDE.md §4.6
status: draft
stale_after: <generated.at + 180 d, as YYYY-MM-DD>
---

<!-- Attested Computation · lives in delivery/metrics/ or systems/metrics/ · phase 2. OKF's own type. Authored and verified by the human; the agent supplies parameter values only. Phase 2. -->

# Computation

…

# Examples

…

[^<source-id>]: <Human label>
