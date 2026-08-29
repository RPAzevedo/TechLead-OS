---
type: RFC
title: "Example — RFC: Media pipeline v2"
description: Example RFC page — entry point to a neighbouring team's proposal with review notes; delete with tos-init --remove-examples.
tags: [example, rfc, media]
resource: https://docs.google.com/document/d/EXAMPLE/edit
superseded_by: ~
sources:
  - id: rfc-doc
    resource: https://docs.google.com/document/d/EXAMPLE/edit
    title: "RFC: Media pipeline v2"
    author: Media team
    last_modified: {{DATE-3}}T11:20:00+10:00
generated: { by: process:init-examples, at: {{GENERATED_AT}} }
status: draft
stale_after: {{STALE_30}}
---

# Summary

Replaces the batch media pipeline with an event-driven one; [asset search](../../systems/example-asset-search.md) consumes its output.[^rfc-doc]

# Options

1. Event-driven rebuild (proposed).[^rfc-doc]
2. Keep batch, shorten the window.[^rfc-doc]

# Review notes

- Search index rebuild assumes complete batches; the RFC does not say how partial events are reconciled.
- Ask for a rollback plan before endorsing.

# Standards check

- Observability standard: not yet addressed.[^rfc-doc]
- Data retention standard: addressed.[^rfc-doc]

# Outcome

Pending — review due back to the authors by {{DATE+7}}.

[^rfc-doc]: RFC: Media pipeline v2
