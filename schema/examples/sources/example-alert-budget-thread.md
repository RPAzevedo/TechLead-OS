---
type: Source
title: "Example — #team-search thread: alert budget breach"
description: Example Source page — a summarised chat thread about a breached alert budget; delete with init.py --remove-examples.
tags: [example, slack, systems]
pinned: false
sources:
  - id: thread
    resource: https://example.slack.com/archives/C0123ABCD/p1756368120000000
    title: "#team-search thread, 6 participants"
    author: "#team-search"
    last_modified: {{DATE-3}}T17:02:00+10:00
generated: { by: process:init-examples, at: {{GENERATED_AT}} }
status: draft
stale_after: ~
---

# Summary

The search-latency alert fired repeatedly over three days and burned the alert budget for [asset search](../systems/example-asset-search.md) early. The system owner asked for a KTLO item to fix the noisy alert before the next sprint, and two participants questioned whether the latency SLO is still the right one.

# Key claims

- The alert budget was breached three days early — "we burned it three days early".[^thread]
- The owner wants a KTLO item for the noisy latency alert before the next sprint.[^thread]
- Two participants asked whether the p95 latency SLO should be revisited after the index migration.[^thread]

# Relevance

Feeds the *Operational standards* and *KTLO* sections of the System page, and raises an [open question](../questions/example-who-owns-the-eval-harness.md) about ownership of adjacent tooling.

# Open questions

- Was the breach caused by the migration or by alert thresholds set before it?

[^thread]: #team-search thread, 6 participants
