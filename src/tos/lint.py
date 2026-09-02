"""/tos-lint, deterministic half — OKF v0.2 conformance and TechLead OS trust checks.

    uv run tos-lint [--json] [--fix] [--today YYYY-MM-DD]

No LLM, no network. Reads the config for data.root and the review settings,
walks wiki/, and prints a markdown report (or JSON). Exit code 1 when a
conformance error is found, 0 otherwise. `--fix` first repairs the mechanical
findings — missing index entries, dead index lines, moved and leading-slash
links — then reports on the repaired tree. The agent pass (contradictions,
unsupported claims, missing cross-references, the people policy, source drift)
is described in CLAUDE.md §4.5 and is not this script's job.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from tos import common as pc
from tos.bundle import LOG_LABELS, add_index_entry

RESERVED = {"index.md", "log.md"}
STATUSES = {"draft", "stable", "deprecated"}
ROLES = {"lead", "support"}
STAGES = {"discovery", "build", "pilot", "rollout", "paused", "done"}
LEVELS = {"company", "team"}
SLACK_RE = re.compile(r"^#[a-z0-9][a-z0-9_-]{0,79}$")
JIRA_RE = re.compile(r"^[A-Z][A-Z0-9_]*-[1-9]\d*$")
HTTPS_RE = re.compile(r"^https://\S+$")  # https only: the contract says https, and `http://` is a paste error
# the pointer fields of a Project or Initiative, and the shape each finding names back
POINTER_SHAPES = {
    "slack": 'a quoted channel name, "#team-search"',
    "jira": "an issue key, ABC-123",
    "confluence": "an https URL",
    "rfc": "an https URL, or a relative path to a page in this bundle",
}
WEEKLY_LABELS = {"Progress", "Challenges & risks", "Blockers & support needed",
                 "Open questions & decisions", "Notes"}
# the label may carry escaped brackets — a title of `[bracketed]` is written `[\[bracketed\]]`
LINK_RE = re.compile(r"(?<!!)\[((?:[^\]\\]|\\.)*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FOOTNOTE_DEF_RE = re.compile(r"^\[\^([^\]]+)\]:", re.M)
QUARTER_RE = re.compile(r"^\d{4}-Q[1-4]$")
TEAM_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
TOP_BULLET_RE = re.compile(r"^[-*] +(.*)$", re.M)          # nested bullets under a label are indented
WEEKLY_LABEL_RE = re.compile(r"\*\*([^*]+)\*\*:[ \t]*\S")
FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
# a fenced block (to the closing fence, or the end of the page when it is never closed) or an
# inline code span. What is inside one is an example, not a link this bundle has to resolve.
CODE_RE = re.compile(r"(?ms)^[ \t]{0,3}(`{3,}|~{3,})[^\n]*\n.*?(?:^[ \t]{0,3}\1[ \t]*$|\Z)|`[^`\n]+`")


load_registry = pc.load_registry  # moved to common.py in 0.8.0; the helpers need it too


class Report:
    def __init__(self):
        self.findings = defaultdict(list)  # check -> list[str]
        self.errors = 0

    def add(self, check: str, msg: str, error: bool = False):
        self.findings[check].append(msg)
        if error:
            self.errors += 1


def rel(p: Path, root: Path) -> str:
    return str(p.relative_to(root)).replace("\\", "/")


def weekly_entries(section: str) -> list:
    """The `## <heading>` entries of a Weekly log, as (heading, body) pairs."""
    heads = list(re.finditer(r"^## +(.+?)[ \t]*$", section, re.M))
    return [(h.group(1), section[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(section)])
            for i, h in enumerate(heads)]


def check_pointers(fm: dict, path: str, page_dir: Path, wiki: Path, rep) -> None:
    """The optional pointers a Project or Initiative carries out to the systems that host it.

    Shape only, and only when present: `slack`, `jira`, `confluence` and `rfc` are notes to the
    human and to a later /tos-pull, never a requirement, so nothing here is a conformance error.
    Recording where work lives is not reading it — no rollout phase and no connector scope enter
    into it; those belong to /tos-pull alone.

    A relative `rfc` is resolved like a body link but is deliberately not one: it adds no inbound
    link, because the orphan check exists to make you link the page from a section (`superseded_by`
    is the same shape), and --fix does not repair it after the RFC page moves.
    """
    for key, want in POINTER_SHAPES.items():
        if key not in fm:
            continue
        v = fm[key]
        if v is None or (isinstance(v, str) and not v.strip()):
            # `slack: #team-search` is not a string: an unquoted # opens a YAML comment, and the
            # human is left believing they set a field that parsed to nothing
            extra = " — an unquoted `#channel` is a YAML comment, so the value is empty" if key == "slack" else ""
            rep.add("pointers", f"`{path}` has an empty `{key}` — expected {want}{extra}")
        elif not isinstance(v, str):
            rep.add("pointers", f"`{path}` has a non-string `{key}` ({v!r}) — one pointer, as {want}; "
                                f"more than one goes in the body")
        elif key == "slack" and not SLACK_RE.match(v):
            rep.add("pointers", f"`{path}` has `slack: {v!r}` — expected {want}")
        elif key == "jira" and not JIRA_RE.match(v):
            rep.add("pointers", f"`{path}` has `jira: {v!r}` — expected {want}")
        elif key == "confluence" and not HTTPS_RE.match(v):
            rep.add("pointers", f"`{path}` has `confluence: {v!r}` — expected {want}")
        elif key == "rfc" and not HTTPS_RE.match(v):
            if v.startswith("/"):
                rep.add("pointers", f"`{path}` has `rfc: {v!r}` — leading slash; use a relative path")
                continue
            target = (page_dir / v.split("#")[0]).resolve()
            try:
                rel(target, wiki.resolve())
            except ValueError:
                rep.add("pointers", f"`{path}` has `rfc: {v!r}` — it resolves outside the bundle")
                continue
            # a directory or a non-markdown file `exists()` too, and neither is a page to open
            if not (target.is_file() and target.suffix == ".md"):
                rep.add("pointers", f"`{path}` has `rfc: {v!r}` — no such page in this bundle")


def section_links(body: str, heading: str, page_dir: Path, wiki: Path) -> set:
    """Bundle-relative targets of the links inside one H1 section.

    The alignment between a Project and its objective, and between a team and a company
    objective, is a link in a named section (schema/types.md) — a mention anywhere else on
    the page does not stand in for it.
    """
    m = re.search(rf"^# {re.escape(heading)}\s*\n(.*?)(?=^# |^\[\^|\Z)", body, re.S | re.M)
    if not m:
        return set()
    found = set()
    for _text, target in prose_links(m.group(1)):
        if target.startswith(("http://", "https://", "mailto:", "#", "/")):
            continue
        try:
            found.add(rel((page_dir / target.split("#")[0]).resolve(), wiki.resolve()))
        except ValueError:
            continue
    return found


def prose_links(text: str) -> list:
    """The `(label, target)` pairs of `text`, code spans and fenced blocks excluded.

    A link inside a fenced example is not a link of this bundle: it must not count as an
    inbound link, be reported broken, list a page in an index, or be repaired by --fix.
    """
    found, pos = [], 0
    for m in CODE_RE.finditer(text):
        found += LINK_RE.findall(text[pos:m.start()])
        pos = m.end()
    return found + LINK_RE.findall(text[pos:])


def sub_outside_code(repl, text: str) -> str:
    """`LINK_RE.sub(repl, text)` applied only outside code spans and fenced blocks."""
    out, pos = [], 0
    for m in CODE_RE.finditer(text):
        out += [LINK_RE.sub(repl, text[pos:m.start()]), m.group(0)]
        pos = m.end()
    out.append(LINK_RE.sub(repl, text[pos:]))
    return "".join(out)


def _splice_target(m, new_target: str) -> str:
    """The link match with its target replaced, label and optional title kept."""
    s, e = m.start(2) - m.start(0), m.end(2) - m.start(0)
    return m.group(0)[:s] + new_target + m.group(0)[e:]


def run_fixes(wiki: Path) -> list[str]:
    """The mechanical repairs behind --fix; returns one line per repair.

    Only what needs no judgement: a page missing from its (existing) index, a
    dead index line, a broken link whose target's basename exists exactly once
    elsewhere in the bundle, a leading-slash link that resolves inside wiki/.
    Everything else stays a report finding. Idempotent: a second run fixes zero.
    """
    fixed = []
    by_name = defaultdict(list)
    for p in sorted(wiki.rglob("*.md")):
        if p.name not in RESERVED:
            by_name[p.name].append(p)

    def retarget(target: str, page_dir: Path):
        """A repaired bundle-relative target for a broken one, or None."""
        clean, _, frag = target.partition("#")
        if target.startswith("/"):
            # `/../outside.md` resolves out of the bundle; repairing it would write a
            # relative link to a file that is not a page of this bundle at all
            cand = pc.bundle_path(wiki, clean.lstrip("/"))
            if cand is None or not cand.exists():
                return None
        elif (page_dir / clean).resolve().exists():
            return None
        else:
            cands = by_name.get(Path(clean).name, [])
            if len(cands) != 1:
                return None
            cand = cands[0]
        return os.path.relpath(cand, page_dir).replace("\\", "/") + (f"#{frag}" if frag else "")

    # pages missing from their directory's existing index.md
    for d in sorted({p.parent for p in wiki.rglob("*.md")}):
        idx = d / "index.md"
        if not idx.exists():
            continue  # a whole missing index needs a title and a description — report, don't guess
        _, body, err = pc.split_frontmatter(idx.read_text(encoding="utf8"))
        if err:
            continue  # a broken index is a conformance error, not a mechanical fix
        listed = {t for _, t in prose_links(body)}
        for p in sorted(d.glob("*.md")):
            if p.name in RESERVED or p.name in listed:
                continue
            fm, _, _, _ = pc.read_page(p)
            heading = "Deprecated" if (fm or {}).get("status") == "deprecated" else "Pages"
            # refresh, so a line this parser could not read (a title with an unescaped `]`,
            # written before 0.8.0) is replaced rather than left beside a second entry —
            # and report only what actually changed, or --fix would claim it every run
            action = add_index_entry(idx, str((fm or {}).get("title") or p.stem), p.name,
                                     str((fm or {}).get("description") or ""), False,
                                     refresh=True, heading=heading)
            if action:
                fixed.append(f"`{rel(p, wiki)}` {action} in `{rel(idx, wiki)}`")

    # dead or moved links — index lines are repaired or removed, body links only repaired
    for p in sorted(wiki.rglob("*.md")):
        if p.name == "log.md":
            continue
        text = p.read_text(encoding="utf8")
        prel = rel(p, wiki)
        # the body only: a markdown-shaped frontmatter value is metadata, not a link, and
        # rewriting it would edit the page's provenance to repair a link that is not there
        _, body, _ = pc.split_frontmatter(text)
        head = text[:len(text) - len(body)]
        if p.name == "index.md":
            out, fence = [], None
            for ln in body.split("\n"):
                f = FENCE_RE.match(ln)
                if f and (fence is None or ln.strip().startswith(fence)):
                    fence = None if fence else f.group(1)
                    out.append(ln)
                    continue
                m = None if fence else LINK_RE.search(ln)
                target = m.group(2) if m else ""
                if (not m or not ln.lstrip().startswith(("*", "-"))
                        or target.startswith(("http://", "https://", "mailto:", "#"))
                        or (p.parent / target.partition("#")[0]).resolve().exists()):
                    out.append(ln)
                    continue
                new = retarget(target, p.parent)
                if new:
                    out.append(ln[:m.start()] + _splice_target(m, new) + ln[m.end():])
                    fixed.append(f"`{prel}` link `{target}` → `{new}`")
                else:
                    fixed.append(f"`{prel}` dead line for `{target}` removed")
            new_body = "\n".join(out)
        else:
            def repl(m, page_dir=p.parent, prel=prel):
                target = m.group(2)
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    return m.group(0)
                new = retarget(target, page_dir)
                if new is None:
                    return m.group(0)
                fixed.append(f"`{prel}` link `{target}` → `{new}`")
                return _splice_target(m, new)
            new_body = sub_outside_code(repl, body)
        if new_body != body:
            p.write_text(head + new_body, encoding="utf8")
    return fixed


def main(argv):
    as_json = "--json" in argv
    cfg = pc.load_config()
    today = pc.today(cfg)
    if "--today" in argv:
        today = pc.parse_date(argv[argv.index("--today") + 1]) or today
    root = pc.data_root(cfg)
    wiki = root / "wiki"
    if not wiki.exists():
        sys.exit(f"no wiki at {wiki} — run /tos-init first")
    expiring_days = int(pc.review_setting(cfg, "expiring_days", 7))
    draft_age = int(pc.review_setting(cfg, "draft_age_days", 14))
    weekly_grace = int(pc.review_setting(cfg, "weekly_log_grace_days", 16))
    registry = load_registry()
    rep = Report()
    if "--fix" in argv:
        for msg in run_fixes(wiki):  # repairs land before the walk, so the report sees the fixed tree
            rep.add("fixed", msg)

    pages = {}  # rel path -> (fm, body)
    yaml_errors = {}  # rel path -> parser message
    for p in sorted(wiki.rglob("*.md")):
        if p.name in RESERVED:
            continue
        fm, body, _, err = pc.read_page(p)
        pages[rel(p, wiki)] = (fm, body)
        if err:
            yaml_errors[rel(p, wiki)] = err

    inbound = defaultdict(set)
    counts = defaultdict(int)
    priority_paths = defaultdict(list)  # priority -> active project paths carrying it
    lead_projects = []  # active lead projects past the grace window; checked against objectives post-loop
    alignment = {}  # page -> targets linked from its alignment section (Expected impact / Objective)

    # ---- per-page checks
    for path, (fm, body) in pages.items():
        if path in yaml_errors:
            rep.add("conformance", f"`{path}` frontmatter is not valid YAML: {yaml_errors[path]}", error=True)
            continue
        if fm is None:
            rep.add("conformance", f"`{path}` has no YAML frontmatter", error=True)
            continue
        t = fm.get("type")
        if not t or not str(t).strip():
            rep.add("conformance", f"`{path}` has no `type`", error=True)
            continue
        counts[str(t)] += 1
        page_dir = (wiki / path).parent
        if str(t) not in registry:
            rep.add("registry", f"`{path}` has type `{t}` which is not in schema/types.md")
        else:
            want = registry[str(t)]["dir"]
            if want and not any(path.startswith(w) for w in want) and str(t) != "Team":
                where = " or ".join(f"`{w}`" for w in want)
                rep.add("registry", f"`{path}` is a `{t}` but lives outside {where}")
            req = registry[str(t)]["headings"]
            if req and fm.get("status") != "deprecated":
                found = [m.group(1) for m in re.finditer(r"^# (.+?)[ \t]*$", body, re.M)]
                missing = [h for h in req if h not in found]
                if missing:
                    rep.add("headings", f"`{path}` — a `{t}` missing required heading(s): "
                                        + " · ".join(f"`# {h}`" for h in missing))
                elif [found.index(h) for h in req] != sorted(found.index(h) for h in req):
                    rep.add("headings", f"`{path}` — required headings out of template order "
                                        f"({' · '.join(req)})")
        gen = fm.get("generated") if isinstance(fm.get("generated"), dict) else None
        gen_at = pc.parse_datetime(gen.get("at")) if gen else None
        if not gen or not gen.get("by") or not gen_at:
            rep.add("trust", f"`{path}` lacks a well-formed `generated: {{ by, at }}`")
        status = fm.get("status")
        if status not in STATUSES:
            rep.add("trust", f"`{path}` has `status: {status!r}` — must be explicit: draft | stable | deprecated")
        if "stale_after" not in fm:
            rep.add("trust", f"`{path}` lacks `stale_after` (use `~` for a record)")
        stale = pc.parse_date(fm.get("stale_after"))
        if fm.get("stale_after") is not None and stale is None:
            rep.add("trust", f"`{path}` has an unparseable `stale_after`: {fm.get('stale_after')!r}")
        stage = str(fm.get("stage") or "")
        # an active Project answers for its freshness and its trust in the weekly portfolio row,
        # so it stays out of the stale, expiring, checkpoint and verify queues (CLAUDE.md §4.7)
        active_project = str(t) == "Project" and status != "deprecated" and stage not in ("paused", "done")
        if stale and status != "deprecated" and not active_project:
            if today >= stale:
                rep.add("stale", f"`{path}` — stale since {stale.isoformat()}")
            elif (stale - today).days <= expiring_days:
                rep.add("expiring", f"`{path}` — expires {stale.isoformat()}")
        tier = pc.trust_tier(fm)
        if tier == "changed-since-verified" and not active_project:
            # an active Project re-verifies from its weekly portfolio row, not from the queues
            rep.add("changed-since-verified", f"`{path}` — generated.at is later than the newest verified.at")
        for e in pc.verified_entries(fm):
            by = str(e.get("by", ""))
            if not (by.startswith("human:") or by.startswith("process:") or "/" in by):
                rep.add("trust", f"`{path}` has a verified entry with a malformed actor `{by}`")
        if status == "draft" and gen_at and (today - gen_at.date()).days > draft_age:
            rep.add("old-drafts", f"`{path}` — draft for {(today - gen_at.date()).days} days")
            if str(t) == "RFC":
                rep.add("rfcs-stuck", f"`{path}` — RFC in draft for {(today - gen_at.date()).days} days")
        if str(t) == "System":
            sec = re.search(r"^# Operational standards\s*\n(.*?)(?=^# |\Z)", body, re.S | re.M)
            if sec:
                unticked = len(re.findall(r"^\s*- \[ \]", sec.group(1), re.M))
                if unticked:
                    rep.add("systems", f"`{path}` — {unticked} operational standard(s) unticked")
        if str(t) == "Project":
            role = fm.get("role")
            prio = fm.get("priority")
            wl = re.search(r"^# Weekly log\s*\n(.*?)(?=^# |^\[\^|\Z)", body, re.S | re.M)
            entries = weekly_entries(wl.group(1)) if wl else []
            # role, priority and the first weekly entry are all seeded by a Monday tick, so they are
            # only expected once one has happened: an entry exists, or the page predates the window.
            # generated.at alone will not do — --apply resets it every week the project moves.
            seen_a_monday = bool(entries) or (gen_at is not None and (today - gen_at.date()).days > weekly_grace)
            if role is not None and str(role) not in ROLES:
                rep.add("projects", f"`{path}` has `role: {role!r}` — must be lead | support")
            if not stage:
                # stage is what makes a project active, and active projects leave the other queues
                rep.add("projects", f"`{path}` has no `stage` — one of {sorted(STAGES)}")
            elif stage not in STAGES:
                rep.add("projects", f"`{path}` has `stage: {stage!r}` — must be one of {sorted(STAGES)}")
            if prio is not None:
                if isinstance(prio, bool) or not isinstance(prio, int) or prio < 1:
                    rep.add("projects", f"`{path}` has `priority: {prio!r}` — must be a positive integer")
                elif not active_project:
                    rep.add("projects", f"`{path}` is not active but still carries `priority: {prio}`")
                else:
                    priority_paths[prio].append(path)
            # the log's shape is checked whatever the stage: pausing a project does not make its
            # history well-formed, and the entries stay on the page
            newest = None
            prev = None
            seen_weeks = set()
            for heading, entry_body in entries:
                labels = []
                for bullet in TOP_BULLET_RE.findall(entry_body):
                    lm = WEEKLY_LABEL_RE.match(bullet)
                    if not lm:
                        rep.add("projects", f"`{path}` — Weekly log entry `## {heading}` has a bullet that is "
                                            f"not `- **Label**: …`: {bullet.strip()[:50]!r}")
                    elif lm.group(1) not in WEEKLY_LABELS:
                        rep.add("projects", f"`{path}` — Weekly log label `**{lm.group(1)}**` is not one of the "
                                            f"five (Progress · Challenges & risks · Blockers & support needed · "
                                            f"Open questions & decisions · Notes)")
                    else:
                        labels.append(lm.group(1))
                if not labels:
                    # a week with no movement writes no entry at all, so an entry that
                    # says nothing is a defect rather than a quiet week
                    rep.add("projects", f"`{path}` — Weekly log entry `## {heading}` has no labelled bullet")
                m = WEEK_RE.match(heading)
                monday = None
                if m:
                    try:
                        monday = dt.date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)
                    except ValueError:
                        pass
                if monday is None:
                    rep.add("projects", f"`{path}` — Weekly log entry `## {heading}` is not `## YYYY-Www`")
                    continue
                if monday > today:
                    # --apply only ever writes the current ISO week; a future one would
                    # otherwise become `newest` and mute the currency check until it arrives
                    rep.add("projects", f"`{path}` — Weekly log entry `## {heading}` is in the future")
                    continue
                if monday in seen_weeks:
                    rep.add("projects", f"`{path}` — Weekly log has more than one `## {heading}` entry")
                seen_weeks.add(monday)
                if prev and monday > prev:
                    rep.add("projects", f"`{path}` — Weekly log entry `## {heading}` is out of order "
                                        f"— newest first")
                prev = monday
                newest = monday if newest is None or monday > newest else newest
            if active_project:
                if role is None and seen_a_monday:
                    rep.add("projects", f"`{path}` — an active Project with no `role` (lead | support)")
                if prio is None and seen_a_monday:
                    rep.add("projects", f"`{path}` — an active Project with no `priority` "
                                        f"(assigned by /tos-weekly --apply)")
                if str(role) == "lead" and seen_a_monday:
                    lead_projects.append(path)
                alignment[path] = section_links(body, "Expected impact", page_dir, wiki)
                if newest is not None:
                    if (today - newest).days > weekly_grace:
                        rep.add("projects", f"`{path}` — an active Project with no weekly entry since "
                                            f"{newest.isoformat()} (its Monday) — pause or deprecate it if it stopped")
                elif seen_a_monday:
                    # a missing *Weekly log* section itself is the headings check's finding
                    rep.add("projects", f"`{path}` — an active Project with no entry in its *Weekly log*")
        if str(t) in ("Project", "Initiative"):
            check_pointers(fm, path, page_dir, wiki, rep)
        if str(t) == "Objective":
            alignment[path] = section_links(body, "Objective", page_dir, wiki)
            level = fm.get("level")
            if level is None or str(level) not in LEVELS:
                rep.add("objectives", f"`{path}` has `level: {level!r}` — must be company | team")
            quarter = fm.get("quarter")
            if quarter is None or not QUARTER_RE.match(str(quarter)):
                rep.add("objectives", f"`{path}` has `quarter: {quarter!r}` — must be `YYYY-Qn`, e.g. 2026-Q3")
            team = fm.get("team")
            if str(level) == "team" and (team is None or not TEAM_RE.match(str(team))):
                # several teams' objectives sit side by side, so each has to say whose it is
                rep.add("objectives", f"`{path}` has `team: {team!r}` — a team Objective names its team as a slug")
            elif str(level) == "company" and team is not None:
                rep.add("objectives", f"`{path}` is `level: company` but carries `team: {team!r}`")
        # sources & footnotes
        srcs = fm.get("sources") or []
        ids = {str(s.get("id")) for s in srcs if isinstance(s, dict) and s.get("id")}
        for s in srcs:
            if isinstance(s, dict) and not s.get("resource"):
                rep.add("provenance", f"`{path}` — a `sources` entry has no `resource` (required by OKF)")
        for fid in FOOTNOTE_DEF_RE.findall(body):
            if ids and fid not in ids:
                rep.add("provenance", f"`{path}` — footnote `[^{fid}]` does not match any `sources[].id`")
        sourced_types = ("Concept", "Synthesis", "Decision", "RFC", "Initiative", "Objective", "System")
        if str(t) in sourced_types and not srcs and status != "deprecated":
            rep.add("provenance", f"`{path}` — a `{t}` page with no `sources`")
        # links
        for _text, target in prose_links(body):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if target.startswith("/"):
                rep.add("links", f"`{path}` → `{target}` uses a leading slash; use a relative link")
                continue
            tpath = (page_dir / target.split("#")[0]).resolve()
            try:
                trel = rel(tpath, wiki.resolve())
            except ValueError:
                trel = None
            if not tpath.exists():
                rep.add("links", f"`{path}` → `{target}` is broken")
            elif trel and trel in pages:
                inbound[trel].add(path)

    # ---- portfolio: duplicate priorities, objective linkage
    for prio, paths in sorted(priority_paths.items()):
        if len(paths) > 1:
            rep.add("projects", f"priority {prio} is carried by {len(paths)} active projects: "
                                + ", ".join(f"`{p}`" for p in paths))
    ranked = sorted(priority_paths)
    if ranked and ranked != list(range(1, len(ranked) + 1)):
        # unranked projects carry no priority at all, so they never open a gap here
        rep.add("projects", f"active priorities are not contiguous 1..N: {ranked} — "
                            f"/tos-weekly --apply renumbers them")
    live_objectives = {p for p, (fm, _) in pages.items()
                       if fm and str(fm.get("type")) == "Objective" and fm.get("status") != "deprecated"}
    company_objectives = {p for p in live_objectives if str(pages[p][0].get("level")) == "company"}
    if live_objectives:  # "preferably tied to OKRs": a nudge once objectives exist, never a demand before
        for path in lead_projects:
            if not any(tgt in live_objectives for tgt in alignment.get(path, ())):
                rep.add("objectives", f"`{path}` — a lead Project whose *Expected impact* links no live objective")
    for path in live_objectives:
        if str(pages[path][0].get("level")) != "team":
            continue
        quarter = str(pages[path][0].get("quarter"))
        # only the same quarter's company objectives are candidates: last quarter's is not the
        # one this team objective rolls up to, and its absence is not a missing link
        peers = {c for c in company_objectives if str(pages[c][0].get("quarter")) == quarter}
        if peers and not any(tgt in peers for tgt in alignment.get(path, ())):
            rep.add("objectives", f"`{path}` — a team Objective whose *Objective* section links no {quarter} "
                                  f"company objective")

    # ---- orphans
    for path in pages:
        if path.startswith("reviews/"):
            continue
        if not inbound.get(path):
            rep.add("orphans", f"`{path}` has no inbound link from another page")

    # ---- index coverage
    for d in sorted({p.parent for p in wiki.rglob("*.md")} | {wiki}):
        idx = d / "index.md"
        drel = rel(d, wiki) if d != wiki else ""
        if not idx.exists():
            rep.add("index", f"`{drel or '.'}/` has no index.md")
            continue
        text = idx.read_text(encoding="utf8")
        fm, body, err = pc.split_frontmatter(text)
        if err:
            rep.add("conformance", f"`{drel or '.'}/index.md` frontmatter is not valid YAML: {err}", error=True)
        elif d == wiki:
            if not fm or str(fm.get("okf_version")) != "0.2":
                rep.add("index", "bundle-root index.md should declare `okf_version: \"0.2\"`")
        elif fm:
            rep.add("index", f"`{drel}/index.md` carries frontmatter — only the bundle root may")
        listed = set()
        for _t, target in prose_links(body):
            if target.startswith(("http://", "https://")):
                continue
            tp = (d / target).resolve()
            listed.add(target)
            if not tp.exists():
                rep.add("index", f"`{drel or '.'}/index.md` links to `{target}` which does not exist")
        for p in sorted(d.glob("*.md")):
            if p.name in RESERVED:
                continue
            if p.name not in listed:
                rep.add("index", f"`{rel(p, wiki)}` is not listed in its index.md")

    # ---- log format
    log = wiki / "log.md"
    if not log.exists():
        rep.add("log", "wiki/log.md is missing")
    else:
        lines = log.read_text(encoding="utf8").splitlines()
        if not lines or not lines[0].startswith("# "):
            rep.add("log", "log.md should start with a `# ` heading")
        last = None
        for i, line in enumerate(lines, 1):
            if line.startswith("## "):
                d = pc.parse_date(line[3:].strip())
                if not d or line[3:].strip() != d.isoformat():
                    rep.add("log", f"log.md line {i}: heading `{line}` is not `## YYYY-MM-DD`")
                elif last and d > last:
                    rep.add("log", f"log.md line {i}: `{d}` is out of order — newest first")
                last = d or last
            elif line.startswith("* "):
                m = re.match(r"\* \*\*([A-Za-z]+)\*\*:", line)
                if not m:
                    rep.add("log", f"log.md line {i}: bullet is not `* **Label**: …`")
                elif m.group(1) not in LOG_LABELS:
                    rep.add("log", f"log.md line {i}: label `{m.group(1)}` is not one of {sorted(LOG_LABELS)}")

    # ---- output
    summary = {
        "pages": len(pages), "by_type": dict(sorted(counts.items())),
        "tiers": {k: sum(1 for fm, _ in pages.values() if fm and pc.trust_tier(fm) == k)
                  for k in ("unverified", "machine-confirmed", "human-reviewed", "changed-since-verified")},
        "errors": rep.errors, "today": today.isoformat(),
    }
    if as_json:
        print(json.dumps({"summary": summary, "findings": rep.findings}, indent=2))
    else:
        print(f"# Lint — {today.isoformat()}\n")
        print(f"{summary['pages']} pages · tiers {summary['tiers']} · conformance errors: {rep.errors}\n")
        order = ["fixed", "conformance", "trust", "registry", "headings", "provenance", "stale", "expiring",
                 "changed-since-verified", "old-drafts", "rfcs-stuck", "systems", "projects", "pointers", "objectives",
                 "links", "orphans", "index", "log"]
        for check in order + [c for c in rep.findings if c not in order]:
            items = rep.findings.get(check)
            if not items:
                continue
            print(f"## {check} ({len(items)})")
            for m in items:
                print(f"- {m}")
            print()
        if not rep.findings:
            print("No findings.")
    return 1 if rep.errors else 0


def cli() -> None:
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
