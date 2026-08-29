"""Malformed YAML must never pass silently.

Regression test for the P1: load_yaml() used to fall back to a permissive
subset parser on any PyYAML error, and that parser dropped lines it could not
understand, so a deliberately invalid page passed lint with exit code 0. The
fallback parser is gone — PyYAML is a required dependency — and its rejections
must surface as explicit errors, never as a partial document.
"""
import pytest

from tos.common import YamlError, load_yaml, read_page, split_frontmatter

VALID = """---
type: Concept
title: Context engineering
description: One sentence.
tags: [llm, agents]
sources:
  - id: some-source
    resource: https://example.com/a
    title: Human label
generated: { by: claude-code/test, at: 2026-08-29T09:14:00+10:00 }
status: draft
stale_after: 2027-08-29
---

# Definition
"""

MALFORMED = {
    # the reproduction from the finding: unclosed flow sequence, a junk line,
    # and a sources block that used to vanish without a word
    "reported": (
        "type: Concept\ntitle: Broken\ntags: [a, b\ndescription: a sentence\n"
        "   randomly indented junk\nsources:\n  - id: x\n"
    ),
    "unclosed_flow": "type: Concept\ntags: [a, b\n",
    "unterminated_quote": "type: Concept\ntitle: 'oops\n",
    # PyYAML raises a bare ValueError here, not a YAMLError; lint must not crash
    "impossible_date": "type: Concept\nstale_after: 2026-13-45\n",
}


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_malformed_frontmatter_is_reported(name):
    fm, body, err = split_frontmatter(f"---\n{MALFORMED[name]}---\n\n# Body\n")
    assert err, f"{name} parsed silently: {fm!r}"
    assert fm == {}
    assert body.strip() == "# Body", "the body is still returned so link checks can run"


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_malformed_yaml_raises(name):
    with pytest.raises(YamlError):
        load_yaml(MALFORMED[name])


def test_valid_frontmatter_parses():
    fm, body, err = split_frontmatter(VALID)
    assert err is None
    assert fm["type"] == "Concept"
    assert fm["tags"] == ["llm", "agents"]
    assert fm["sources"][0]["resource"] == "https://example.com/a"
    assert fm["generated"]["by"] == "claude-code/test"
    assert body.strip() == "# Definition"


def test_unclosed_fence_is_an_error():
    """An opened `---` with no closing fence is malformed, not "this page has none"."""
    fm, _body, err = split_frontmatter("---\ntype: Concept\ntitle: X\n\n# Body\n")
    assert err and "never closed" in err
    assert fm == {}


def test_no_frontmatter_is_not_an_error():
    fm, body, err = split_frontmatter("# Just a heading\n")
    assert (fm, body, err) == (None, "# Just a heading\n", None)


def test_empty_frontmatter_is_not_an_error():
    fm, _body, err = split_frontmatter("---\n\n---\n\n# Body\n")
    assert err is None
    assert fm == {}


def test_non_mapping_frontmatter_is_an_error():
    """`- one\\n- two` is valid YAML, but OKF frontmatter must be a mapping."""
    fm, body, err = split_frontmatter("---\n- one\n- two\n---\n\n# Body\n")
    assert err and "not a mapping" in err
    assert fm == {}
    assert body.strip() == "# Body"


def test_read_page_reports_the_error(tmp_path):
    page = tmp_path / "broken.md"
    page.write_text(f"---\n{MALFORMED['reported']}---\n\n# Body\n", encoding="utf8")
    _fm, _body, text, err = read_page(page)
    assert err
    assert text.startswith("---\n")
