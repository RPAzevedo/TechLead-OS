"""/tos-deny — the deny list guardrail 11 needs, worked out from your config.

    uv run tos-deny [--write] [--json]

A Claude Code permission rule matches a tool by its exact name, and MCP tool
names embed the server name *you* chose: `mcp__<server>__<tool>`. An entry
naming a server you do not have is ignored without an error, which is how the
Atlassian entries shipped in 0.7.1 came to guard nothing at all.

So the names cannot be guessed in the engine. This reads the server names out of
`connectors.*` in your config, crosses them with the write-tool vocabulary in
`schema/connector-writes.yaml`, and reports which entries are missing from
`.claude/settings.json` and `.claude/settings.local.json`. `--write` adds them to
the local file, which is per-machine and gitignored — it only ever appends, so a
rule you added by hand is never removed.

Exit 1 while any entry is missing, 0 once the deny list covers the config.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tos import common as pc

SETTINGS = ("settings.json", "settings.local.json")


def write_vocabulary() -> dict[str, list[str]]:
    """Write-capable tool names per connector kind, from schema/connector-writes.yaml."""
    text = pc.engine_path("schema", "connector-writes.yaml").read_text(encoding="utf8")
    vocab = pc.load_yaml(text)
    if not isinstance(vocab, dict):
        sys.exit("schema/connector-writes.yaml is not a mapping of kind -> [tool, …]")
    return {k: list(v or []) for k, v in vocab.items()}


def servers(cfg: dict) -> dict[str, list[str]]:
    """{connector: [mcp server name, …]} from the config.

    `mcp_server` names the server as `claude mcp list` shows it, and may be a
    list when one connector is served by more than one (Jira and Confluence
    often are). Absent, it falls back to the part after `mcp:` in `provider`,
    which is what the config meant before the two were distinguished.
    """
    out = {}
    for name, spec in (cfg.get("connectors") or {}).items():
        if not isinstance(spec, dict):
            continue
        declared = spec.get("mcp_server")
        if declared is None:
            provider = str(spec.get("provider") or "")
            declared = provider.split("mcp:", 1)[1] if provider.startswith("mcp:") else None
        if not declared:
            continue  # filesystem and the like expose no MCP server
        out[name] = [declared] if isinstance(declared, str) else [str(d) for d in declared]
    return out


def kind_of(spec: dict) -> str | None:
    provider = str((spec or {}).get("provider") or "")
    return provider.split("mcp:", 1)[1] if provider.startswith("mcp:") else None


def expected(cfg: dict, vocab: dict[str, list[str]]) -> dict[str, list[str]]:
    """{connector: [deny entry, …]} — every write tool of its kind, on every server it names."""
    out = {}
    conns = cfg.get("connectors") or {}
    for name, names in servers(cfg).items():
        tools = vocab.get(kind_of(conns.get(name)) or "", [])
        out[name] = [f"mcp__{s}__{t}" for s in names for t in tools]
    return out


def present(engine_root: Path) -> set[str]:
    """Every deny entry already in force, across both settings files."""
    found: set[str] = set()
    for fname in SETTINGS:
        p = engine_root / ".claude" / fname
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf8"))
        except json.JSONDecodeError as e:
            sys.exit(f"{p} is not valid JSON: {e}")
        found |= set((data.get("permissions") or {}).get("deny") or [])
    return found


def add_to_local(engine_root: Path, entries: list[str]) -> Path:
    """Append missing entries to settings.local.json. Additive and idempotent."""
    p = engine_root / ".claude" / "settings.local.json"
    data = json.loads(p.read_text(encoding="utf8")) if p.exists() else {}
    perms = data.setdefault("permissions", {})
    deny = perms.setdefault("deny", [])
    for e in entries:
        if e not in deny:
            deny.append(e)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf8")
    return p


def main(argv) -> int:
    argv = list(argv)
    do_write = "--write" in argv
    as_json = "--json" in argv
    if [a for a in argv if a not in ("--write", "--json")]:
        print("usage: tos-deny [--write] [--json]", file=sys.stderr)
        return 2

    cfg = pc.load_config()
    exp = expected(cfg, write_vocabulary())
    have = present(pc.ENGINE_ROOT)
    missing = {c: [e for e in entries if e not in have] for c, entries in exp.items()}
    missing = {c: e for c, e in missing.items() if e}

    if do_write and missing:
        target = add_to_local(pc.ENGINE_ROOT, [e for entries in missing.values() for e in entries])
        have = present(pc.ENGINE_ROOT)
        missing = {}

    if as_json:
        print(json.dumps({"expected": exp, "missing": missing}, indent=2))
        return 1 if missing else 0

    for conn, names in sorted(servers(cfg).items()):
        covered = [e for e in exp[conn] if e in have]
        print(f"{conn:12} {', '.join(names):32} {len(covered)}/{len(exp[conn])} write tools denied")
    if not any(exp.values()):
        print("\nno connector in the config names an MCP server; nothing to deny")
    if missing:
        total = sum(len(v) for v in missing.values())
        print(f"\n{total} entries missing. Re-run with --write to add them to .claude/settings.local.json:")
        for entries in [e for _, e in sorted(missing.items())]:
            for e in entries:
                print(f"  {e}")
        return 1
    if do_write:
        print(f"\nwrote the missing entries to {target}")
    print("\nevery write tool the config implies is denied")
    print("NOTE: this proves the names in your config are covered, not that they are the names your")
    print("      servers use. Confirm against `claude mcp list` and the tools each server exposes.")
    return 0


def cli() -> None:
    raise SystemExit(main(sys.argv[1:]))
