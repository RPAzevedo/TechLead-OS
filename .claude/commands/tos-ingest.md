---
description: Turn notes in raw/inbox (or one file) into wiki pages
argument-hint: [path]
---
Follow CLAUDE.md §0, then §4.3 exactly. Input: $ARGUMENTS — a file path, or nothing, meaning every file in `raw/inbox/` except `pull.md`.

For each input:
1. Read it. Decide what it is (meeting notes, 1:1 notes, an incident report, a clipped page, a transcript).
2. Write `wiki/sources/YYYY-MM-DD-<slug>.md` from `schema/templates/source.md`: a summary; the load-bearing lines quoted as short excerpts under *Key claims*, each footnoted; a `sources` entry whose `resource` is the file's future path under `raw/notes/` (or the clip's URL), with `title`, `author` and `last_modified`.
3. Extract what `schema/types.md` recognises for the current `rollout.phase` (phase 1: Concept, Decision, RFC, Project, Initiative, Objective, System, Question, Synthesis). Create pages from their templates or update existing ones — an internal update goes into an existing page's *Timeline* or *Status* (for a Project: *Status*, *Next*, *Risks* or *Decisions* — never its *Weekly log*, which only `/tos-weekly --apply` writes), not a new page. An OKR document yields one Objective page per objective, with `level`, `quarter` and a quarter-prefixed slug; where a source states a project's problem or intended impact, it goes under *Problem* or *Expected impact* with a link to the objective it advances. Where a source states a Project's or Initiative's canonical Slack channel, Jira initiative or epic key, Confluence page or RFC, set the matching frontmatter pointer (`slack` — quoted, or YAML reads the `#` as a comment — `jira`, `confluence`, `rfc`), one value each, further ones as body links; do not restate it in *Status* and do not create a page for it. Typically 5–15 touches. Never create a later-phase type.
4. Footnote every new claim to a `sources[].id`. On contradiction with an existing page, add to that page's *Open questions* rather than overwriting, and mention it in your summary.
5. New pages are created with `uv run tos-new <Type> <slug> --title "…" --description "…" --by claude-code/<your model id>` — it copies the template, computes `generated`, `status: draft` and `stale_after` from the registry, and indexes the page; you then fill the body. On a page you update by hand, set `generated: { by: claude-code/<your model id>, at: <now, ISO-8601 with offset> }` and re-run `uv run tos-index <path>` so the index entry matches. **Never write `verified`.**
6. Append the operation's log line with `uv run tos-log Ingest "[Title](sources/<file>) — touched N pages (M new)."`
7. Move the input file from `raw/inbox/` to `raw/notes/` (same name; add the date prefix if it has none). Never edit its contents.
8. Commit `data.root` with the log line as the message.

If the input contains material about a person (health, personal circumstances, compensation, ratings, characterisations), summarise the work content only and say that you left the rest out (CLAUDE.md §5).

Finish with the list of pages created or updated, and open questions raised.
