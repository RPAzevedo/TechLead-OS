---
description: Answer a question from the wiki, citing pages with their trust tier and age
argument-hint: <question>
---
Follow CLAUDE.md §0, then §4.4. Question: $ARGUMENTS

1. Read `wiki/index.md`. Choose the directories that could hold the answer; read their `index.md`. Read the frontmatter of candidate pages; read bodies only for the pages you will use. Do not walk the whole bundle.
2. Answer in prose. After the answer, list every page you relied on as `- [path](path) — <tier>, <date>` where tier is one of: human-reviewed (newest `verified[].at`), machine-confirmed, unverified (`generated.at`), changed since verification, and add `stale since <stale_after>` when today ≥ `stale_after`. Exclude `status: deprecated` pages unless the question asks about history.
3. If the answer is reusable (a comparison, a dependency list, a position), write it as `wiki/syntheses/<slug>.md` from `schema/templates/synthesis.md` with `status: draft`, footnoted to the pages' sources, add it to `syntheses/index.md`, log `* **Query**: "<question>" → [Synthesis](syntheses/<file>)`, and commit. Otherwise log nothing.
4. If the wiki cannot answer, say so plainly and offer to create a `Question` page (do so only if the human agrees).
