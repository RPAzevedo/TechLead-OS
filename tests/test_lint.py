"""End-to-end: a page whose frontmatter will not parse is a conformance error."""
import pytest

from tos import init as tos_init
from tos import lint as tos_lint

BROKEN = """---
type: Concept
title: Broken
tags: [a, b
description: a sentence
   randomly indented junk
sources:
  - id: x
---

# Definition

Nothing here.
"""


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    """A real data root built by tos-init, with the config it was built from."""
    root = tmp_path / "data"
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f'engine: "0.5"\ndata:\n  root: {root}\n  timezone: Australia/Melbourne\n'
        f"  actor: human:test\nrollout:\n  phase: 1\n",
        encoding="utf8",
    )
    monkeypatch.setenv("TOS_CONFIG", str(cfg))
    assert tos_init.main(["--with-examples"]) == 0
    return root


def test_clean_bundle_has_no_conformance_error(bundle, capsys):
    code = tos_lint.main([])
    capsys.readouterr()
    assert code == 0


def test_malformed_page_fails_lint(bundle, capsys):
    page = bundle / "wiki" / "concepts" / "broken.md"
    page.write_text(BROKEN, encoding="utf8")
    idx = bundle / "wiki" / "concepts" / "index.md"
    idx.write_text(idx.read_text(encoding="utf8") + "* [Broken](broken.md) - a broken page\n", encoding="utf8")

    code = tos_lint.main([])
    out = capsys.readouterr().out

    assert code == 1, "lint passed a page with unparseable frontmatter"
    assert "## conformance" in out
    assert "concepts/broken.md" in out
    assert "not valid YAML" in out


def test_unclosed_fence_in_a_subdirectory_index_fails_lint(bundle, capsys):
    """A fence that is opened and never closed used to read as "no frontmatter" and pass."""
    idx = bundle / "wiki" / "concepts" / "index.md"
    idx.write_text("---\nokf_version: 0.2\n\n# Concepts\n", encoding="utf8")
    code = tos_lint.main([])
    out = capsys.readouterr().out
    assert code == 1
    assert "concepts/index.md` frontmatter is not valid YAML" in out
    assert "never closed" in out


def test_malformed_index_fails_lint(bundle, capsys):
    idx = bundle / "wiki" / "index.md"
    idx.write_text('---\nokf_version: "0.2"\ntags: [a, b\n---\n\n# TechLead OS\n', encoding="utf8")
    code = tos_lint.main([])
    out = capsys.readouterr().out
    assert code == 1
    assert "index.md` frontmatter is not valid YAML" in out
