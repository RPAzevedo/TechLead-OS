"""tos-index adds or refreshes a page's line in its directory index."""
from tos import index_add, new_page


def idx_text(root, d="concepts"):
    return (root / "wiki" / d / "index.md").read_text(encoding="utf8")


def test_defaults_come_from_the_page_frontmatter(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--description", "A widget."]) == 0
    # wipe the line tos-new wrote, then restore it from the page itself
    idx = bare / "wiki" / "concepts" / "index.md"
    idx.write_text("\n".join(ln for ln in idx_text(bare).splitlines() if "widget" not in ln) + "\n", encoding="utf8")
    assert index_add.main(["concepts/widget.md"]) == 0
    assert "* [Widget](widget.md) - A widget." in idx_text(bare)


def test_refreshes_in_place_without_duplicating(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--description", "Old."]) == 0
    assert index_add.main(["concepts/widget.md", "--desc", "New description."]) == 0
    text = idx_text(bare)
    assert text.count("](widget.md)") == 1
    assert "New description." in text and "Old." not in text


def test_deprecated_moves_the_line_under_its_own_heading(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--description", "A widget."]) == 0
    assert index_add.main(["concepts/widget.md", "--deprecated"]) == 0
    text = idx_text(bare)
    assert text.count("](widget.md)") == 1
    assert text.index("## Deprecated") < text.index("](widget.md)")


def test_missing_page_is_refused(bare, capsys):
    assert index_add.main(["concepts/nothing.md"]) == 1
    assert "does not exist" in capsys.readouterr().err


def test_a_path_outside_the_bundle_is_refused(bare, capsys):
    outside = bare / "outside.md"
    outside.write_text("---\ntype: Concept\ntitle: Outside\ndescription: d\ntags: []\n"
                       "generated: { by: claude-code/t, at: 2026-01-01T09:00:00+10:00 }\n"
                       "status: draft\nstale_after: 2099-01-01\n---\n\n# Definition\n", encoding="utf8")
    for arg in ("../outside.md", str(outside)):
        assert index_add.main([arg]) == 2
        assert "outside the bundle" in capsys.readouterr().err


def test_refreshing_keeps_the_entrys_position(bare, capsys):
    """`delivery/projects/index.md` is priority-ordered, and /tos-ingest re-indexes a project
    it touched: a refresh that moved the line to the tail would silently re-rank the portfolio."""
    for slug in ("first", "second", "third"):
        assert new_page.main(["Concept", slug, "--title", slug.capitalize(), "--description", "d"]) == 0
    assert index_add.main(["concepts/second.md", "--desc", "New."]) == 0
    entries = [ln for ln in idx_text(bare).splitlines() if ln.startswith("* [")]
    assert entries == ["* [First](first.md) - d",
                       "* [Second](second.md) - New.",
                       "* [Third](third.md) - d"]


def test_a_mention_in_another_entry_is_not_that_pages_line(bare, capsys):
    """A link inside another entry's description names a page; it does not list it."""
    for slug in ("widget", "gadget"):
        assert new_page.main(["Concept", slug, "--title", slug.capitalize(), "--description", "d"]) == 0
    idx = bare / "wiki" / "concepts" / "index.md"
    idx.write_text(idx_text(bare).replace("* [Gadget](gadget.md) - d",
                                          "* [Gadget](gadget.md) - like [Widget](widget.md), but smaller"),
                   encoding="utf8")
    assert index_add.main(["concepts/widget.md", "--deprecated"]) == 0
    text = idx_text(bare)
    assert "* [Gadget](gadget.md) - like [Widget](widget.md), but smaller" in text
    assert text.count("](widget.md)") == 2  # the mention, and the moved entry
    assert text.index("## Deprecated") < text.rindex("](widget.md)")


def test_a_missing_index_is_written_in_full(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--description", "A widget."]) == 0
    (bare / "wiki" / "concepts" / "index.md").unlink()
    assert index_add.main(["concepts/widget.md"]) == 0
    assert "created: concepts/index.md" in capsys.readouterr().out
    text = idx_text(bare)
    # the canonical body, not a stub starting at `## Pages`: /tos-init only ever creates an
    # index that is missing, so a stub would keep its missing heading for good
    assert text.startswith("# Concepts\n")
    assert "ideas, techniques, standards, terms" in text
    assert "* [Widget](widget.md) - A widget." in text
