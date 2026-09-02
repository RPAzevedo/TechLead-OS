---
type: Project
title: Example — Review-bot pilot
description: Example Project page — an AI code-review bot piloted in one team; delete with tos-init --remove-examples.
tags: [example, project, ai-review]
resource: https://github.com/example-org/review-bot
owner: human:rafael
role: lead
stage: pilot
priority: 1  # assigned by /tos-weekly --apply; the example shows the state after its first Monday
next_checkpoint: {{DATE+14}}
slack: "#example-review-bot"
jira: REV-142
confluence: https://example.atlassian.net/wiki/spaces/ENG/pages/12345/Review-bot+pilot
rfc: ../../design/rfcs/example-media-pipeline-v2.md
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

# Problem

Review turnaround is the longest step in the delivery cycle for three teams; on the search services it is the loop this quarter's OKR sets out to cut.[^leadership-notes]

# Expected impact

Median review turnaround on the search services halved by quarter end, with no rise in post-merge defects attributed to review misses — the [team objective](../objectives/example-review-turnaround-okr.md) this project advances.[^leadership-notes]

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

# Weekly log

## {{ISO_WEEK}}

- **Progress**: pilot running in one team; vendor evaluation started.[^leadership-notes]
- **Challenges & risks**: a vendor product could make the in-house bot redundant.[^leadership-notes]
- **Blockers & support needed**: none this week.
- **Open questions & decisions**: [who owns the evaluation harness?](../../questions/example-who-owns-the-eval-harness.md)
- **Notes**: a vendor shipped an agentic review product last week, which is what put the extension behind a decision rather than a date.[^leadership-notes]

[^leadership-notes]: Leadership meeting notes (example)
