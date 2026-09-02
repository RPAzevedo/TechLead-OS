"""tos-lint --fix repairs only the mechanical findings, idempotently."""
from tos import lint as tos_lint
from tos import new_page


def unindex(root, d, name):
    idx = root / "wiki" / d / "index.md"
    idx.write_text("\n".join(ln for ln in idx.read_text(encoding="utf8").splitlines()
                             if f"]({name})" not in ln) + "\n", encoding="utf8")


def test_unindexed_page_is_listed_again(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--description", "A widget."]) == 0
    unindex(bare, "concepts", "widget.md")
    tos_lint.main(["--fix"])
    out = capsys.readouterr().out
    assert "## fixed" in out and "added in" in out
    assert "* [Widget](widget.md) - A widget." in (bare / "wiki" / "concepts" / "index.md").read_text(encoding="utf8")


def test_moved_and_leading_slash_links_are_repaired(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget"]) == 0
    q = bare / "wiki" / "questions" / "why.md"
    q.write_text((bare / "wiki" / "concepts" / "widget.md").read_text(encoding="utf8")
                 .replace("type: Concept", "type: Question")
                 + "\nSee [moved](widget.md) and [slash](/concepts/widget.md).\n", encoding="utf8")
    tos_lint.main(["--fix"])
    capsys.readouterr()
    text = q.read_text(encoding="utf8")
    assert "[moved](../concepts/widget.md)" in text
    assert "[slash](../concepts/widget.md)" in text


def test_ambiguous_basename_is_reported_not_guessed(bare, capsys):
    assert new_page.main(["Concept", "twin", "--title", "Twin"]) == 0
    assert new_page.main(["Synthesis", "twin", "--title", "Twin"]) == 0
    q = bare / "wiki" / "questions" / "why.md"
    q.write_text("---\ntype: Question\ntitle: Why\ndescription: d\ntags: []\n"
                 "generated: { by: claude-code/t, at: 2026-01-01T09:00:00+10:00 }\n"
                 "status: draft\nstale_after: 2099-01-01\n---\n\n# Question\n\nSee [twin](twin.md).\n",
                 encoding="utf8")
    tos_lint.main(["--fix"])
    out = capsys.readouterr().out
    assert "[twin](twin.md)" in q.read_text(encoding="utf8")  # untouched
    assert "`questions/why.md` → `twin.md` is broken" in out  # still reported


def test_dead_index_line_is_removed(bare, capsys):
    idx = bare / "wiki" / "concepts" / "index.md"
    idx.write_text(idx.read_text(encoding="utf8") + "* [Ghost](ghost.md) - long gone\n", encoding="utf8")
    tos_lint.main(["--fix"])
    out = capsys.readouterr().out
    assert "dead line for `ghost.md` removed" in out
    assert "ghost.md" not in idx.read_text(encoding="utf8")


def test_second_run_fixes_nothing(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget"]) == 0
    unindex(bare, "concepts", "widget.md")
    tos_lint.main(["--fix"])
    capsys.readouterr()
    tos_lint.main(["--fix"])
    assert "## fixed" not in capsys.readouterr().out


def test_a_leading_slash_link_out_of_the_bundle_is_not_repaired(bare, capsys):
    """`/../outside.md` resolves out of wiki/; rewriting it would point a page at a
    file that is not part of the bundle at all."""
    outside = bare / "outside.md"
    outside.write_text("secret\n", encoding="utf8")
    q = bare / "wiki" / "questions" / "why.md"
    q.write_text("---\ntype: Question\ntitle: Why\ndescription: d\ntags: []\n"
                 "generated: { by: claude-code/t, at: 2026-01-01T09:00:00+10:00 }\n"
                 "status: draft\nstale_after: 2099-01-01\n---\n\n# Question\n\n"
                 "See [escape](/../outside.md).\n", encoding="utf8")
    tos_lint.main(["--fix"])
    out = capsys.readouterr().out
    assert "[escape](/../outside.md)" in q.read_text(encoding="utf8")  # untouched
    assert "outside.md` → " not in out                                  # never rewritten
    assert "uses a leading slash" in out                                # still reported


def test_an_unparseable_index_line_is_refreshed_once(bare, capsys):
    """A pre-0.8.0 line whose label swallowed a `]` is replaced, not duplicated —
    and --fix must not keep claiming it every run."""
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--description", "d"]) == 0
    idx = bare / "wiki" / "concepts" / "index.md"
    idx.write_text(idx.read_text(encoding="utf8").replace("* [Widget](widget.md) - d",
                                                          "* [[legacy]](widget.md) - d"), encoding="utf8")
    tos_lint.main(["--fix"])
    assert "refreshed in" in capsys.readouterr().out
    text = idx.read_text(encoding="utf8")
    assert text.count("](widget.md)") == 1
    assert "[[legacy]]" not in text
    tos_lint.main(["--fix"])
    assert "## fixed" not in capsys.readouterr().out


def test_frontmatter_and_code_examples_are_never_rewritten(bare, capsys):
    """--fix repairs links a reader would follow. A markdown-shaped frontmatter value is
    metadata, and a link inside a fenced or inline code span is an example of the format."""
    assert new_page.main(["Concept", "widget", "--title", "Widget"]) == 0
    q = bare / "wiki" / "questions" / "why.md"
    q.write_text('---\ntype: Question\ntitle: Why\ndescription: "the shape is [label](widget.md)"\ntags: []\n'
                 "generated: { by: claude-code/t, at: 2026-01-01T09:00:00+10:00 }\n"
                 "status: draft\nstale_after: 2099-01-01\n---\n\n# Question\n\n"
                 "An index line looks like:\n\n```markdown\n* [Widget](widget.md) - a line\n```\n\n"
                 "or inline, `[Widget](widget.md)`.\n\nThe real one: [Widget](widget.md).\n", encoding="utf8")
    tos_lint.main(["--fix"])
    capsys.readouterr()
    text = q.read_text(encoding="utf8")
    assert 'description: "the shape is [label](widget.md)"' in text
    assert "* [Widget](widget.md) - a line" in text
    assert "or inline, `[Widget](widget.md)`." in text
    assert "The real one: [Widget](../concepts/widget.md)." in text
    tos_lint.main([])
    out = capsys.readouterr().out
    assert "is broken" not in out  # nor are the examples reported, or --fix could never clear them
