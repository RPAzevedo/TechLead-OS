"""/init — create (or refresh) the data root described by the config.

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

WIKI_DIRS = {
    # path: (title, description)
    "": ("TechLead OS", "the OKF bundle root — start here"),
    "delivery": ("Delivery", "initiatives, projects, objectives, delivery metrics"),
    "delivery/initiatives": ("Initiatives", "cross-functional efforts and company moving parts"),
    "delivery/projects": ("Projects", "what the team delivers"),
    "delivery/objectives": ("Objectives", "the quarter's OKRs (phase 2)"),
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
RAW_DIRS = ["inbox", "notes", "pinned", "metrics", "assets"]

PULL_MD = """# Pointers to pull

One pointer per line. `/pull` reads each through its connector, writes a Source
page, and removes the line. Add `--pin` after a pointer to keep a verbatim copy
under raw/pinned/. Lines starting with `#` are ignored.

"""


def index_body(rel: str, title: str, desc: str, root: Path) -> str:
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
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def add_index_entry(index_path: Path, title: str, filename: str, desc: str, dry: bool):
    text = index_path.read_text(encoding="utf8") if index_path.exists() else ""
    line = f"* [{title}]({filename}) - {desc}"
    if f"]({filename})" in text:
        return
    if "## Pages" in text:
        stripped = text.rstrip("\n")
        text = stripped + ("\n\n" if stripped.endswith("## Pages") else "\n") + line + "\n"
    else:
        text = text.rstrip("\n") + "\n\n## Pages\n\n" + line + "\n"
    if not dry:
        index_path.write_text(text, encoding="utf8")


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
    now = dt.datetime.now().astimezone()
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
        ensure(d / "index.md", index_body(rel, title, desc, root), dry, created)
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
    if str(cfg.get("engine")) not in (pc.ENGINE_VERSION, pc.ENGINE_VERSION.rsplit(".", 1)[0]):
        print(f"note: config engine \"{cfg.get('engine')}\" ≠ engine {pc.ENGINE_VERSION}")
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
