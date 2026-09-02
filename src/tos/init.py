"""/tos-init — create (or refresh) the data root described by the config.

    uv run tos-init [--with-examples] [--remove-examples] [--dry-run]

Creates data.root with raw/ and wiki/ (every directory with its index.md), the
bundle-root index.md carrying okf_version "0.2", log.md with a Creation entry,
raw/inbox/pull.md, the vault files from schema/vault/, optionally the worked
examples from schema/examples/, and a git repository. Re-running never
overwrites an index, the log, or a page; it re-installs the vault files and
reports engine/config drift.
"""
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

from tos import common as pc
from tos.bundle import WIKI_DIRS, add_index_entry, index_body

RAW_DIRS = ["inbox", "notes", "pinned", "metrics", "assets"]

PULL_MD = """# Pointers to pull

One pointer per line. `/tos-pull` reads each through its connector, writes a Source
page, and removes the line. Add `--pin` after a pointer to keep a verbatim copy
under raw/pinned/. Lines starting with `#` are ignored.

"""


def ensure(path: Path, content: str, dry: bool, created: list):
    if path.exists():
        return
    created.append(path)
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf8")


def install_vault(root: Path, dry: bool, log: list):
    src = pc.engine_path("schema", "vault")
    for p in src.rglob("*"):
        if p.is_file():
            dest = root / p.relative_to(src)
            log.append(f"vault: {dest.relative_to(root)}")
            if not dry:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, dest)


def fill_placeholders(text: str, now: dt.datetime) -> str:
    def stale(days):
        return (now.date() + dt.timedelta(days=days)).isoformat()
    repl = {
        "{{GENERATED_AT}}": now.replace(microsecond=0).isoformat(),
        "{{DATE}}": now.date().isoformat(),
        "{{DATE-1}}": (now.date() - dt.timedelta(days=1)).isoformat(),
        "{{DATE-3}}": (now.date() - dt.timedelta(days=3)).isoformat(),
        "{{DATE-8}}": (now.date() - dt.timedelta(days=8)).isoformat(),
        "{{DATE+7}}": (now.date() + dt.timedelta(days=7)).isoformat(),
        "{{DATE+14}}": (now.date() + dt.timedelta(days=14)).isoformat(),
        "{{STALE_30}}": stale(30), "{{STALE_60}}": stale(60), "{{STALE_90}}": stale(90), "{{STALE_365}}": stale(365),
        "{{QUARTER}}": f"{now.year}-Q{(now.month - 1) // 3 + 1}",
        "{{ISO_WEEK}}": now.strftime("%G-W%V"),
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def install_examples(root: Path, now: dt.datetime, dry: bool, log: list):
    src = pc.ENGINE_ROOT / "schema" / "examples"
    if not src.exists():
        return
    for p in sorted(src.rglob("*.md")):
        rel = p.relative_to(src)
        if rel.parts[0] == "_raw":
            dest = root / "raw" / Path(*rel.parts[1:])
            if not dest.exists():
                log.append(f"example: raw/{Path(*rel.parts[1:])}")
                if not dry:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(fill_placeholders(p.read_text(encoding="utf8"), now), encoding="utf8")
            continue
        dest = root / "wiki" / rel
        if dest.exists():
            continue
        text = fill_placeholders(p.read_text(encoding="utf8"), now)
        fm, _, err = pc.split_frontmatter(text)
        if err:
            sys.exit(f"engine example {p} has unparseable frontmatter: {err}")
        log.append(f"example: wiki/{rel}")
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf8")
            add_index_entry(dest.parent / "index.md", str((fm or {}).get("title", rel.stem)), rel.name,
                            str((fm or {}).get("description", "example page")), dry)


def remove_examples(root: Path, dry: bool, log: list):
    src = pc.ENGINE_ROOT / "schema" / "examples"
    for p in sorted(src.rglob("*.md")):
        rel = p.relative_to(src)
        if rel.parts[0] == "_raw":
            dest = root / "raw" / Path(*rel.parts[1:])
            if dest.exists():
                log.append(f"remove example: raw/{Path(*rel.parts[1:])}")
                if not dry:
                    dest.unlink()
            continue
        dest = root / "wiki" / rel
        if not dest.exists():
            continue
        fm, _, _, err = pc.read_page(dest)
        if err:
            log.append(f"skipped (unreadable frontmatter): wiki/{rel} — {err}")
            continue
        if "example" not in (fm or {}).get("tags", []):
            continue
        log.append(f"remove example: wiki/{rel}")
        if not dry:
            dest.unlink()
            idx = dest.parent / "index.md"
            if idx.exists():
                kept = [ln for ln in idx.read_text(encoding="utf8").splitlines() if f"]({rel.name})" not in ln]
                idx.write_text("\n".join(kept) + "\n", encoding="utf8")


def git(root: Path, *args, check=False):
    cmd = ["git"]
    ident = subprocess.run(["git", "config", "user.email"], cwd=root, capture_output=True, text=True)
    if not ident.stdout.strip():  # no identity configured: commit as the engine without touching global config
        cmd += ["-c", "user.name=tos-engine", "-c", "user.email=tos@localhost"]
    return subprocess.run([*cmd, *args], cwd=root, capture_output=True, text=True, check=check)


def main(argv):
    dry = "--dry-run" in argv
    cfg = pc.load_config()
    root = pc.data_root(cfg)
    now = pc.now(cfg)
    created, log = [], []

    if "--remove-examples" in argv:
        remove_examples(root, dry, log)
        for line in log:
            print(line)
        return 0

    existed = root.exists()
    if not dry:
        root.mkdir(parents=True, exist_ok=True)
    for d in RAW_DIRS:
        p = root / "raw" / d
        if not p.exists():
            created.append(p)
            if not dry:
                p.mkdir(parents=True, exist_ok=True)
                (p / ".gitkeep").write_text("", encoding="utf8")
    ensure(root / "raw" / "inbox" / "pull.md", PULL_MD, dry, created)
    for rel, (title, desc) in WIKI_DIRS.items():
        d = root / "wiki" / rel
        if not dry:
            d.mkdir(parents=True, exist_ok=True)
        ensure(d / "index.md", index_body(rel, title, desc), dry, created)
    creation = (f"* **Creation**: data root initialised by tos-engine {pc.ENGINE_VERSION} "
                f"(config engine \"{cfg.get('engine')}\").\n")
    ensure(root / "wiki" / "log.md",
           f"# Data update log\n\n## {now.date().isoformat()}\n{creation}",
           dry, created)
    ensure(root / ".gitignore", ".obsidian/workspace.json\n.obsidian/workspace-mobile.json\n.DS_Store\n", dry, created)
    install_vault(root, dry, log)
    if "--with-examples" in argv:
        install_examples(root, now, dry, log)

    # git
    if not dry and not (root / ".git").exists():
        r = git(root, "init", "-q")
        if r.returncode == 0:
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", f"Creation: data root initialised by tos-engine {pc.ENGINE_VERSION}")
            log.append("git: repository initialised and first commit made")
        else:
            log.append("git: not available — initialise the repository yourself")

    print(f"data root: {root} ({'existed' if existed else 'created'})")
    drift = pc.engine_drift(cfg)
    if drift:
        print(drift)
    for p in created:
        print(f"created: {p.relative_to(root)}")
    for line in log:
        print(line)
    if dry:
        print("(dry run — nothing written)")
    return 0


def cli() -> None:
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
