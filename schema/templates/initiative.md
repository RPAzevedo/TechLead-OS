---
type: Initiative
title: <Title>
description: <One sentence.>
tags: []
owner: <actor>
stage: <text>
# next_checkpoint: YYYY-MM-DD          # set during ingest, or by /tos-weekly's `checkpoint` answer
# Optional pointers — one canonical each; more than one goes in the body. Uncomment what applies.
# slack: "#channel"                  # quote it: an unquoted # is a YAML comment, and the value would be empty
# jira: ABC-123                      # the initiative or epic key
# confluence: https://<site>/wiki/spaces/<SPACE>/pages/<id>
# rfc: ../../design/rfcs/<slug>.md   # or an https:// URL
sources:
  - id: <source-id>
    resource: <URL, permalink, or raw/notes/… path>
    title: <Human label>
    author: <name or actor>
    last_modified: <the source's own time or version>
generated: { by: claude-code/<model-id>, at: <ISO-8601 with offset> }
# verified: never set by /tos-ingest — see CLAUDE.md §4.6
status: draft
stale_after: <generated.at + 30 d, as YYYY-MM-DD>
---

<!-- Initiative · lives in delivery/initiatives/ · phase 1. A cross-functional effort or a company moving part. Internal updates are Timeline entries, not new pages.
     The commented pointer keys say where the work lives — the channel, the epic, the page — one canonical
     each; uncomment what applies and leave the rest out. -->

# Problem statement

…

# Status

…

# Timeline

…

# Stakeholders

…

# Dependencies

…

# My stance

…

# Open questions

…

[^<source-id>]: <Human label>
