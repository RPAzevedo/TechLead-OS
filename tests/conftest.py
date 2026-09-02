"""Shared fixtures: real data roots built by tos-init, config via $TOS_CONFIG."""
import time

import pytest

from tos import common as pc
from tos import init as tos_init


def _root(tmp_path, monkeypatch, args):
    root = tmp_path / "data"
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f'engine: "0.8"\ndata:\n  root: {root}\n  timezone: Australia/Melbourne\n'
        f"  actor: human:test\nrollout:\n  phase: 1\n",
        encoding="utf8",
    )
    monkeypatch.setenv("TOS_CONFIG", str(cfg))
    assert tos_init.main(args) == 0
    return root


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    """A real data root built by tos-init, with the example pages."""
    return _root(tmp_path, monkeypatch, ["--with-examples"])


@pytest.fixture
def bare(tmp_path, monkeypatch):
    """A data root with no example pages: the new checks see only what a test writes."""
    return _root(tmp_path, monkeypatch, [])


def config_today():
    """Today in the config's timezone — the day every helper writes, whatever the host's is."""
    return pc.today(pc.load_config())


@pytest.fixture
def utc_host(monkeypatch):
    """The host runs in UTC while the config says Australia/Melbourne."""
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()
