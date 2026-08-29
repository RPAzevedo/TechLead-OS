#!/usr/bin/env python3
"""Shared helpers for the TechLead OS engine scripts.

- config loading (PyYAML if present, otherwise a small YAML-subset parser)
- frontmatter parsing for OKF pages
- date helpers

Deliberately stdlib-only so the scripts run on a fresh machine.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import sys
from pathlib import Path

ENGINE_VERSION = "0.5.1"
ENGINE_ROOT = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------------- YAML subset
try:  # pragma: no cover
    import yaml as _yaml  # type: ignore
except Exception:  # pragma: no cover
    _yaml = None


def _strip_comment(line: str) -> str:
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _scalar(tok: str):
    t = tok.strip()
    if t == "" or t in ("~", "null", "Null", "NULL"):
        return None
    if t in ("true", "True", "TRUE"):
        return True
    if t in ("false", "False", "FALSE"):
        return False
    if (t[0] == t[-1]) and t[0] in ("'", '"') and len(t) >= 2:
        return t[1:-1]
    if t.startswith("[") and t.endswith("]"):
        inner = t[1:-1].strip()
        return [_scalar(x) for x in _split_flow(inner)] if inner else []
    if t.startswith("{") and t.endswith("}"):
        inner = t[1:-1].strip()
        d = {}
        for part in _split_flow(inner):
            if ":" in part:
                k, v = part.split(":", 1)
                d[k.strip()] = _scalar(v)
        return d
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    if re.fullmatch(r"-?\d+\.\d+", t):
        return float(t)
    return t


def _split_flow(s: str):
    parts, depth, quote, cur = [], 0, None, []
    for ch in s:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            cur.append(ch)
        elif ch in "[{":
            depth += 1
            cur.append(ch)
        elif ch in "]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return [p.strip() for p in parts]


def _mini_yaml(text: str):
    lines = []
    for raw in text.splitlines():
        s = _strip_comment(raw)
        if s.strip() == "":
            continue
        indent = len(s) - len(s.lstrip(" "))
        lines.append((indent, s.strip()))

    def parse_block(i: int, indent: int):
        if i >= len(lines):
            return None, i
        if lines[i][1].startswith("- "):
            return parse_seq(i, indent)
        return parse_map(i, indent)

    def parse_seq(i: int, indent: int):
        items = []
        while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
            content = lines[i][1][2:].strip()
            if content == "":
                val, i = parse_block(i + 1, lines[i + 1][0] if i + 1 < len(lines) else indent + 2)
                items.append(val)
                continue
            if ":" in content and not content.startswith(("{", "[", "'", '"')):
                # mapping item; first key on the dash line, rest deeper
                k, v = content.split(":", 1)
                item = {}
                if v.strip() == "":
                    sub, i2 = parse_block(i + 1, lines[i + 1][0]) if i + 1 < len(lines) and lines[i + 1][0] > indent else (None, i + 1)
                    item[k.strip()] = sub
                    i = i2
                else:
                    item[k.strip()] = _scalar(v)
                    i += 1
                child_indent = indent + 2
                while i < len(lines) and lines[i][0] > indent and not lines[i][1].startswith("- "):
                    ci = lines[i][0]
                    k2, v2 = lines[i][1].split(":", 1)
                    if v2.strip() == "":
                        sub, i = parse_block(i + 1, lines[i + 1][0]) if i + 1 < len(lines) and lines[i + 1][0] > ci else (None, i + 1)
                        item[k2.strip()] = sub
                    else:
                        item[k2.strip()] = _scalar(v2)
                        i += 1
                items.append(item)
            else:
                items.append(_scalar(content))
                i += 1
        return items, i

    def parse_map(i: int, indent: int):
        d = {}
        while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
            line = lines[i][1]
            if ":" not in line:
                i += 1
                continue
            k, v = line.split(":", 1)
            k = k.strip()
            if v.strip() == "":
                if i + 1 < len(lines) and (lines[i + 1][0] > indent or (lines[i + 1][0] == indent and lines[i + 1][1].startswith("- "))):
                    sub, i = parse_block(i + 1, lines[i + 1][0])
                    d[k] = sub
                else:
                    d[k] = None
                    i += 1
            else:
                d[k] = _scalar(v)
                i += 1
        return d, i

    if not lines:
        return {}
    val, _ = parse_block(0, lines[0][0])
    return val


def load_yaml(text: str):
    if _yaml is not None:
        try:
            return _yaml.safe_load(text) or {}
        except Exception:
            pass
    return _mini_yaml(text) or {}


# ----------------------------------------------------------------------------- config
def config_path() -> Path:
    env = os.environ.get("TOS_CONFIG")
    return Path(env).expanduser() if env else Path("~/.config/tos/config.yaml").expanduser()


def load_config(path: Path | None = None) -> dict:
    p = path or config_path()
    if not p.exists():
        sys.exit(f"config not found: {p}\n  copy {ENGINE_ROOT / 'config.example.yaml'} there, or set $TOS_CONFIG")
    cfg = load_yaml(p.read_text(encoding="utf8"))
    if not isinstance(cfg, dict) or "data" not in cfg or not (cfg.get("data") or {}).get("root"):
        sys.exit(f"config at {p} has no data.root")
    cfg["_path"] = str(p)
    return cfg


def data_root(cfg: dict) -> Path:
    return Path(str(cfg["data"]["root"])).expanduser().resolve()


def review_setting(cfg: dict, key: str, default):
    return (cfg.get("review") or {}).get(key, default)


# ----------------------------------------------------------------------------- frontmatter
FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.S)


def split_frontmatter(text: str):
    """Return (frontmatter dict or None, body). None when there is no frontmatter block."""
    m = FM_RE.match(text)
    if not m:
        return None, text
    try:
        fm = load_yaml(m.group(1))
    except Exception:
        return {}, text[m.end():]
    return (fm if isinstance(fm, dict) else {}), text[m.end():]


def read_page(path: Path):
    text = path.read_text(encoding="utf8", errors="replace")
    fm, body = split_frontmatter(text)
    return fm, body, text


# ----------------------------------------------------------------------------- dates
def today() -> dt.date:
    return dt.date.today()


def parse_date(v) -> dt.date | None:
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = str(v).strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def parse_datetime(v) -> dt.datetime | None:
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v if v.tzinfo else v.replace(tzinfo=dt.timezone.utc)
    if isinstance(v, dt.date):
        return dt.datetime(v.year, v.month, v.day, tzinfo=dt.timezone.utc)
    s = str(v).strip()
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        d = parse_date(s)
        return dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc) if d else None


def verified_entries(fm: dict) -> list:
    v = fm.get("verified")
    if v is None:
        return []
    if isinstance(v, dict):
        return [v]
    if isinstance(v, list):
        return [x for x in v if isinstance(x, dict)]
    return []


def trust_tier(fm: dict) -> str:
    entries = verified_entries(fm)
    if not entries:
        return "unverified"
    gen = parse_datetime((fm.get("generated") or {}).get("at")) if isinstance(fm.get("generated"), dict) else None
    latest = max((parse_datetime(e.get("at")) for e in entries if parse_datetime(e.get("at"))), default=None)
    if gen and latest and gen > latest:
        return "changed-since-verified"
    if any(str(e.get("by", "")).startswith("human:") for e in entries):
        return "human-reviewed"
    return "machine-confirmed"


if __name__ == "__main__":
    if "--show" in sys.argv:
        cfg = load_config()
        print(f"config:   {cfg['_path']}")
        print(f"engine:   {ENGINE_VERSION} (config says {cfg.get('engine')})")
        print(f"data:     {data_root(cfg)}  exists={data_root(cfg).exists()}")
        print(f"actor:    {(cfg.get('data') or {}).get('actor')}")
        print(f"phase:    {(cfg.get('rollout') or {}).get('phase', 1)}")
        print(f"yaml:     {'PyYAML' if _yaml else 'built-in subset parser'}")
    else:
        print("usage: tos_common.py --show")
