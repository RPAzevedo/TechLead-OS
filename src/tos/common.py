"""Shared helpers for the TechLead OS engine.

- config loading
- frontmatter parsing for OKF pages (PyYAML)
- date helpers

Malformed YAML is never silently tolerated: `load_yaml()` raises `YamlError`,
and `split_frontmatter()` / `read_page()` hand that message back as an explicit
error so `/lint` can report it as the OKF conformance failure it is.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import yaml

try:
    ENGINE_VERSION = version("techlead-os")
except PackageNotFoundError:  # running from a checkout with no install
    ENGINE_VERSION = "0.5.3"


def _find_engine_root() -> Path:
    """Where `schema/` and `config.example.yaml` live: the checkout root, found
    by walking up from this file. They sit beside `src/`, not inside the
    package, because they are human-edited (CLAUDE.md §1). `$TOS_ENGINE_ROOT`
    overrides the search.
    """
    env = os.environ.get("TOS_ENGINE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve()
    for cand in here.parents:
        if (cand / "schema" / "types.md").exists():
            return cand
    return here.parents[2]  # src/tos/common.py -> the checkout root


ENGINE_ROOT = _find_engine_root()


def engine_path(*parts: str) -> Path:
    """A path inside the engine checkout, with a clear error when it is missing."""
    p = ENGINE_ROOT.joinpath(*parts)
    if not p.exists():
        sys.exit(
            f"engine file not found: {p}\n"
            "  run tos from the engine checkout (uv run tos-…), or set $TOS_ENGINE_ROOT to it"
        )
    return p


# ----------------------------------------------------------------------------- YAML
class YamlError(ValueError):
    """Raised when the input is not YAML we can trust."""


def load_yaml(text: str):
    """Parse YAML. Raises YamlError on anything malformed — never a partial document."""
    try:
        return yaml.safe_load(text)
    except (yaml.YAMLError, ValueError) as e:
        # PyYAML raises a bare ValueError for an impossible timestamp
        raise YamlError(str(e).replace("\n", " ").strip()) from e


# ----------------------------------------------------------------------------- config
def config_path() -> Path:
    env = os.environ.get("TOS_CONFIG")
    return Path(env).expanduser() if env else Path("~/.config/tos/config.yaml").expanduser()


def load_config(path: Path | None = None) -> dict:
    p = path or config_path()
    if not p.exists():
        sys.exit(
            f"config not found: {p}\n"
            f"  copy {ENGINE_ROOT / 'config.example.yaml'} there, or set $TOS_CONFIG"
        )
    try:
        cfg = load_yaml(p.read_text(encoding="utf8"))
    except YamlError as e:
        sys.exit(f"config at {p} is not valid YAML: {e}")
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
FM_OPEN_RE = re.compile(r"\A---[ \t]*\r?\n")


def split_frontmatter(text: str):
    """Return (frontmatter, body, error).

    Three outcomes, deliberately distinct:
      * no frontmatter block at all -> (None, text, None)
      * a block that will not parse  -> ({}, body, "line N: …")
      * a block that parses          -> (dict, body, None)

    A block that parses to something other than a mapping is an error too: OKF
    frontmatter is a mapping. The body is always returned so a caller can keep
    checking links and indexes on a page whose frontmatter is broken.
    """
    m = FM_RE.match(text)
    if not m:
        if FM_OPEN_RE.match(text):
            return {}, text, "the frontmatter fence `---` is opened but never closed"
        return None, text, None
    body = text[m.end():]
    try:
        fm = load_yaml(m.group(1))
    except YamlError as e:
        return {}, body, str(e)
    if fm is None:
        return {}, body, None
    if not isinstance(fm, dict):
        return {}, body, f"frontmatter is a {type(fm).__name__}, not a mapping"
    return fm, body, None


def read_page(path: Path):
    """Return (frontmatter, body, text, error) — see split_frontmatter."""
    text = path.read_text(encoding="utf8", errors="replace")
    fm, body, err = split_frontmatter(text)
    return fm, body, text, err


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


# ----------------------------------------------------------------------------- cli
def main(argv) -> int:
    if argv and argv[0] not in ("--show",):
        print("usage: tos-config [--show]", file=sys.stderr)
        return 2
    cfg = load_config()
    print(f"config:   {cfg['_path']}")
    print(f"engine:   {ENGINE_VERSION} (config says {cfg.get('engine')})")
    print(f"engine root: {ENGINE_ROOT}")
    print(f"data:     {data_root(cfg)}  exists={data_root(cfg).exists()}")
    print(f"actor:    {(cfg.get('data') or {}).get('actor')}")
    print(f"phase:    {(cfg.get('rollout') or {}).get('phase', 1)}")
    return 0


def cli() -> None:
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
