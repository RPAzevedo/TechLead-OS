---
type: Synthesis
title: Example — What depends on the search index
description: Example Synthesis page — a query answer filed back; delete with init.py --remove-examples.
tags: [example, synthesis, search]
audience: ~
sources:
  - id: runbook
    resource: https://example.atlassian.net/wiki/spaces/ENG/pages/9128/Asset+search+runbook
    title: Asset search runbook
    author: Envato Engineering
  - id: rfc-doc
    resource: https://docs.google.com/document/d/EXAMPLE/edit
    title: "RFC: Media pipeline v2"
generated: { by: process:init-examples, at: {{GENERATED_AT}} }
status: draft
stale_after: {{STALE_90}}
---

# Claim

Two systems consume the search index directly, and the proposed [media pipeline v2](../design/rfcs/example-media-pipeline-v2.md) would make a third.[^runbook][^rfc-doc]

# Evidence

- [Asset search](../systems/example-asset-search.md) rebuilds the index nightly.[^runbook]
- The RFC's event-driven pipeline writes into the same index.[^rfc-doc]

# Counterpoints

- The RFC may target a separate index; the document is not explicit.

# What would change my mind

A dependency diagram from the media team showing a separate index.

[^runbook]: Asset search runbook
[^rfc-doc]: RFC: Media pipeline v2
