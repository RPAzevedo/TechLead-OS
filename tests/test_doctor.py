"""tos-doctor reports, never dies where it should report."""
import json

from tos import doctor


def test_healthy_bundle_passes(bare, capsys, monkeypatch):
    monkeypatch.setattr(doctor, "claude_mcp_list", lambda: None)
    assert doctor.main([]) == 0
    out = capsys.readouterr().out
    assert "ok    config" in out
    assert "`claude mcp list` unavailable" in out  # a skip note, not a crash


def test_missing_config_is_the_one_fatal_report(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("TOS_CONFIG", str(tmp_path / "nowhere.yaml"))
    assert doctor.main([]) == 1
    assert "config not found" in capsys.readouterr().out


def test_missing_data_root_fails(tmp_path, capsys, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text('engine: "0.9"\ndata:\n  root: /nonexistent/tos-data\n  timezone: UTC\n'
                   "  actor: human:test\n", encoding="utf8")
    monkeypatch.setenv("TOS_CONFIG", str(cfg))
    monkeypatch.setattr(doctor, "claude_mcp_list", lambda: None)
    assert doctor.main([]) == 1
    assert "run /tos-init" in capsys.readouterr().out


def test_engine_drift_and_connectors_are_warnings_not_failures(bare, capsys, monkeypatch):
    cfg_path = bare.parent / "config.yaml"
    cfg_path.write_text(cfg_path.read_text(encoding="utf8").replace('engine: "0.9"', 'engine: "0.5"')
                        + "connectors:\n  confluence:\n    provider: mcp:atlassian\n", encoding="utf8")
    monkeypatch.setattr(doctor, "claude_mcp_list", lambda: "some-other-server: npx foo\n")
    assert doctor.main(["--json"]) == 0
    rows = {r["check"]: r for r in json.loads(capsys.readouterr().out)}
    assert rows["engine"]["status"] == "warn"
    assert rows["mcp:atlassian"]["status"] == "warn"
    assert "no server named `atlassian`" in rows["mcp:atlassian"]["detail"]


def test_missing_claude_binary_is_skipped(bare, capsys, monkeypatch):
    real_run = doctor.subprocess.run

    def run(cmd, **kwargs):
        if cmd[0] == "claude":
            raise FileNotFoundError("claude")
        return real_run(cmd, **kwargs)
    monkeypatch.setattr(doctor.subprocess, "run", run)
    assert doctor.main([]) == 0
    assert "`claude mcp list` unavailable" in capsys.readouterr().out


SAMPLE = """Checking MCP server health…

claude.ai Google Drive: https://drivemcp.googleapis.com/mcp/v1 - ✔ Connected
plugin_atlassian_atlassian: npx foo - ✔ Connected
"""


def test_server_names_are_parsed_exactly_not_matched_as_substrings(bare, capsys, monkeypatch):
    """`mcp:atlassian` reading as present because `plugin_atlassian_atlassian`
    contains it is the exact mismatch this check exists to catch (0.7.3)."""
    cfg_path = bare.parent / "config.yaml"
    cfg_path.write_text(cfg_path.read_text(encoding="utf8")
                        + "connectors:\n  confluence:\n    provider: mcp:atlassian\n"
                          "  gdocs:\n    provider: mcp:claude_ai_Google_Drive\n", encoding="utf8")
    monkeypatch.setattr(doctor, "claude_mcp_list", lambda: SAMPLE)
    assert doctor.main(["--json"]) == 0
    rows = {r["check"]: r for r in json.loads(capsys.readouterr().out)}
    assert rows["mcp:atlassian"]["status"] == "warn"
    assert "no server named `atlassian`" in rows["mcp:atlassian"]["detail"]
    # the real server, named by its tool-prefix form, is found
    assert rows["mcp:claude_ai_Google_Drive"]["status"] == "ok"


def connectors(bare, text):
    cfg_path = bare.parent / "config.yaml"
    cfg_path.write_text(cfg_path.read_text(encoding="utf8") + text, encoding="utf8")


def test_deny_list_coverage_uses_the_same_exact_names(bare, capsys, monkeypatch):
    connectors(bare, "connectors:\n  gdocs:\n    provider: mcp:claude_ai_Google_Drive\n")
    monkeypatch.setattr(doctor, "claude_mcp_list", lambda: SAMPLE)
    assert doctor.main(["--json"]) == 0
    rows = {r["check"]: r for r in json.loads(capsys.readouterr().out)}
    assert rows["deny list"]["status"] == "ok"
    assert "claude_ai_Google_Drive" in rows["deny list"]["detail"]


def test_one_guarded_server_does_not_clear_an_unguarded_one(bare, capsys, monkeypatch):
    """A newly wired-up connector with no deny entries must not be hidden by a
    guarded one — that is a false all-clear on the safety check."""
    connectors(bare, "connectors:\n  gdocs:\n    provider: mcp:claude_ai_Google_Drive\n"
                     "  notes:\n    provider: mcp:brand_new_server\n")
    monkeypatch.setattr(doctor, "claude_mcp_list",
                        lambda: SAMPLE + "brand_new_server: npx foo - Connected\n")
    assert doctor.main(["--json"]) == 0
    rows = {r["check"]: r for r in json.loads(capsys.readouterr().out)}
    assert rows["deny list"]["status"] == "warn"
    assert "brand_new_server" in rows["deny list"]["detail"]
    assert "notes" in rows["deny list"]["detail"]  # names the connector that would use it


def test_deny_list_is_skipped_when_no_connector_server_is_installed(bare, capsys, monkeypatch):
    monkeypatch.setattr(doctor, "claude_mcp_list", lambda: SAMPLE)
    assert doctor.main(["--json"]) == 0
    rows = {r["check"]: r for r in json.loads(capsys.readouterr().out)}
    assert rows["deny list"]["status"] == "skip"


def test_an_unreadable_config_is_reported_not_raised(tmp_path, capsys, monkeypatch):
    """A directory, a permission denial or non-UTF-8 bytes used to escape as a traceback."""
    monkeypatch.setenv("TOS_CONFIG", str(tmp_path))  # a directory
    assert doctor.main([]) == 1
    assert "can not be read" in capsys.readouterr().out
    bad = tmp_path / "bad.yaml"
    bad.write_bytes(b'engine: "0.9"\ndata:\n  root: /tmp/x\n\xff\xfe\n')
    monkeypatch.setenv("TOS_CONFIG", str(bad))
    assert doctor.main([]) == 1
    assert "can not be read" in capsys.readouterr().out


def test_a_data_root_that_is_a_file_is_fatal(tmp_path, capsys, monkeypatch):
    root = tmp_path / "notadir"
    root.write_text("", encoding="utf8")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(f'engine: "0.9"\ndata:\n  root: {root}\n  timezone: UTC\n  actor: human:test\n',
                   encoding="utf8")
    monkeypatch.setenv("TOS_CONFIG", str(cfg))
    monkeypatch.setattr(doctor, "claude_mcp_list", lambda: None)
    assert doctor.main([]) == 1
    assert "is not a directory" in capsys.readouterr().out


def test_parse_mcp_servers_reads_the_name_field():
    assert doctor.parse_mcp_servers(SAMPLE) == {"claude.ai Google Drive", "plugin_atlassian_atlassian"}
    assert doctor.tool_prefix("claude.ai Google Drive") == "claude_ai_Google_Drive"


def test_a_timezone_that_is_not_an_iana_zone_is_a_warning(bare, capsys, monkeypatch):
    """The helpers fall back to the host zone for `Australia/Melborne`, so every page they
    write carries an offset the contract forbids — an all-ok report would hide that."""
    cfg_path = bare.parent / "config.yaml"
    cfg_path.write_text(cfg_path.read_text(encoding="utf8").replace("Australia/Melbourne", "Australia/Melborne"),
                        encoding="utf8")
    monkeypatch.setattr(doctor, "claude_mcp_list", lambda: None)
    assert doctor.main(["--json"]) == 0
    rows = {r["check"]: r for r in json.loads(capsys.readouterr().out)}
    assert rows["data.timezone"]["status"] == "warn"
    assert "not an IANA timezone" in rows["data.timezone"]["detail"]
