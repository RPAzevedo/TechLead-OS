"""/tos-lint, deterministic half — OKF v0.2 conformance and TechLead OS trust checks.

    uv run tos-lint [--json] [--today YYYY-MM-DD]

No LLM, no network. Reads the config for data.root and the review settings,
walks wiki/, and prints a markdown report (or JSON). Exit code 1 when a
conformance error is found, 0 otherwise. The agent pass (contradictions,
unsupported claims, missing cross-references, the people policy, source drift)
is described in CLAUDE.md §4.5 and is not this script's job.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from tos import common as pc

RESERVED = {"index.md", "log.md"}
STATUSES = {"draft", "stable", "deprecated"}
LOG_LABELS = {"Creation", "Pull", "Ingest", "Query", "Brief", "Measure",
              "Lint", "Verify", "Review", "Deprecate", "Migration"}
ROLES = {"lead", "support"}
STAGES = {"discovery", "build", "pilot", "rollout", "paused", "done"}
LEVELS = {"company", "team"}
WEEKLY_LABELS = {"Progress", "Challenges & risks", "Blockers & support needed",
                 "Open questions & decisions", "Notes"}
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FOOTNOTE_DEF_RE = re.compile(r"^\[\^([^\]]+)\]:", re.M)
QUARTER_RE = re.compile(r"^\d{4}-Q[1-4]$")
WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
TOP_BULLET_RE = re.compile(r"^[-*] +(.*)$", re.M)          # nested bullets under a label are indented
WEEKLY_LABEL_RE = re.compile(r"\*\*([^*]+)\*\*:[ \t]*\S")


def load_registry() -> dict:
    """Parse schema/types.md into {type: {dir, horizon, gate}} from the markdown table."""
    reg = {}
    text = pc.engine_path("schema", "types.md").read_text(encoding="utf8")
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("| Type") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        name, phase, lives, horizon, gate, _heads = cells[:6]
        if name in ("Field",) or not name:
            continue
        reg[name] = {"phase": phase, "dir": lives.strip("`"), "horizon": horizon, "gate": gate}
    return reg


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
    for _text, target in LINK_RE.findall(m.group(1)):
        if target.startswith(("http://", "https://", "mailto:", "#", "/")):
            continue
        try:
            found.add(rel((page_dir / target.split("#")[0]).resolve(), wiki.resolve()))
        except ValueError:
            continue
    return found


def main(argv):
    as_json = "--json" in argv
    today = pc.today()
    if "--today" in argv:
        today = pc.parse_date(argv[argv.index("--today") + 1]) or today
    cfg = pc.load_config()
    root = pc.data_root(cfg)
    wiki = root / "wiki"
    if not wiki.exists():
        sys.exit(f"no wiki at {wiki} — run /tos-init first")
    expiring_days = int(pc.review_setting(cfg, "expiring_days", 7))
    draft_age = int(pc.review_setting(cfg, "draft_age_days", 14))
    weekly_grace = int(pc.review_setting(cfg, "weekly_log_grace_days", 16))
    registry = load_registry()
    rep = Report()

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
        if str(t) not in registry:
            rep.add("registry", f"`{path}` has type `{t}` which is not in schema/types.md")
        else:
            want = registry[str(t)]["dir"]
            if want and not any(path.startswith(w.strip()) for w in want.split(",")) and str(t) != "Team":
                rep.add("registry", f"`{path}` is a `{t}` but lives outside `{want}`")
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
                alignment[path] = section_links(body, "Expected impact", (wiki / path).parent, wiki)
                if newest is not None:
                    if (today - newest).days > weekly_grace:
                        rep.add("projects", f"`{path}` — an active Project with no weekly entry since "
                                            f"{newest.isoformat()} (its Monday) — pause or deprecate it if it stopped")
                elif seen_a_monday:
                    what = "no entry in its *Weekly log*" if wl else "no *Weekly log* section"
                    rep.add("projects", f"`{path}` — an active Project with {what}")
        if str(t) == "Objective":
            alignment[path] = section_links(body, "Objective", (wiki / path).parent, wiki)
            level = fm.get("level")
            if level is None or str(level) not in LEVELS:
                rep.add("objectives", f"`{path}` has `level: {level!r}` — must be company | team")
            quarter = fm.get("quarter")
            if quarter is None or not QUARTER_RE.match(str(quarter)):
                rep.add("objectives", f"`{path}` has `quarter: {quarter!r}` — must be `YYYY-Qn`, e.g. 2026-Q3")
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
        page_dir = (wiki / path).parent
        for _text, target in LINK_RE.findall(body):
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
        for _t, target in LINK_RE.findall(body):
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
        order = ["conformance", "trust", "registry", "provenance", "stale", "expiring", "changed-since-verified",
                 "old-drafts", "rfcs-stuck", "systems", "projects", "objectives", "links", "orphans", "index", "log"]
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
