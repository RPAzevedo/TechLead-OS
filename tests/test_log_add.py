"""tos-log writes the canonical log shape, newest first."""
import datetime as dt

from conftest import config_today

from tos import common as pc
from tos import lint as tos_lint
from tos import log_add


def log_text(root):
    return (root / "wiki" / "log.md").read_text(encoding="utf8")


def test_appends_under_todays_existing_heading(bare, capsys):
    assert log_add.main(["Ingest", "first thing"]) == 0
    assert log_add.main(["Query", "second thing"]) == 0
    text = log_text(bare)
    assert text.count(f"## {config_today().isoformat()}") == 1  # tos-init already wrote today's heading
    assert text.index("* **Ingest**: first thing") < text.index("* **Query**: second thing")


def test_older_and_newer_dates_stay_in_date_order(bare, capsys):
    today = config_today()
    assert log_add.main(["Ingest", "backfilled", "--date", (today - dt.timedelta(days=3)).isoformat()]) == 0
    assert log_add.main(["Ingest", "ahead", "--date", (today + dt.timedelta(days=1)).isoformat()]) == 0
    text = log_text(bare)
    assert (text.index(f"## {(today + dt.timedelta(days=1)).isoformat()}")
            < text.index(f"## {today.isoformat()}")
            < text.index(f"## {(today - dt.timedelta(days=3)).isoformat()}"))
    capsys.readouterr()
    assert tos_lint.main([]) == 0
    assert "## log" not in capsys.readouterr().out


def test_prints_the_bullet_for_the_commit_message(bare, capsys):
    assert log_add.main(["Verify", "some page"]) == 0
    assert capsys.readouterr().out.strip() == "* **Verify**: some page"


def test_unknown_label_is_refused(bare, capsys):
    assert log_add.main(["Frobnicate", "whatever"]) == 2
    assert "Frobnicate" in capsys.readouterr().err
    assert "Frobnicate" not in log_text(bare)


def test_missing_log_says_run_init(bare, capsys):
    (bare / "wiki" / "log.md").unlink()
    assert log_add.main(["Ingest", "text"]) == 1
    assert "tos-init" in capsys.readouterr().err


def test_dry_run_writes_nothing(bare, capsys):
    before = log_text(bare)
    assert log_add.main(["Ingest", "phantom", "--dry-run"]) == 0
    assert log_text(bare) == before


def test_the_days_heading_is_the_configured_timezones_day(bare, capsys, utc_host, monkeypatch):
    """15:30 UTC is 01:30 the next day in Melbourne: the log is the human's calendar."""
    fixed = dt.datetime(2026, 9, 2, 15, 30, tzinfo=dt.timezone.utc)

    class Clock(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.astimezone(tz)

    monkeypatch.setattr(pc.dt, "datetime", Clock)
    assert log_add.main(["Ingest", "after hours"]) == 0
    monkeypatch.undo()
    text = log_text(bare)
    assert "## 2026-09-03\n* **Ingest**: after hours" in text
