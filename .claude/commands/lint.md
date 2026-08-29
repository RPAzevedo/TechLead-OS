---
description: Health-check the bundle — deterministic script, then the agent pass
argument-hint: [--fix]
---
Follow CLAUDE.md §0, then §4.5.

1. Run `python3 scripts/okf_lint.py` and read the report.
2. Agent pass, on the pages the report mentions plus any page changed in the last 7 days (use `git log` in `data.root`): contradictions between pages; claims without a footnote; missing cross-references between pages that mention each other's subjects; gaps worth a `Question` page; the people policy (CLAUDE.md §5) on any page that mentions a person; and **source drift**: for each Source page whose `sources[].resource` is a URL inside a connector's scope and whose connector is enabled for the current phase, fetch the source's current modified time or version through the connector (read-only) and list those newer than the recorded `last_modified` as "changed since read".
3. Write the combined findings as the *Lint* section of the current week's Review page (`wiki/reviews/<ISO-week>.md`; create it from `schema/templates/review.md` if it does not exist). Do not fix anything judgement-shaped.
4. Only if `--fix` was given: repair mechanical findings — missing index entries, broken relative links whose target obviously moved, malformed log bullets — and log `* **Lint**: fixed N mechanical findings; M open.` Commit. Lint never adds `verified` entries.

Finish with counts per check and the three findings you would act on first.
