"""tos-new creates registry-conformant pages from the templates."""
import datetime as dt
from zoneinfo import ZoneInfo

from conftest import config_today

from tos import common as pc
from tos import lint as tos_lint
from tos import new_page


def test_creates_every_p1_type_and_the_bundle_still_lints(bare, capsys):
    registry = pc.load_registry()
    p1 = [t for t, e in registry.items() if e["phase"] == "P1"]
    assert len(p1) == 11
    for i, t in enumerate(p1):
        slug = f"2026-q3-page-{i}" if t == "Objective" else f"page-{i}"
        assert new_page.main([t, slug, "--title", f"Page {i}", "--description", "A test page."]) == 0
    capsys.readouterr()
    assert tos_lint.main([]) == 0


def test_frontmatter_is_computed_from_the_registry(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--by", "claude-code/test-model"]) == 0
    fm, _, _, err = pc.read_page(bare / "wiki" / "concepts" / "widget.md")
    assert err is None
    assert fm["status"] == "draft"
    assert fm["generated"]["by"] == "claude-code/test-model"
    assert pc.parse_date(fm["stale_after"]) == config_today() + dt.timedelta(days=365)
    assert "verified" not in fm


def test_source_gets_a_date_prefix_and_a_null_stale_after(bare, capsys):
    assert new_page.main(["Source", "meeting-notes", "--title", "Meeting notes"]) == 0
    path = bare / "wiki" / "sources" / f"{config_today().isoformat()}-meeting-notes.md"
    fm, _, _, _ = pc.read_page(path)
    assert fm["stale_after"] is None  # a record: never expires
    assert "# verified: never set by /tos-ingest" in path.read_text(encoding="utf8")


def test_a_new_project_or_initiative_carries_no_pointer_keys(bare, capsys):
    """The pointer keys ship commented out, so a fresh page carries none of them and lints clean.

    A live `slack: "#channel"` in the template would survive tos-new, which fills only title,
    description, generated and stale_after, and every new page would open with a finding.
    """
    for t, d in (("Project", "delivery/projects"), ("Initiative", "delivery/initiatives")):
        assert new_page.main([t, "thing", "--title", "Thing", "--description", "One sentence."]) == 0
        path = bare / "wiki" / d.split("/")[0] / d.split("/")[1] / "thing.md"
        fm, _, _, err = pc.read_page(path)
        assert err is None
        for key in ("slack", "jira", "confluence", "rfc", "next_checkpoint"):
            assert key not in fm, f"{t} carries a placeholder `{key}`"
        assert '# slack: "#channel"' in path.read_text(encoding="utf8")
    capsys.readouterr()
    assert tos_lint.main([]) == 0


def test_page_is_listed_in_its_index(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--description", "One sentence."]) == 0
    idx = (bare / "wiki" / "concepts" / "index.md").read_text(encoding="utf8")
    assert "* [Widget](widget.md) - One sentence." in idx


def test_never_overwrites(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget"]) == 0
    assert new_page.main(["Concept", "widget", "--title", "Widget again"]) == 1


def test_later_phase_type_is_refused_at_phase_1(bare, capsys):
    assert new_page.main(["Attested Computation", "cycle-time", "--title", "Cycle time",
                          "--dir", "delivery/metrics/"]) == 1
    err = capsys.readouterr().err
    assert "phase-2" in err
    assert not (bare / "wiki" / "delivery" / "metrics" / "cycle-time.md").exists()


def test_unknown_type_and_bad_slug_are_usage_errors(bare, capsys):
    assert new_page.main(["Widget", "x", "--title", "X"]) == 2
    assert new_page.main(["Concept", "Not_A_Slug", "--title", "X"]) == 2


def test_opt_in_log_line(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget",
                          "--log", "Ingest: created [Widget](concepts/widget.md)"]) == 0
    log = (bare / "wiki" / "log.md").read_text(encoding="utf8")
    assert "* **Ingest**: created [Widget](concepts/widget.md)" in log


def test_dry_run_writes_nothing(bare, capsys):
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--dry-run"]) == 0
    assert not (bare / "wiki" / "concepts" / "widget.md").exists()
    assert "widget.md" not in (bare / "wiki" / "concepts" / "index.md").read_text(encoding="utf8")


def test_implicitly_typed_titles_stay_strings(bare, capsys):
    """`true`, `null` and a bare date are YAML scalars: unquoted they load as a
    bool, None and a date, so the page would carry a type nobody asked for."""
    for i, value in enumerate(["true", "null", "2026-09-01", "no", "1.0"]):
        assert new_page.main(["Concept", f"typed-{i}", "--title", value, "--description", value]) == 0
        fm, _, _, err = pc.read_page(bare / "wiki" / "concepts" / f"typed-{i}.md")
        assert err is None
        assert fm["title"] == value and isinstance(fm["title"], str)
        assert fm["description"] == value and isinstance(fm["description"], str)


def test_a_title_with_yaml_punctuation_round_trips(bare, capsys):
    for i, value in enumerate(["Ranking: how we do it", "A # hash", "[bracketed]", "yes: no"]):
        assert new_page.main(["Concept", f"punct-{i}", "--title", value]) == 0
        fm, _, _, err = pc.read_page(bare / "wiki" / "concepts" / f"punct-{i}.md")
        assert err is None
        assert fm["title"] == value


def test_a_title_with_brackets_is_indexed_readably(bare, capsys):
    """An unescaped `]` closes the link label early, and the page reads as unindexed."""
    assert new_page.main(["Concept", "bracket", "--title", "[bracketed] title",
                          "--description", "d"]) == 0
    idx = (bare / "wiki" / "concepts" / "index.md").read_text(encoding="utf8")
    assert r"* [\[bracketed\] title](bracket.md) - d" in idx
    from tos import lint as tos_lint
    assert tos_lint.LINK_RE.findall(idx.splitlines()[-1]) == [(r"\[bracketed\] title", "bracket.md")]
    capsys.readouterr()
    tos_lint.main([])
    assert "not listed in its index.md" not in capsys.readouterr().out


def test_a_missing_directory_index_is_created_before_the_page(bare, capsys):
    (bare / "wiki" / "concepts" / "index.md").unlink()
    assert new_page.main(["Concept", "widget", "--title", "Widget", "--description", "A widget."]) == 0
    out = capsys.readouterr().out
    assert out.index("created: concepts/index.md") < out.index("created: concepts/widget.md")
    text = (bare / "wiki" / "concepts" / "index.md").read_text(encoding="utf8")
    assert text.startswith("# Concepts\n") and "* [Widget](widget.md) - A widget." in text


def test_timestamps_come_from_the_configured_timezone(bare, capsys, utc_host):
    """A UTC runner with an Australia/Melbourne config still writes Melbourne offsets: the
    page contract is written in the human's zone, and `stale_after` counts from its day."""
    assert new_page.main(["Concept", "widget", "--title", "Widget"]) == 0
    fm, _, _, _ = pc.read_page(bare / "wiki" / "concepts" / "widget.md")
    at = pc.parse_datetime(fm["generated"]["at"])
    assert at.utcoffset() == ZoneInfo("Australia/Melbourne").utcoffset(at)
    assert pc.parse_date(fm["stale_after"]) == at.date() + dt.timedelta(days=365)


def test_the_horizon_counts_from_the_configured_calendar_day(bare, capsys, utc_host, monkeypatch):
    """15:30 UTC is already the next day in Melbourne — the day the page has to expire from."""
    fixed = dt.datetime(2026, 9, 2, 15, 30, tzinfo=dt.timezone.utc)

    class Clock(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.astimezone(tz)

    monkeypatch.setattr(pc.dt, "datetime", Clock)
    assert new_page.main(["Concept", "widget", "--title", "Widget"]) == 0
    monkeypatch.undo()
    fm, _, _, _ = pc.read_page(bare / "wiki" / "concepts" / "widget.md")
    assert pc.parse_datetime(fm["generated"]["at"]) == fixed
    assert pc.parse_date(fm["generated"]["at"]) == dt.date(2026, 9, 3)  # the Melbourne day, not the UTC one
    assert pc.parse_date(fm["stale_after"]) == dt.date(2027, 9, 3)
