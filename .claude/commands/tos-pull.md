---
description: Read a source through a connector and write its Source page (no verbatim copy unless --pin)
argument-hint: <pointer | feed-name> [--pin]
---
Follow CLAUDE.md §0, then §4.2 exactly. Pointer(s): $ARGUMENTS — or, if none given, every non-comment line of `raw/inbox/pull.md`.

A Project's or Initiative's `confluence` or `jira` frontmatter pointer is a legal pointer here, subject to the same checks as any other.

For each pointer:
1. Identify the connector (confluence page URL → `confluence`; Google Docs, Sheets or Slides URL, or a `drive.google.com` file or folder URL → `gdrive`; Jira issue key, issue URL or JQL → `jira`; Slack permalink or `"#channel, <window>"` → `slack`; Trello board → `trello`; a path inside a repo in `connectors.md.scope.repos` → `md`; any other URL → `web`). A `gdocs` key in an older config is `gdrive` under its old name.
2. Reads are bounded by the human's own account permissions, not by the engine: `confluence`, `gdrive`, `jira`, `slack` and `web` have no scope and are readable in every phase, so a source the account cannot open is a failed fetch to report, not to work around. A `scope` left under one of them in an older config is ignored. Three checks remain; if one fails, stop for that pointer and say which setting or rule would allow it: a local path must be inside a repo in `connectors.md.scope.repos`; `trello` waits for `rollout.phase: 4` and reads only the boards in `connectors.trello.scope.boards`; and a Slack pointer must not be a DM or group DM — check the conversation's type through the connector before reading anything in it. Never a write to any connected system.
3. Fetch through the connector named by `connectors.<name>.provider`, read-only. Read it fully.
   - `gdrive`: read the file through the provider's content tool (on the claude.ai server, `read_file_content`, which renders Docs, Sheets, Slides, PDFs, Office files and images as text). `last_modified` is the file's `modifiedTime`. Excerpts say where they come from: the tab and cells in a Sheet, the slide number in a deck.
   - A broad pointer: a Drive folder is each file directly inside it, one Source page per file — list them and ask first if there are more than ten. A JQL query or a Slack channel window is one Source page summarising what it returned, citing the issue keys or permalinks it rests on; its `last_modified` is the newest `updated` time or message among them.
4. Run the `/tos-ingest` procedure on what you read (CLAUDE.md §4.3), writing `wiki/sources/YYYY-MM-DD-<slug>.md` from `schema/templates/source.md` and touching the pages the source feeds. Record in the Source page's `sources[0]`: the pointer as `resource`, the source's title and author, and its own modified time or version as `last_modified`.
5. Keep nothing verbatim — unless `--pin` was given: then also write the full text to `raw/pinned/<connector>/YYYY-MM-DD-<slug>.md` with the header from `schema/templates/pinned-header.md`, and set `pinned: true` on the Source page. A re-pin is a new dated file; never overwrite.
6. Remove the pointer's line from `pull.md` if it came from there.
7. `uv run log Pull "<connector> <short pointer> → [Source](sources/<file>), not pinned"` (or `pinned`). Then the `Ingest` line(s) from step 4.
8. Commit `data.root` with the log line as the message.

Finish by listing the pages created or updated with their paths, and anything you could not do and why.
