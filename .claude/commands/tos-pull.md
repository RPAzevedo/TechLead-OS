---
description: Read a source through a connector and write its Source page (no verbatim copy unless --pin)
argument-hint: <pointer | feed-name> [--pin]
---
Follow CLAUDE.md §0, then §4.2 exactly. Pointer(s): $ARGUMENTS — or, if none given, every non-comment line of `raw/inbox/pull.md`.

For each pointer:
1. Identify the connector (confluence page URL → `confluence`; Google Doc URL → `gdocs`; Slack permalink → `slack`; JQL or issue key → `jira`; Trello board → `trello`; a path inside a configured repo → `md`; any other URL → `web`).
2. Check `rollout.phase` in the config allows that connector (phase 1: confluence, web, md, gdocs; jira from phase 2; slack from phase 3; trello from phase 4) and that the pointer is inside the connector's `scope`. If not, stop for that pointer and say which setting would allow it. Never DMs. Never a write to any connected system.
3. Fetch through the connector named by `connectors.<name>.provider`, read-only. Read it fully.
4. Run the `/tos-ingest` procedure on what you read (CLAUDE.md §4.3), writing `wiki/sources/YYYY-MM-DD-<slug>.md` from `schema/templates/source.md` and touching the pages the source feeds. Record in the Source page's `sources[0]`: the pointer as `resource`, the source's title and author, and its own modified time or version as `last_modified`.
5. Keep nothing verbatim — unless `--pin` was given: then also write the full text to `raw/pinned/<connector>/YYYY-MM-DD-<slug>.md` with the header from `schema/templates/pinned-header.md`, and set `pinned: true` on the Source page. A re-pin is a new dated file; never overwrite.
6. Remove the pointer's line from `pull.md` if it came from there.
7. `uv run tos-log Pull "<connector> <short pointer> → [Source](sources/<file>), not pinned"` (or `pinned`). Then the `Ingest` line(s) from step 4.
8. Commit `data.root` with the log line as the message.

Finish by listing the pages created or updated with their paths, and anything you could not do and why.
