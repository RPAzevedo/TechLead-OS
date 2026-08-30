"""Everything the engine ships must parse clean.

The example pages carry {{PLACEHOLDER}} tokens that /tos-init substitutes on the way
in, so they are checked the way they are actually written to the data root.
"""
import datetime as dt

import pytest

from tos.common import ENGINE_ROOT, FM_RE, load_yaml, split_frontmatter
from tos.init import fill_placeholders

PAGES = sorted((ENGINE_ROOT / "schema").rglob("*.md"))


def test_pages_were_found():
    assert PAGES, f"no shipped pages under {ENGINE_ROOT / 'schema'}"


@pytest.mark.parametrize("path", PAGES, ids=lambda p: str(p.relative_to(ENGINE_ROOT)))
def test_shipped_page_frontmatter_parses(path):
    text = fill_placeholders(path.read_text(encoding="utf8"), dt.datetime.now(dt.timezone.utc))
    if not FM_RE.match(text):
        return  # index.md and the pinned header carry none
    _fm, _body, err = split_frontmatter(text)
    assert err is None, f"{path}: {err}"


def test_example_config_parses():
    cfg = load_yaml((ENGINE_ROOT / "config.example.yaml").read_text(encoding="utf8"))
    assert cfg["data"]["root"]
    assert cfg["rollout"]["phase"] == 1
