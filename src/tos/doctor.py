"""tos-doctor — the onboarding checklist, report-only.

    uv run tos-doctor [--json]

Checks the config, the data root's layout, engine/config drift, the vault
files, the data repository, the config's MCP connector names against
`claude mcp list`, and (report-only) whether the engine's deny list names
those servers. Fixes nothing, proposes nothing in place. Exit 1 only when the
install is unusable: no readable config, or no data root.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

from tos import bundle
from tos import common as pc
from tos import init as tos_init


class Checkup:
    def __init__(self):
        self.rows = []  # {check, status: ok|warn|fail|skip, detail}
        self.fatal = False

    def add(self, check, status, detail=""):
        self.rows.append({"check": check, "status": status, "detail": detail})
        if status == "fail":
            self.fatal = True


MCP_LINE_RE = re.compile(r"^(\S.*?):\s")


def claude_mcp_list() -> str | None:
    """The raw `claude mcp list` output, or None when the CLI is unavailable."""
    try:
        r = subprocess.run(["claude", "mcp", "list"], capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def parse_mcp_servers(out: str) -> set:
    """The server names in `claude mcp list` output — `<name>: <address> - <status>` per line.

    Exact names, never a substring test: `mcp:atlassian` matching the text of
    `plugin_atlassian_atlassian` is the very mismatch this check exists to catch,
    since the tools would be `mcp__plugin_atlassian_atlassian__…` either way.
    """
    names = set()
    for line in out.splitlines():
        m = MCP_LINE_RE.match(line.strip())
        if m:
            names.add(m.group(1).strip())
    return names


def tool_prefix(name: str) -> str:
    """The server name as it appears inside a tool id — non-alphanumerics become underscores.

    `claude.ai Google Drive` is denied as `mcp__claude_ai_Google_Drive__create_file`.
    """
    return re.sub(r"[^A-Za-z0-9]", "_", name)


def main(argv) -> int:
    as_json = "--json" in argv
    c = Checkup()

    # config
    cfg, err = pc.try_load_config()
    if err:
        c.add("config", "fail", err.replace("\n", " — "))
        return finish(c, as_json)
    c.add("config", "ok", cfg["_path"])
    data = cfg.get("data") or {}
    actor = str(data.get("actor") or "")
    c.add("data.actor", "ok" if actor.startswith("human:") and "CHANGE_ME" not in actor else "warn",
          actor or "missing — the human actor in every verified entry")
    # a nonempty string is not enough: with `Australia/Melborne` every helper falls back to the
    # host zone, and the page contract's offsets and dates are the config's zone or nothing
    tz = str(data.get("timezone") or "").strip()
    if not tz:
        c.add("data.timezone", "warn", "missing — the zone every generated.at and stale_after is written in")
    elif pc.load_timezone(tz) is None:
        c.add("data.timezone", "warn", f"{tz} — not an IANA timezone; the helpers would fall back "
                                       "to the host zone and write the wrong offset")
    else:
        c.add("data.timezone", "ok", tz)
    phase = (cfg.get("rollout") or {}).get("phase", 1)
    c.add("rollout.phase", "ok" if phase in (1, 2, 3, 4) else "warn", str(phase))
    drift = pc.engine_drift(cfg)
    c.add("engine", "warn" if drift else "ok", drift or f"{pc.ENGINE_VERSION} (config matches)")

    # data root and layout
    root = pc.data_root(cfg)
    if not root.is_dir():
        # a root that is a regular file is as unusable as a missing one, and /tos-init
        # cannot create the layout over it
        c.add("data root", "fail", f"{root} does not exist — run /tos-init" if not root.exists()
              else f"{root} is not a directory — data.root names the directory raw/ and wiki/ live in")
        return finish(c, as_json)
    c.add("data root", "ok", str(root))
    missing = [f"raw/{d}" for d in tos_init.RAW_DIRS if not (root / "raw" / d).is_dir()]
    missing += [f"wiki/{rel}/index.md".replace("//", "/") for rel in bundle.WIKI_DIRS
                if not (root / "wiki" / rel / "index.md").exists()]
    for f in ("wiki/log.md", "raw/inbox/pull.md"):
        if not (root / f).exists():
            missing.append(f)
    c.add("layout", "warn" if missing else "ok",
          f"missing: {', '.join(missing)} — re-run /tos-init" if missing else
          f"{len(bundle.WIKI_DIRS)} wiki directories, raw/, log.md, pull.md")
    root_idx = root / "wiki" / "index.md"
    if root_idx.exists():
        fm, _, _, _ = pc.read_page(root_idx)
        c.add("okf_version", "ok" if fm and str(fm.get("okf_version")) == "0.2" else "warn",
              'bundle root declares okf_version "0.2"' if fm and str(fm.get("okf_version")) == "0.2"
              else "bundle-root index.md should declare `okf_version: \"0.2\"`")
    vault_missing = [f for f in ("Home.md", ".obsidian") if not (root / f).exists()]
    c.add("vault", "warn" if vault_missing else "ok",
          f"missing {', '.join(vault_missing)} — re-run /tos-init" if vault_missing
          else "Home.md and .obsidian/ present")

    # git
    if not (root / ".git").exists():
        c.add("git", "warn", "the data root is not a git repository — /tos-init initialises one")
    else:
        r = tos_init.git(root, "status", "--porcelain")
        if r.returncode != 0:
            c.add("git", "warn", "git is not available")
        else:
            dirty = len([ln for ln in r.stdout.splitlines() if ln.strip()])
            c.add("git", "ok", "clean" if not dirty else f"{dirty} uncommitted change(s)")
            ident = tos_init.git(root, "config", "user.email")
            if not ident.stdout.strip():
                c.add("git identity", "warn", "no user.email — commits fall back to tos-engine <tos@localhost>")

    # connectors vs the MCP servers actually installed
    servers = {}  # mcp server name -> connector names
    for name, conn in (cfg.get("connectors") or {}).items():
        provider = str((conn or {}).get("provider") or "")
        if provider.startswith("mcp:"):
            servers.setdefault(provider[4:], []).append(name)
    mcp_out = claude_mcp_list()
    installed = parse_mcp_servers(mcp_out) if mcp_out is not None else set()
    prefixes = {tool_prefix(n) for n in installed}
    if mcp_out is None:
        c.add("mcp servers", "skip", "`claude mcp list` unavailable — could not compare connector names")
    else:
        for server, names in sorted(servers.items()):
            found = server in installed or server in prefixes
            c.add(f"mcp:{server}", "ok" if found else "warn",
                  f"connector(s) {', '.join(names)}" + ("" if found else
                  f" — no server named `{server}`; installed: {', '.join(sorted(installed)) or 'none'}"))

    # deny-list coverage — report only (the 0.7.4 attempts at enforcing this were both withdrawn)
    settings = pc.ENGINE_ROOT / ".claude" / "settings.json"
    if settings.exists() and mcp_out is not None:
        deny = (json.loads(settings.read_text(encoding="utf8")).get("permissions") or {}).get("deny") or []
        guarded = {"__".join(d.split("__")[1:-1]) for d in deny if d.startswith("mcp__")}
        # coverage is per server: one guarded connector saying "ok" for all of them is how a
        # newly wired-up connector goes unguarded without anyone hearing about it
        in_use = {}  # tool-prefix form -> the connectors that named it
        for server, names in servers.items():
            prefix = tool_prefix(server) if server in installed else server if server in prefixes else None
            if prefix:
                in_use.setdefault(prefix, []).extend(names)
        uncovered = [f"`{p}` ({', '.join(in_use[p])})" for p in sorted(in_use) if p not in guarded]
        if not in_use:
            c.add("deny list", "skip", "no configured connector's server is installed — nothing to cover")
        elif uncovered:
            c.add("deny list", "warn", f"no deny entry guards {', '.join(uncovered)} — a write tool of that "
                                       "server would be allowed; add its write tools to .claude/settings.json")
        else:
            c.add("deny list", "ok", f"every connector server in use is guarded: {', '.join(sorted(in_use))}")

    return finish(c, as_json)


def finish(c: Checkup, as_json: bool) -> int:
    if as_json:
        print(json.dumps(c.rows, indent=2, ensure_ascii=False))
    else:
        width = max(len(r["check"]) for r in c.rows)
        for r in c.rows:
            print(f"{r['status']:<5} {r['check']:<{width}}  {r['detail']}")
        bad = [r for r in c.rows if r["status"] in ("warn", "fail")]
        print(f"\n{len(c.rows)} checks — {len(bad)} to look at" if bad else f"\n{len(c.rows)} checks — all good")
    return 1 if c.fatal else 0


def cli() -> None:
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
