"""tos-deny: the deny list the config implies, and whether it is in force.

The bug this exists to prevent is a permission rule that matches nothing. The
engine cannot know what your MCP servers are called, so the names come from the
config and the write-tool vocabulary comes from schema/connector-writes.yaml;
these check the crossing of the two, and that --write only ever adds.
"""
import json

import pytest

from tos import common as pc
from tos import deny as tos_deny

CFG = """engine: "0.7"
data:
  root: {root}
  timezone: Australia/Melbourne
  actor: human:test
rollout:
  phase: 1
connectors:
{connectors}
"""


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    """Write a config with the given connectors block and point $TOS_CONFIG at it."""
    def build(connectors: str):
        p = tmp_path / "config.yaml"
        p.write_text(CFG.format(root=tmp_path / "data", connectors=connectors), encoding="utf8")
        monkeypatch.setenv("TOS_CONFIG", str(p))
        return pc.load_config()
    return build


VOCAB = {"slack": ["post_message", "add_reaction"], "atlassian": ["create_issue"]}


def test_mcp_server_may_name_several_servers(cfg):
    c = cfg("  slack:\n    provider: mcp:slack\n    mcp_server: [slack, plugin_slack_slack]\n")
    assert tos_deny.servers(c) == {"slack": ["slack", "plugin_slack_slack"]}
    assert tos_deny.expected(c, VOCAB)["slack"] == [
        "mcp__slack__post_message", "mcp__slack__add_reaction",
        "mcp__plugin_slack_slack__post_message", "mcp__plugin_slack_slack__add_reaction",
    ]


def test_mcp_server_falls_back_to_the_provider_name(cfg):
    """A config written before the two were distinguished still yields entries."""
    c = cfg("  slack:\n    provider: mcp:slack\n")
    assert tos_deny.servers(c) == {"slack": ["slack"]}


def test_a_connector_with_no_mcp_server_contributes_nothing(cfg):
    """`md` is read off the filesystem; there is no server and so no tool to deny."""
    c = cfg("  md:\n    provider: filesystem\n    scope: { repos: [] }\n")
    assert tos_deny.servers(c) == {}
    assert tos_deny.expected(c, VOCAB) == {}


def test_an_unknown_kind_fails_closed_rather_than_reporting_nothing_to_do(cfg, monkeypatch, tmp_path, capsys):
    """A typo in `provider` must not read as "this server has no write tools".

    Reporting 0/0 and exiting 0 would be the same silent-pass that made 0.7.1's
    entries inert, one level up.
    """
    c = cfg("  notion:\n    provider: mcp:notoin\n")
    assert tos_deny.unknown_kinds(c, VOCAB) == {"notion": "notoin"}
    assert "notion" not in tos_deny.expected(c, VOCAB)

    monkeypatch.setattr(tos_deny.pc, "ENGINE_ROOT", tmp_path)
    (tmp_path / ".claude").mkdir()
    monkeypatch.setattr(tos_deny, "write_vocabulary", lambda: VOCAB)
    assert tos_deny.main([]) == 1
    assert "no write-tool vocabulary for" in capsys.readouterr().out


def test_a_kind_with_no_write_tools_is_declared_not_omitted():
    """`fetch` is read-only; it says so with an empty list rather than by absence."""
    vocab = tos_deny.write_vocabulary()
    assert vocab["fetch"] == []


def test_writing_twice_is_a_no_op_rather_than_a_crash(cfg, tmp_path, monkeypatch, capsys):
    """`--write` on an already-covered config used to raise UnboundLocalError."""
    monkeypatch.setattr(tos_deny.pc, "ENGINE_ROOT", tmp_path)
    (tmp_path / ".claude").mkdir()
    monkeypatch.setattr(tos_deny, "write_vocabulary", lambda: VOCAB)
    cfg("  slack:\n    provider: mcp:slack\n")

    assert tos_deny.main(["--write"]) == 0
    capsys.readouterr()
    assert tos_deny.main(["--write"]) == 0
    assert "every write tool the config implies is denied" in capsys.readouterr().out


def test_the_shipped_vocabulary_covers_every_kind_the_example_config_names():
    vocab = tos_deny.write_vocabulary()
    example = pc.load_yaml(pc.engine_path("config.example.yaml").read_text(encoding="utf8"))
    kinds = {tos_deny.kind_of(s) for s in (example.get("connectors") or {}).values()}
    # a kind with no write tools is declared with an empty list, never omitted
    missing = {k for k in kinds if k} - set(vocab)
    assert not missing, f"connector kinds with no write vocabulary: {sorted(missing)}"


def test_write_is_additive_and_idempotent(cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(pc, "ENGINE_ROOT", tmp_path)
    monkeypatch.setattr(tos_deny.pc, "ENGINE_ROOT", tmp_path)
    local = tmp_path / ".claude" / "settings.local.json"
    local.parent.mkdir(parents=True)
    local.write_text(json.dumps({"permissions": {"deny": ["mcp__mine__hand_written"]}}), encoding="utf8")

    tos_deny.add_to_local(tmp_path, ["mcp__slack__post_message"])
    tos_deny.add_to_local(tmp_path, ["mcp__slack__post_message"])
    deny = json.loads(local.read_text(encoding="utf8"))["permissions"]["deny"]

    assert deny.count("mcp__slack__post_message") == 1, "an entry was added twice"
    assert "mcp__mine__hand_written" in deny, "a hand-written rule was removed"


def test_missing_entries_exit_nonzero_and_writing_them_fixes_it(cfg, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tos_deny.pc, "ENGINE_ROOT", tmp_path)
    (tmp_path / ".claude").mkdir()
    monkeypatch.setattr(tos_deny, "write_vocabulary", lambda: VOCAB)
    cfg("  slack:\n    provider: mcp:slack\n")

    assert tos_deny.main([]) == 1
    assert "mcp__slack__post_message" in capsys.readouterr().out
    assert tos_deny.main(["--write"]) == 0
    capsys.readouterr()
    assert tos_deny.main([]) == 0
