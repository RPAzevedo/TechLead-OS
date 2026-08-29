---
type: Initiative
title: Example — AI-assisted code review rollout
description: Example Initiative page — the company-wide rollout the pilot feeds; delete with tos-init --remove-examples.
tags: [example, initiative, ai-review]
owner: human:example-director
stage: rollout planning
next_checkpoint: {{DATE+14}}
sources:
  - id: leadership-notes
    resource: ../../../raw/notes/example-leadership-meeting-notes.md
    title: Leadership meeting notes (example)
    author: human:rafael
    last_modified: {{DATE-1}}
generated: { by: process:init-examples, at: {{GENERATED_AT}} }
status: draft
stale_after: {{STALE_30}}
---

# Problem statement

Review turnaround is the longest step in the delivery cycle for three teams.[^leadership-notes]

# Status

Pilot running in one team; extension gated on a vendor evaluation.[^leadership-notes]

# Timeline

- {{DATE-1}} — leadership asks for a data-handling brief before the pilot extends.[^leadership-notes]

# Stakeholders

- Security — wants the data-handling brief first.[^leadership-notes]

# Dependencies

- [Review-bot pilot](../projects/example-review-bot-pilot.md)

# My stance

Evaluate before extending; see the [decision](../../design/decisions/example-evaluate-vendor-before-extending-pilot.md).

# Open questions

- Who owns the evaluation harness? ([question](../../questions/example-who-owns-the-eval-harness.md))

[^leadership-notes]: Leadership meeting notes (example)
