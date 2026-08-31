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

# {command: phase}. The phase is the last column; the first may contain escaped pipes.
PHASES = {
    m.group(1): re.search(r"\|\s*(\d+)\s*\|\s*$", row).group(1)
    for row in commands_table()
    for m in [re.match(r"\| `/(tos-[a-z-]+)", row)]
    if m and re.search(r"\|\s*(\d+)\s*\|\s*$", row)
}


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


def test_every_table_row_names_a_phase():
    """A row whose phase column did not parse would silently skip the gating test below."""
    assert set(PHASES) == TABLED


# Each way a gated command states its phase, and how to read the number back out. `\d+` is
# greedy, so a stub saying `below 20` reads as 20 and does not satisfy a README phase of 2.
GATES = {
    "refuses below": r"\bbelow (\d+)\b",
    "names in its refusal": r"\bnot enabled until phase (\d+)\b",
    "tells you to set": r"\brollout\.phase: (\d+)\b",
}


@pytest.mark.parametrize("path", COMMANDS, ids=lambda p: p.name)
def test_a_command_is_gated_by_the_phase_the_readme_promises(path):
    """A phase the README gates must be a refusal the command file actually makes.

    The stub is the whole of a later-phase command until that phase is built, so
    nothing else would notice if the number in it drifted from the table.
    """
    phase, body = PHASES[path.stem], path.read_text(encoding="utf8")
    if phase == "1":
        assert "not enabled until phase" not in body, f"/{path.stem} is phase 1 but refuses to run"
        return
    assert "rollout.phase" in body, f"/{path.stem} is phase {phase} but never reads rollout.phase"
    for what, pattern in GATES.items():
        found = sorted(set(re.findall(pattern, body)))
        assert found == [phase], (
            f"/{path.stem} is phase {phase} in the README but {what} phase {found or 'nothing'}"
        )
