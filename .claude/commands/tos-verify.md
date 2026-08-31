---
description: Promote a page the human has read — the only way a human:* verification is ever written
argument-hint: <page path> | --queue
---
Follow CLAUDE.md §0, then §4.6. Target: $ARGUMENTS

If `--queue`: list the top `review.verify_queue` unverified or changed-since-verified pages, ranked by inbound links, recency and domain weight (team > design > systems > delivery > learning), and take them one at a time. Leave out active Projects (`status` not `deprecated`, `stage` not `paused` or `done`) — they are verified from their rows in the weekly portfolio, where the week's entry is shown with them.

For each page:
1. Show the page's title, type, tier, and the diff since its newest `verified[].at` (or the whole page if never verified): `git -C <data.root> log -p -- <path>` narrowed to that window.
2. Ask the human: verify, fix, or skip. **Wait for the answer. Never assume it.**
3. On "verify": append `{ by: <data.actor>, at: <now, ISO-8601 with offset> }` to `verified` (create the list if absent); if the type's gate in `schema/types.md` is met, set `status: stable`; log `* **Verify**: [Title](path) by <data.actor>`; commit.
4. On "fix": make the change they describe, update `generated`, leave `status: draft`, log `* **Ingest**: [Title](path) — revised after review`, commit, and offer to verify again.
5. On "skip": do nothing.

Never write a `human:` verification outside this command. Never verify on your own initiative.
