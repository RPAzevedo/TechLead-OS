"""tos-verify-mark: actor rules, gates, and text-level frontmatter safety."""
from zoneinfo import ZoneInfo

from conftest import config_today

from tos import common as pc
from tos import new_page, verify_mark


def make(bare, t="Concept", slug="widget", title="Widget"):
    assert new_page.main([t, slug, "--title", title]) == 0


def page_path(bare, rel):
    return bare / "wiki" / rel


def test_process_actor_gives_machine_confirmed(bare, capsys):
    make(bare)
    assert verify_mark.main(["concepts/widget.md", "--by", "process:cross-check"]) == 0
    fm, _, _, err = pc.read_page(page_path(bare, "concepts/widget.md"))
    assert err is None
    assert pc.trust_tier(fm) == "machine-confirmed"
    assert fm["status"] == "draft"  # no --promote


def test_template_comment_and_key_order_survive(bare, capsys):
    make(bare)
    assert verify_mark.main(["concepts/widget.md", "--by", "process:cross-check"]) == 0
    text = page_path(bare, "concepts/widget.md").read_text(encoding="utf8")
    assert "# verified: never set by /tos-ingest" in text
    assert text.index("generated:") < text.index("\nverified:") < text.index("status:")


def test_human_actor_needs_the_confirmation_flag(bare, capsys):
    make(bare)
    assert verify_mark.main(["concepts/widget.md", "--by", "human:test"]) == 1
    assert "--human-confirmed" in capsys.readouterr().err
    assert verify_mark.main(["concepts/widget.md", "--by", "human:someone-else", "--human-confirmed"]) == 1
    fm, _, _, _ = pc.read_page(page_path(bare, "concepts/widget.md"))
    assert pc.verified_entries(fm) == []


def test_the_agent_never_verifies(bare, capsys):
    make(bare)
    assert verify_mark.main(["concepts/widget.md", "--by", "claude-code/some-model"]) == 1


def test_promote_obeys_the_h_gate(bare, capsys):
    make(bare)
    assert verify_mark.main(["concepts/widget.md", "--by", "process:cross-check", "--promote"]) == 0
    fm, _, _, _ = pc.read_page(page_path(bare, "concepts/widget.md"))
    assert fm["status"] == "draft"  # Concept gate is H; a process entry does not meet it
    assert verify_mark.main(["concepts/widget.md", "--by", "human:test", "--human-confirmed", "--promote"]) == 0
    fm, _, _, _ = pc.read_page(page_path(bare, "concepts/widget.md"))
    assert fm["status"] == "stable"
    assert len(pc.verified_entries(fm)) == 2


def test_promote_meets_the_m_gate_with_a_process_entry(bare, capsys):
    make(bare, t="Source", slug="a-note", title="A note")
    rel = f"sources/{config_today().isoformat()}-a-note.md"
    assert verify_mark.main([rel, "--by", "process:cross-check", "--promote"]) == 0
    fm, _, _, _ = pc.read_page(page_path(bare, rel))
    assert fm["status"] == "stable"  # Source gate is M


def test_generated_is_never_touched(bare, capsys):
    make(bare)
    before = page_path(bare, "concepts/widget.md").read_text(encoding="utf8")
    gen_line = next(ln for ln in before.splitlines() if ln.startswith("generated:"))
    assert verify_mark.main(["concepts/widget.md", "--by", "process:cross-check"]) == 0
    after = page_path(bare, "concepts/widget.md").read_text(encoding="utf8")
    assert gen_line in after.splitlines()


def test_dry_run_writes_nothing(bare, capsys):
    make(bare)
    before = page_path(bare, "concepts/widget.md").read_text(encoding="utf8")
    assert verify_mark.main(["concepts/widget.md", "--by", "process:cross-check", "--dry-run"]) == 0
    assert page_path(bare, "concepts/widget.md").read_text(encoding="utf8") == before


def test_a_path_outside_the_bundle_is_refused(bare, capsys):
    """`..` used to climb out and an absolute operand used to discard wiki/ entirely."""
    outside = bare / "outside.md"
    outside.write_text("---\ntype: Concept\ntitle: Outside\ndescription: d\ntags: []\n"
                       "generated: { by: claude-code/t, at: 2026-01-01T09:00:00+10:00 }\n"
                       "status: draft\nstale_after: 2099-01-01\n---\n\n# Definition\n", encoding="utf8")
    for arg in ("../outside.md", str(outside)):
        assert verify_mark.main([arg, "--by", "process:test"]) == 2
        assert "outside the bundle" in capsys.readouterr().err
    assert "verified" not in outside.read_text(encoding="utf8")


def test_promoting_an_rfc_makes_it_a_record(bare, capsys):
    """RFC's horizon is "30 d while draft, then —": a stable RFC that kept its
    draft expiry would be reported stale a month later."""
    make(bare, t="RFC", slug="a-proposal", title="A proposal")
    assert verify_mark.main(["design/rfcs/a-proposal.md", "--by", "human:test",
                             "--human-confirmed", "--promote"]) == 0
    fm, _, _, _ = pc.read_page(page_path(bare, "design/rfcs/a-proposal.md"))
    assert fm["status"] == "stable"
    assert fm["stale_after"] is None


def test_promoting_a_concept_keeps_its_horizon(bare, capsys):
    make(bare)
    assert verify_mark.main(["concepts/widget.md", "--by", "human:test",
                             "--human-confirmed", "--promote"]) == 0
    fm, _, _, _ = pc.read_page(page_path(bare, "concepts/widget.md"))
    assert fm["status"] == "stable"
    assert pc.parse_date(fm["stale_after"]) is not None  # only RFC becomes a record


def test_a_backdated_verification_does_not_promote(bare, capsys):
    """--at supports backdating; an entry older than `generated.at` leaves the page
    changed-since-verified, which is not a tier the gate lets through."""
    make(bare)
    assert verify_mark.main(["concepts/widget.md", "--by", "human:test", "--human-confirmed",
                             "--at", "2020-01-01T09:00:00+10:00", "--promote"]) == 0
    out = capsys.readouterr().out
    fm, _, _, _ = pc.read_page(page_path(bare, "concepts/widget.md"))
    assert fm["status"] == "draft"
    assert pc.trust_tier(fm) == "changed-since-verified"
    assert "changed-since-verified" in out and "promoted" not in out
    # and a current verification still promotes the same page
    assert verify_mark.main(["concepts/widget.md", "--by", "human:test", "--human-confirmed", "--promote"]) == 0
    fm, _, _, _ = pc.read_page(page_path(bare, "concepts/widget.md"))
    assert fm["status"] == "stable"


def test_a_backdated_process_entry_does_not_promote_an_m_gate(bare, capsys):
    make(bare, t="Source", slug="a-note", title="A note")
    rel = f"sources/{config_today().isoformat()}-a-note.md"
    assert verify_mark.main([rel, "--by", "process:cross-check",
                             "--at", "2020-01-01T09:00:00+10:00", "--promote"]) == 0
    fm, _, _, _ = pc.read_page(page_path(bare, rel))
    assert fm["status"] == "draft"


def with_verified(bare, block):
    make(bare)
    page = page_path(bare, "concepts/widget.md")
    page.write_text(page.read_text(encoding="utf8").replace("status: draft", f"{block}\nstatus: draft"),
                    encoding="utf8")
    return page


def test_the_single_mapping_form_becomes_a_list(bare, capsys):
    """OKF allows `verified: { by, at }` and docs/design.md shows it; tos-verify-mark is now the
    only way an entry is ever written, so it has to extend that page without a hand edit."""
    page = with_verified(bare, "verified: { by: process:cross-check, at: 2026-01-01T09:00:00+10:00 }")
    assert verify_mark.main(["concepts/widget.md", "--by", "human:test", "--human-confirmed"]) == 0
    fm, _, _, err = pc.read_page(page)
    assert err is None
    assert [str(e["by"]) for e in pc.verified_entries(fm)] == ["process:cross-check", "human:test"]
    assert pc.trust_tier(fm) == "human-reviewed"


def test_the_block_mapping_form_becomes_a_list(bare, capsys):
    page = with_verified(bare, "verified:\n  by: process:cross-check\n  at: 2026-01-01T09:00:00+10:00")
    assert verify_mark.main(["concepts/widget.md", "--by", "process:okf-lint"]) == 0
    fm, _, _, err = pc.read_page(page)
    assert err is None
    assert [str(e["by"]) for e in pc.verified_entries(fm)] == ["process:cross-check", "process:okf-lint"]


def test_a_flow_sequence_is_still_refused_rather_than_re_emitted(bare, capsys):
    page = with_verified(bare, "verified: [ { by: process:cross-check, at: 2026-01-01T09:00:00+10:00 } ]")
    before = page.read_text(encoding="utf8")
    assert verify_mark.main(["concepts/widget.md", "--by", "process:okf-lint"]) == 1
    assert "fix it by hand" in capsys.readouterr().err
    assert page.read_text(encoding="utf8") == before


def test_an_entry_at_column_zero_is_appended_at_its_own_indent(bare, capsys):
    page = with_verified(bare, "verified:\n- { by: process:cross-check, at: 2026-01-01T09:00:00+10:00 }")
    assert verify_mark.main(["concepts/widget.md", "--by", "process:okf-lint"]) == 0
    fm, _, _, err = pc.read_page(page)
    assert err is None
    assert len(pc.verified_entries(fm)) == 2


def test_the_verification_time_is_the_configured_timezones(bare, capsys, utc_host):
    make(bare)
    assert verify_mark.main(["concepts/widget.md", "--by", "process:cross-check"]) == 0
    fm, _, _, _ = pc.read_page(page_path(bare, "concepts/widget.md"))
    at = pc.parse_datetime(pc.verified_entries(fm)[0]["at"])
    assert at.utcoffset() == ZoneInfo("Australia/Melbourne").utcoffset(at)
