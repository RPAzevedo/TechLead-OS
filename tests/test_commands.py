"""The command surface and the README's Commands table are one thing, kept in sync here.

Every operation is a slash command named `/tos-<verb>`; the table under
`## Commands` is where a reader finds out one exists, with its arguments and the
phase that enables it. A command file added without a row there, or without the
prefix, fails this. Mentions elsewhere in the README do not count.
"""
import re

import pytest

from tos.common import ENGINE_ROOT

COMMAND_DIR = ENGINE_ROOT / ".claude" / "commands"
COMMANDS = sorted(COMMAND_DIR.glob("*.md"))
README = (ENGINE_ROOT / "README.md").read_text(encoding="utf8")


def commands_table() -> list[str]:
    """The table rows under `## Commands`, up to the next heading."""
    section = re.search(r"^## Commands$(.*?)^## ", README, re.M | re.S)
    assert section, "README.md has no `## Commands` section"
    rows = [ln for ln in section.group(1).splitlines() if ln.startswith("|")]
    assert len(rows) > 2, "the Commands section has no table"
    return rows[2:]  # drop the header and its separator


TABLED = {m.group(1) for row in commands_table() for m in [re.match(r"\| `/(tos-[a-z-]+)", row)] if m}


def test_commands_were_found():
    assert COMMANDS, f"no command files under {COMMAND_DIR}"


@pytest.mark.parametrize("path", COMMANDS, ids=lambda p: p.name)
def test_command_is_prefixed(path):
    assert path.name.startswith("tos-"), f"{path.name}: commands are named tos-<verb>.md"


@pytest.mark.parametrize("path", COMMANDS, ids=lambda p: p.name)
def test_command_has_a_row_in_the_readme_table(path):
    assert path.stem in TABLED, f"/{path.stem} has no row in the README's Commands table"


def test_the_table_lists_no_command_that_does_not_exist():
    assert TABLED <= {p.stem for p in COMMANDS}


def test_every_table_row_names_a_command():
    """A malformed row would otherwise be skipped by the regex and pass silently."""
    assert len(TABLED) == len(commands_table())
