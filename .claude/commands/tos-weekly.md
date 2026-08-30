---
description: The Monday tick — lint, queues, expiries, RFCs, systems, questions; --apply executes the human's inline answers
argument-hint: [--apply]
---
Follow CLAUDE.md §0, then §4.7. Mode: $ARGUMENTS

Without `--apply`:
1. Run the `/tos-lint` procedure (script + agent pass), keeping its findings for step 3.
2. Gather from `wiki/`: pages ingested in the last 7 days (from `log.md`); the verify queue (top `review.verify_queue` unverified or changed-since-verified pages, ranked as in `/tos-verify --queue`); the re-pull queue (source drift); pages stale or expiring within `review.expiring_days`; `next_checkpoint` dates in the past; RFCs with `status: draft`; System pages expiring within 14 days or with unticked standards; open Question pages.
3. Write `wiki/reviews/<ISO-week, e.g. 2026-W36>.md` from `schema/templates/review.md` with `generated: { by: process:weekly-review, at: now }` and these H1 sections, each a checklist the human can answer inline with `→ <answer>`: Ingested this week · Verify queue · Re-pull queue · Expiring (refresh / extend / deprecate) · Checkpoints passed · Design — awaiting your decision · Systems · Questions · Lint · Engine proposals. Phase 3+ sections (Comms due, 1:1 prep) only when the phase allows.
4. Add the page to `reviews/index.md`, log `* **Review**: [Week NN](reviews/<file>) written`, commit. Tell the human it is ready and how to answer (edit the page inline, then `/tos-weekly --apply`).

With `--apply`:
1. Read this week's Review page and every `→` answer.
2. Execute each: `extend` → move `stale_after` by the type's horizon and log `Verify` only if the human also said verify, otherwise log `Ingest`; `deprecate` → `status: deprecated` with the reason, log `Deprecate`; `refresh`/`re-pull` → run `/tos-pull` on the page's pointer; a verify answer → run the `/tos-verify` procedure for that page; a question answer → update the Question page's *Resolution*; a checkpoint answer → update `next_checkpoint`.
3. Engine proposals the human accepted: apply them in this engine repository, add a line to `CHANGELOG.md`, commit the engine — and write nothing about it in `wiki/log.md`. If an accepted proposal changes existing data pages, log that change as `* **Migration**: … (engine <version>)`.
4. Mark the Review page `status: stable`, log `* **Review**: [Week NN](reviews/<file>) applied — N actions`, commit.
