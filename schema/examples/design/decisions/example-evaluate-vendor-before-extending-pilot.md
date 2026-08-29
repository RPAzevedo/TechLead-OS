---
type: Decision
title: Example — Evaluate vendor X before extending the review-bot pilot
description: Example Decision (proposed) — gate the pilot extension on a vendor evaluation; delete with tos-init --remove-examples.
tags: [example, decision, ai-review]
superseded_by: ~
sources:
  - id: leadership-notes
    resource: ../../../raw/notes/example-leadership-meeting-notes.md
    title: Leadership meeting notes (example)
    author: human:rafael
    last_modified: {{DATE-1}}
generated: { by: process:init-examples, at: {{GENERATED_AT}} }
status: draft
stale_after: ~
---

# Context

The [review-bot pilot](../../delivery/projects/example-review-bot-pilot.md) is due to extend to two more teams; a vendor shipped an agentic review product last week.[^leadership-notes]

# Options

1. Extend the pilot as planned.
2. Run a two-week evaluation of the vendor first (proposed).
3. Pause the pilot.

# Decision

Proposed: option 2. Extending without an evaluation risks building on a tool the vendor makes redundant.[^leadership-notes]

# Consequences

- The [rollout initiative](../../delivery/initiatives/example-ai-assisted-code-review-rollout.md) checkpoint moves by two weeks.

# Standards applied

- Vendor evaluation checklist (Security review required before any pilot extension).

[^leadership-notes]: Leadership meeting notes (example)
