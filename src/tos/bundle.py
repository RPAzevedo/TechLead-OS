"""Write-side helpers for the OKF bundle — the canonical formats, produced once.

`common.py` stays read-only; everything that appends a log bullet, an index
entry or edits a page's frontmatter goes through here so the formats cannot
drift per operation. Frontmatter is always edited at the text level, never
round-tripped through the YAML parser: `yaml.dump` would destroy comments
(the templates' `# verified: never set by /tos-ingest` breadcrumb), key order
and the flow-style `generated: { by, at }`.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from tos import common as pc

LOG_LABELS = {"Creation", "Pull", "Ingest", "Query", "Brief", "Measure",
              "Lint", "Verify", "Review", "Deprecate", "Migration"}

HEADING_RE = re.compile(r"^## +(.*?)[ \t]*$")
# a directory index entry: the *first* link on a bullet line is the page it lists, and only
# that one. A link inside another entry's description names a page, it does not list it.
ENTRY_TARGET_RE = re.compile(r"^[ \t]*[*-] .*?\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

WIKI_DIRS = {
    # path: (title, description)
    "": ("TechLead OS", "the OKF bundle root — start here"),
    "delivery": ("Delivery", "initiatives, projects, objectives, delivery metrics"),
    "delivery/initiatives": ("Initiatives", "cross-functional efforts and company moving parts"),
    "delivery/projects": ("Projects", "what the team delivers"),
    "delivery/objectives": ("Objectives", "the quarter's OKRs — company and team"),
    "delivery/metrics": ("Delivery metrics", "attested computations over Jira snapshots (phase 2)"),
    "team": ("Team", "the team, its people, stakeholders and playbooks (phase 3)"),
    "team/people": ("People", "reports — human-reviewed before any use (phase 3)"),
    "team/stakeholders": ("Stakeholders", "partners outside the team (phase 3)"),
    "team/playbooks": ("Playbooks", "how we do X; shareable (phase 3)"),
    "systems": ("Systems", "systems owned or supported, their standards and KTLO"),
    "systems/metrics": ("System metrics", "attested computations over system data (phase 2)"),
    "design": ("Design", "RFCs, decisions, visions"),
    "design/rfcs": ("RFCs", "proposals under review — entry points to the canonical documents"),
    "design/decisions": ("Decisions", "ADR-style records"),
    "design/visions": ("Visions", "technical visions per area of influence (phase 4)"),
    "learning": ("Learning", "paths and drills (phase 4)"),
    "learning/paths": ("Learning paths", "goals with exit criteria (phase 4)"),
    "learning/drills": ("Drills", "retrieval practice (phase 4)"),
    "concepts": ("Concepts", "ideas, techniques, standards, terms"),
    "sources": ("Sources", "one page per source read: summary, excerpts, provenance"),
    "syntheses": ("Syntheses", "overviews, comparisons, theses, briefs"),
    "radar": ("Radar", "external signals feeding visions and initiatives (phase 4)"),
    "radar/signals": ("Signals", "external observations with a 30-day horizon (phase 4)"),
    "questions": ("Questions", "the ambiguity register"),
    "reviews": ("Reviews", "weekly and sprint reviews with inline answers"),
}


def md_label(text: str) -> str:
    """A title as a markdown link label: `[`, `]` and `\\` escaped.

    An unescaped `]` closes the label early, so `[bracketed]` would produce
    `* [[bracketed]](page.md)` — a line no link parser reads, leaving lint
    convinced the page is unindexed and `--fix` unable to repair it.
    """
    return re.sub(r"([\\\[\]])", r"\\\1", text)


def yaml_scalar(value: str) -> str:
    """A string as a YAML scalar: plain only when it parses back as the same string.

    Round-tripping is the test rather than a character blocklist, because YAML's
    implicit typing is what bites: a title of `true`, `null` or `2026-09-01` read
    back as a bool, None or a date, and the page's frontmatter would then carry a
    different type from what was asked for. Anything else is JSON-quoted, which
    is valid YAML.
    """
    if value and value == value.strip():
        try:
            if pc.load_yaml(value) == value:
                return value
        except pc.YamlError:
            pass
    return json.dumps(value, ensure_ascii=False)


# ----------------------------------------------------------------------------- index.md
def index_body(rel: str, title: str, desc: str) -> str:
    """The canonical index.md for the bundle-relative directory `rel`."""
    lines = []
    if rel == "":
        lines.append('---\nokf_version: "0.2"\n---')
    lines += [f"# {title}", "", desc, ""]
    children = sorted(k for k in WIKI_DIRS if k != rel and str(Path(k).parent) == (rel or "."))
    if children:
        lines += ["## Directories", ""]
        for c in children:
            t, d = WIKI_DIRS[c]
            lines.append(f"* [{t}]({Path(c).name}/) - {d}")
        lines.append("")
    lines += ["## Pages", ""]
    return "\n".join(lines) + "\n"


def ensure_index(wiki: Path, directory: Path, dry: bool) -> bool:
    """Write the directory's canonical index.md when it has none. True when it created one.

    A skeletal file would be worse than none: /tos-init only creates an index that is
    missing, so a stub beginning at `## Pages` would keep its heading and description
    for good. A directory the engine does not name gets a title from its own name.
    """
    index_path = directory / "index.md"
    if index_path.exists():
        return False
    rel = str(directory.resolve().relative_to(wiki.resolve())).replace("\\", "/")
    rel = "" if rel == "." else rel
    title, desc = WIKI_DIRS.get(rel, (Path(rel).name.replace("-", " ").capitalize() or "TechLead OS", ""))
    if not dry:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(index_body(rel, title, desc), encoding="utf8")
    return True


def entry_target(line: str) -> str | None:
    """The file a directory index line lists, or None when the line is not an entry."""
    m = ENTRY_TARGET_RE.match(line)
    return m.group(1) if m else None


def add_index_entry(index_path: Path, title: str, filename: str, desc: str, dry: bool,
                    *, refresh: bool = False, heading: str = "Pages") -> str | None:
    """Add `* [title](filename) - desc` under `## <heading>`, creating the section at the end.

    An existing entry for the same file is left alone unless `refresh` is set, which
    rewrites it where it stands — `delivery/projects/index.md` is ordered by priority,
    and re-indexing a project after an ingest must not move it to the tail. Only a
    changed `heading` moves the line (how a page's entry travels to `## Deprecated`).
    Returns "added" | "refreshed" | None (no-op).
    """
    if not index_path.exists() and not dry:
        # a caller that skipped ensure_index would otherwise get a stub with no H1, and
        # /tos-init only ever creates an index that is *missing* — the stub would be permanent
        raise FileNotFoundError(f"{index_path} is missing — run /tos-init, or call ensure_index first")
    text = index_path.read_text(encoding="utf8") if index_path.exists() else ""
    line = f"* [{md_label(title)}]({filename}) - {desc}"
    lines = text.rstrip("\n").split("\n") if text.strip() else []
    existing = [i for i, ln in enumerate(lines) if entry_target(ln) == filename]
    if existing and not refresh:
        return None

    def write(new_lines):
        if not dry:
            index_path.write_text("\n".join(new_lines) + "\n", encoding="utf8")

    def heading_above(i, headings):
        prior = [j for j in headings if j < i]
        return headings[max(prior)] if prior else None

    headings = {i: m.group(1) for i, ln in enumerate(lines) if (m := HEADING_RE.match(ln))}
    if existing and heading_above(existing[0], headings) == heading:
        lines[existing[0]] = line
        for i in reversed(existing[1:]):  # a duplicate entry for the same page is not two pages
            del lines[i]
        write(lines)
        return "refreshed"

    action = "refreshed" if existing else "added"
    for i in reversed(existing):
        del lines[i]
    # find the target section; create it at the end when absent
    headings = {i: m.group(1) for i, ln in enumerate(lines) if (m := HEADING_RE.match(ln))}
    try:
        start = next(i for i, h in headings.items() if h == heading)
    except StopIteration:
        lines += ["", f"## {heading}"]
        start = len(lines) - 1
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    insert_at = end
    if insert_at == start + 1:
        lines.insert(insert_at, "")
        insert_at += 1
    lines.insert(insert_at, line)
    write(lines)
    return action


# ----------------------------------------------------------------------------- log.md
def log_add(log_path: Path, label: str, text: str, date: dt.date, dry: bool = False) -> str:
    """Append `* **label**: text` under `## date` in wiki/log.md, newest first.

    Creates the day's heading in date order (never out of order); appends at the
    end of an existing day's group. Returns the bullet written. Raises ValueError
    on an unknown label, FileNotFoundError when the log is missing.
    """
    if label not in LOG_LABELS:
        raise ValueError(f"label `{label}` is not one of {sorted(LOG_LABELS)}")
    if not log_path.exists():
        raise FileNotFoundError(f"{log_path} is missing — run tos-init first")
    bullet = f"* **{label}**: {text}"
    lines = log_path.read_text(encoding="utf8").rstrip("\n").split("\n")
    headings = [(i, pc.parse_date(ln[3:].strip())) for i, ln in enumerate(lines) if ln.startswith("## ")]
    ours = next((i for i, d in headings if d == date), None)
    if ours is not None:
        end = next((i for i, _ in headings if i > ours), len(lines))
        while end > ours + 1 and not lines[end - 1].strip():
            end -= 1
        lines.insert(end, bullet)
    else:
        at = next((i for i, d in headings if d and d < date), len(lines))
        block = [f"## {date.isoformat()}", bullet, ""]
        if at and lines[at - 1].strip():
            block.insert(0, "")
        lines[at:at] = block
        while lines and not lines[-1].strip():
            lines.pop()
    if not dry:
        log_path.write_text("\n".join(lines) + "\n", encoding="utf8")
    return bullet


# ----------------------------------------------------------------------------- frontmatter
def _fm_span(text: str) -> tuple[int, int]:
    """(start, end) line indexes of the frontmatter block's content in text.split("\\n")."""
    fm, _, err = pc.split_frontmatter(text)
    if err:
        raise ValueError(f"frontmatter is not valid YAML: {err}")
    if fm is None:
        raise ValueError("the page has no frontmatter block")
    lines = text.split("\n")
    close = next(i for i in range(1, len(lines)) if lines[i].rstrip() == "---")
    return 1, close


def edit_frontmatter_lines(text: str, replacements: dict[str, str]) -> str:
    """Replace whole top-level `key:` lines in the frontmatter block, textually.

    `replacements` maps a key to its new full line (no newline). Raises KeyError
    for a key the block does not carry — the templates carry every key we fill.
    """
    start, end = _fm_span(text)
    lines = text.split("\n")
    pending = dict(replacements)
    for i in range(start, end):
        key = lines[i].split(":", 1)[0]
        if not lines[i].startswith((" ", "\t", "#")) and ":" in lines[i] and key in pending:
            lines[i] = pending.pop(key)
    if pending:
        raise KeyError(f"frontmatter has no top-level key(s): {sorted(pending)}")
    return "\n".join(lines)


VERIFIED_ITEM_RE = re.compile(r"^([ \t]*)- ")


def append_verified_entry(text: str, by: str, at: str) -> str:
    """Append `- { by, at }` to the page's `verified`, whatever shape the key is in.

    OKF allows a list of mappings or a single mapping — `common.verified_entries()` reads
    both and docs/design.md shows both — and tos-verify-mark is now the only way an entry is
    ever written, so a conforming page it could not extend would need exactly the hand edit
    CLAUDE.md §0 forbids. A single mapping, flow or block, becomes a one-item list with its
    text carried over verbatim, so key order, extra keys and comments survive. Raises
    ValueError for a shape that cannot be extended without re-emitting it.
    """
    entry = f"{{ by: {by}, at: {at} }}"
    start, end = _fm_span(text)
    lines = text.split("\n")
    v = next((i for i in range(start, end) if lines[i].startswith("verified:")), None)
    if v is None:
        return insert_frontmatter_lines(text, "status", ["verified:", f"  - {entry}"])

    inline = lines[v][len("verified:"):].strip()
    if inline and not inline.startswith("#"):  # `verified:   # a comment` is an empty key
        try:
            value = pc.load_yaml(inline)
        except pc.YamlError as e:
            raise ValueError(f"has a `verified:` value that is not valid YAML ({e})") from e
        if not isinstance(value, dict):
            raise ValueError("has an inline `verified:` value that is not a single mapping — "
                             "write it as a list of `- { by, at }` entries first")
        lines[v] = "verified:"
        lines[v + 1:v + 1] = [f"  - {inline}", f"  - {entry}"]
        return "\n".join(lines)

    # the key's block: the indented lines under it, blank lines included
    body_lines, i = [], v + 1
    while i < end:
        # an item may sit at column 0 (`- { … }` under `verified:` is valid YAML), so a
        # missing indent alone does not mean the next top-level key has started
        if lines[i].strip() and not lines[i].startswith((" ", "\t")) and not VERIFIED_ITEM_RE.match(lines[i]):
            break
        if lines[i].strip():
            body_lines.append(i)
        i += 1
    if not body_lines:
        lines.insert(v + 1, f"  - {entry}")
        return "\n".join(lines)
    last = body_lines[-1]
    items = [j for j in body_lines if VERIFIED_ITEM_RE.match(lines[j])]
    if items:  # already a list: match the indent the page uses, which need not be two spaces
        indent = VERIFIED_ITEM_RE.match(lines[items[-1]]).group(1)
        lines.insert(last + 1, f"{indent}- {entry}")
        return "\n".join(lines)
    # a block mapping: re-indent it into the list's first item, verbatim
    first = body_lines[0]
    base = len(lines[first]) - len(lines[first].lstrip())
    for j in range(first, last + 1):
        if lines[j].strip():
            lines[j] = ("  - " if j == first else "    ") + lines[j][base:]
    lines.insert(last + 1, f"  - {entry}")
    return "\n".join(lines)


def insert_frontmatter_lines(text: str, before_key: str, new_lines: list[str]) -> str:
    """Insert lines immediately before the top-level `before_key:` line."""
    start, end = _fm_span(text)
    lines = text.split("\n")
    for i in range(start, end):
        if lines[i].startswith(f"{before_key}:"):
            lines[i:i] = new_lines
            return "\n".join(lines)
    raise KeyError(f"frontmatter has no top-level key: {before_key}")
