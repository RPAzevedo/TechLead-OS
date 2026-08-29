---
type: System
title: Example — Asset search
description: Example System page — the search service behind marketplace browse; delete with init.py --remove-examples.
tags: [example, system, search]
resource: https://github.com/example-org/asset-search
owner: human:rafael
sources:
  - id: thread
    resource: ../sources/example-alert-budget-thread.md
    title: "#team-search thread: alert budget breach"
    last_modified: {{DATE-3}}T17:02:00+10:00
  - id: runbook
    resource: https://example.atlassian.net/wiki/spaces/ENG/pages/9128/Asset+search+runbook
    title: Asset search runbook
    author: Envato Engineering
    last_modified: {{DATE-8}}
generated: { by: process:init-examples, at: {{GENERATED_AT}} }
status: draft
stale_after: {{STALE_90}}
---

# Purpose

Serves marketplace browse and search. Depends on the [search index](../concepts/example-alert-budget.md) being rebuilt nightly.[^runbook]

# Ownership

Owner of record: human:rafael. Supported by the team; escalation path in the runbook.[^runbook]

# Operational standards

- [x] On-call rota and escalation path documented[^runbook]
- [ ] Alert budget within target — breached {{DATE-3}}[^thread]
- [x] Dashboards linked from the runbook[^runbook]

# KTLO

- Fix the noisy p95 latency alert before the next sprint (from the [thread](../sources/example-alert-budget-thread.md)).[^thread]

# Dependencies

- Media pipeline (see the [RFC](../design/rfcs/example-media-pipeline-v2.md) for the proposed v2).

# Runbooks & links

- [Runbook](https://example.atlassian.net/wiki/spaces/ENG/pages/9128/Asset+search+runbook)
- Dependents: [search index dependents](../syntheses/example-search-index-dependents.md)

[^thread]: #team-search thread: alert budget breach
[^runbook]: Asset search runbook
