"""tos-log — append a labelled entry to wiki/log.md in the canonical shape.

    uv run tos-log <Label> <text…> [--date YYYY-MM-DD] [--dry-run]

Writes `* **Label**: text` under the day's `## YYYY-MM-DD` heading, creating
the heading in date order (newest first) when absent. Prints the bullet it
wrote — the calling command reuses it as the commit message. Does not commit:
the operation that logs is the one that commits (CLAUDE.md §4).
"""
from __future__ import annotations

import sys

from tos import bundle
from tos import common as pc


def main(argv) -> int:
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    cfg = pc.load_config()
    date = pc.today(cfg)
    if "--date" in argv:
        i = argv.index("--date")
        date = pc.parse_date(argv[i + 1]) if i + 1 < len(argv) else None
        if date is None:
            print("--date takes YYYY-MM-DD", file=sys.stderr)
            return 2
        del argv[i:i + 2]
    if len(argv) < 2:
        print("usage: tos-log <Label> <text…> [--date YYYY-MM-DD] [--dry-run]", file=sys.stderr)
        return 2
    label, text = argv[0], " ".join(argv[1:])
    if label not in bundle.LOG_LABELS:
        print(f"label `{label}` is not one of {sorted(bundle.LOG_LABELS)}", file=sys.stderr)
        return 2
    log_path = pc.data_root(cfg) / "wiki" / "log.md"
    try:
        bullet = bundle.log_add(log_path, label, text, date, dry=dry)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(bullet)
    if dry:
        print("(dry run — nothing written)")
    return 0


def cli() -> None:
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
