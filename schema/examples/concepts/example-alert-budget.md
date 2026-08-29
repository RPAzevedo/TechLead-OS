---
type: Concept
title: Example — Alert budget
description: Example Concept page — an alert budget as the error-budget idea applied to paging; delete with init.py --remove-examples.
tags: [example, operations, slo]
sources:
  - id: sre-book
    resource: https://sre.google/sre-book/monitoring-distributed-systems/
    title: Monitoring Distributed Systems (SRE book)
    author: Google
  - id: thread
    resource: ../sources/example-alert-budget-thread.md
    title: "#team-search thread: alert budget breach"
generated: { by: process:init-examples, at: {{GENERATED_AT}} }
status: draft
stale_after: {{STALE_365}}
---

# Definition

A cap on how often a system may page people in a period, treated like an error budget: when it is spent, noise reduction takes priority over features.[^sre-book]

# How it works

Alerts are counted against the budget; a breach triggers a review of thresholds and causes, not just a fix of the immediate alert.[^sre-book]

# Where it shows up

[Asset search](../systems/example-asset-search.md) breached its budget after the index migration.[^thread]

# Open questions

- Should the budget be per system or per on-call rota?

[^sre-book]: Monitoring Distributed Systems (SRE book)
[^thread]: #team-search thread: alert budget breach
