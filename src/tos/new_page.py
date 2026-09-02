"""tos-new — create a page from its template, frontmatter computed from the registry.

    uv run tos-new <Type> <slug> --title "…" [--description "…"] [--by <actor>]
                   [--dir <one of the type's directories>] [--log "Label: text"] [--dry-run]

Copies schema/templates/<type>.md, fills `title`, `description`, `generated`
and `stale_after` (today + the type's horizon; `~` for a record), and lists the
page in its directory's index.md. The body placeholders stay for the agent to
fill; `status: draft` comes from the template. The log line is opt-in (`--log`)
because the convention is one bullet per operation, not per page (CLAUDE.md §2).
"""
from __future__ import annotations

import datetime as dt
import re
import sys

from tos import bundle, index_add
from tos import common as pc
from tos.index_add import _flag

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
QUARTER_PREFIX_RE = re.compile(r"^\d{4}-q[1-4]-")


def main(argv) -> int:
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    title = description = by = subdir = log_arg = None
    err = None
    for name in ("--title", "--description", "--by", "--dir", "--log"):
        argv, val, err = _flag(argv, name)
        if err:
            break
        if name == "--title":
            title = val
        elif name == "--description":
            description = val
        elif name == "--by":
            by = val
        elif name == "--dir":
            subdir = val
        else:
            log_arg = val
    if err or len(argv) != 2 or not title:
        print(err or "usage: tos-new <Type> <slug> --title \"…\" [--description …] [--by <actor>] "
                     "[--dir <d>] [--log \"Label: text\"] [--dry-run]", file=sys.stderr)
        return 2
    type_name, slug = argv
    cfg = pc.load_config()
    wiki = pc.data_root(cfg) / "wiki"
    registry = pc.load_registry()
    if type_name not in registry:
        print(f"`{type_name}` is not in schema/types.md — one of: {', '.join(sorted(registry))}", file=sys.stderr)
        return 2
    entry = registry[type_name]
    phase = int((cfg.get("rollout") or {}).get("phase", 1))
    type_phase = int(entry["phase"].lstrip("P"))
    if type_phase > phase:
        print(f"`{type_name}` is a phase-{type_phase} type; the config's rollout.phase is {phase} (CLAUDE.md §3)",
              file=sys.stderr)
        return 1

    if type_name == "Source" and not DATE_PREFIX_RE.match(slug):
        slug = f"{pc.today(cfg).isoformat()}-{slug}"
    if not SLUG_RE.match(slug):
        print(f"slug `{slug}` — lowercase, hyphenated, ASCII, no extension (CLAUDE.md §2)", file=sys.stderr)
        return 2
    if type_name == "Objective" and not QUARTER_PREFIX_RE.match(slug):
        print(f"warning: Objective slugs are quarter-prefixed (`2026-q3-…`); `{slug}` is not")
    label = log_text = None
    if log_arg:
        label, sep, log_text = log_arg.partition(": ")
        if not sep or label not in bundle.LOG_LABELS:
            print(f"--log takes \"Label: text\" with a label from {sorted(bundle.LOG_LABELS)}", file=sys.stderr)
            return 2

    dirs = entry["dir"]
    if dirs and dirs[0].endswith(".md"):  # Team lives in a single file, not a directory of pages
        dest = wiki / dirs[0]
    elif len(dirs) > 1:
        if subdir not in dirs:
            print(f"a `{type_name}` lives in one of {dirs} — pass --dir", file=sys.stderr)
            return 2
        dest = wiki / subdir / f"{slug}.md"
    else:
        dest = wiki / dirs[0] / f"{slug}.md"
    if dest.exists():
        print(f"`{dest.relative_to(wiki)}` already exists — tos-new never overwrites", file=sys.stderr)
        return 1
    # before the page is written: a page the index operation then refuses would be an orphan
    if bundle.ensure_index(wiki, dest.parent, dry):
        print(f"created: {index_add.rel_index(wiki, dest.parent)} (it was missing)")

    template = pc.engine_path("schema", "templates", type_name.lower().replace(" ", "-") + ".md")
    now = pc.now(cfg)
    stale = (f"stale_after: {(now.date() + dt.timedelta(days=entry['horizon_days'])).isoformat()}"
             if entry["horizon_days"] else pc.STALE_AFTER_RECORD)
    repl = {
        "title": f"title: {bundle.yaml_scalar(title)}",
        "generated": f"generated: {{ by: {by or 'claude-code/unknown'}, at: {now.isoformat()} }}",
        "stale_after": stale,
    }
    if description:
        repl["description"] = f"description: {bundle.yaml_scalar(description)}"
    text = bundle.edit_frontmatter_lines(template.read_text(encoding="utf8"), repl)
    fm, _, fm_err = pc.split_frontmatter(text)
    if fm_err:
        sys.exit(f"template {template.name} no longer parses after filling: {fm_err}")
    if not dry:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf8")
    print(f"created: {dest.relative_to(wiki)} (status: draft, {stale.split(': ', 1)[1]})")
    bundle.add_index_entry(dest.parent / "index.md", title, dest.name,
                           description or "(description pending)", dry)
    print(f"indexed in {dest.parent.relative_to(wiki) if dest.parent != wiki else '.'}/index.md")
    if label:
        print(bundle.log_add(wiki / "log.md", label, log_text, now.date(), dry=dry))
    if dry:
        print("(dry run — nothing written)")
    return 0


def cli() -> None:
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
