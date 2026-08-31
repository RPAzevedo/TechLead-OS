"""The deny list and what the README claims about it are one thing, kept in sync here.

Guardrail 11 is enforced by `.claude/settings.json`, and a permission rule matches a
tool by its exact name: an entry naming a server that does not exist is ignored in
silence. That is how 0.7.1's Atlassian entries came to guard nothing. Nothing here can
reach a live MCP server, so these check the two things that are checkable — that every
entry is well formed, and that every server the list guards is one the README names.
"""
import json
import re

import pytest

from tos.common import ENGINE_ROOT

SETTINGS = json.loads((ENGINE_ROOT / ".claude" / "settings.json").read_text(encoding="utf8"))
DENY = SETTINGS["permissions"]["deny"]
ENTRY_RE = re.compile(r"^mcp__(?P<server>[A-Za-z0-9_]+?)__(?P<tool>[A-Za-z0-9_]+)$")
SAFETY = re.search(r"^## Connector safety$(.*?)^## ",
                   (ENGINE_ROOT / "README.md").read_text(encoding="utf8"), re.M | re.S)


def servers() -> set[str]:
    return {m.group("server") for e in DENY for m in [ENTRY_RE.match(e)] if m}


def test_the_deny_list_is_not_empty():
    assert DENY


@pytest.mark.parametrize("entry", DENY, ids=lambda e: e)
def test_every_deny_entry_is_a_well_formed_mcp_tool_name(entry):
    """A malformed name is not a rule; it is a comment that looks like one."""
    assert ENTRY_RE.match(entry), f"{entry!r} is not `mcp__<server>__<tool>`"


def test_no_deny_entry_is_repeated():
    assert len(DENY) == len(set(DENY)), sorted({e for e in DENY if DENY.count(e) > 1})


def test_the_readme_documents_every_server_the_list_guards():
    """A server added to the deny list without a word in the README is a silent claim."""
    assert SAFETY, "README.md has no `## Connector safety` section"
    missing = sorted(s for s in servers() if f"`{s}`" not in SAFETY.group(1))
    assert not missing, f"guarded but undocumented: {missing}"
