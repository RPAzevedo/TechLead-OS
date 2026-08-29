---
type: Project
title: Example — Review-bot pilot
description: Example Project page — an AI code-review bot piloted in one team; delete with init.py --remove-examples.
tags: [example, project, ai-review]
resource: https://github.com/example-org/review-bot
owner: human:rafael
stage: pilot
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

# Goal

Reduce review turnaround on the search services without lowering review quality.

# Status

Running in one team; extension to two more is gated on a [decision](../../design/decisions/example-evaluate-vendor-before-extending-pilot.md).[^leadership-notes]

# Components & owners

- Bot service — human:rafael
- Evaluation harness — ownership unclear, see the [open question](../../questions/example-who-owns-the-eval-harness.md)

# Next

- Vendor evaluation, two weeks.

# Risks

- A vendor product makes the in-house bot redundant.[^leadership-notes]

# Decisions

- [Evaluate vendor X before extending the pilot](../../design/decisions/example-evaluate-vendor-before-extending-pilot.md)

[^leadership-notes]: Leadership meeting notes (example)
