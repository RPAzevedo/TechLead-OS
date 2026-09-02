"""tos-index — add or refresh a page's entry in its directory's index.md.

    uv run tos-index <wiki-relative-page.md> [--title "…"] [--desc "…"] [--deprecated] [--dry-run]

Title and description default to the page's own frontmatter so the entry and
the page cannot disagree; the flags override. `--deprecated` files the entry
under a `## Deprecated` heading (guardrail 4), creating it when absent.
"""
from __future__ import annotations

import sys
from pathlib import Path

from tos import bundle
from tos import common as pc


def rel_index(wiki: Path, directory: Path) -> str:
    """`concepts/index.md`, or `./index.md` at the bundle root — for the printed line."""
    d = directory.relative_to(wiki)
    return f"{d}/index.md" if str(d) != "." else "./index.md"


def _flag(argv, name):
    if name in argv:
        i = argv.index(name)
        if i + 1 >= len(argv):
            return argv, None, f"{name} takes a value"
        v = argv[i + 1]
        return argv[:i] + argv[i + 2:], v, None
    return argv, None, None


def main(argv) -> int:
    dry = "--dry-run" in argv
    deprecated = "--deprecated" in argv
    argv = [a for a in argv if a not in ("--dry-run", "--deprecated")]
    argv, title, err = _flag(argv, "--title")
    if not err:
        argv, desc, err = _flag(argv, "--desc")
    if err or len(argv) != 1:
        print(err or "usage: tos-index <wiki-relative-page.md> [--title …] [--desc …] [--deprecated] [--dry-run]",
              file=sys.stderr)
        return 2
    cfg = pc.load_config()
    wiki = pc.data_root(cfg) / "wiki"
    page = pc.bundle_path(wiki, argv[0])
    if page is None:
        print(f"`{argv[0]}` points outside the bundle — pass a path relative to {wiki}", file=sys.stderr)
        return 2
    if page.name in ("index.md", "log.md") or not str(Path(argv[0])).endswith(".md"):
        print(f"`{argv[0]}` is not an indexable page", file=sys.stderr)
        return 2
    if not page.exists():
        print(f"`{argv[0]}` does not exist under {wiki} — an index entry for a missing page is a lint finding",
              file=sys.stderr)
        return 1
    fm, _, _, fm_err = pc.read_page(page)
    if fm_err and not (title and desc):
        print(f"`{argv[0]}` frontmatter is unreadable ({fm_err}); pass --title and --desc", file=sys.stderr)
        return 1
    title = title or str((fm or {}).get("title") or page.stem)
    desc = desc or str((fm or {}).get("description") or "")
    heading = "Deprecated" if deprecated else "Pages"
    if bundle.ensure_index(wiki, page.parent, dry):
        print(f"created: {rel_index(wiki, page.parent)} (it was missing)")
    action = bundle.add_index_entry(page.parent / "index.md", title, page.name, desc, dry,
                                    refresh=True, heading=heading)
    print(f"{action}: * [{title}]({page.name}) - {desc}" + (f"  (under ## {heading})" if deprecated else ""))
    if dry:
        print("(dry run — nothing written)")
    return 0


def cli() -> None:
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
