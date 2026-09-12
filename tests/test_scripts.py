"""The console scripts and the README's `uv run` table are one thing, kept in sync here.

The `tos-` prefix belongs to the Claude Code slash commands alone (see
`test_commands.py`, which enforces it there). A console script wears no prefix:
it is `uv run lint`, not `uv run tos-lint`. An entry point added to
`pyproject.toml` without a row in the README's install table, or with the prefix
back on, fails this.
"""
import re

import pytest

from tos.common import ENGINE_ROOT

PYPROJECT = (ENGINE_ROOT / "pyproject.toml").read_text(encoding="utf8")
README = (ENGINE_ROOT / "README.md").read_text(encoding="utf8")


def scripts() -> dict[str, str]:
    """`[project.scripts]` as {name: target}, read without tomllib (Python 3.10 support)."""
    section = re.search(r"^\[project\.scripts\]$(.*?)(?=^\[)", PYPROJECT, re.M | re.S)
    assert section, "pyproject.toml has no [project.scripts] section"
    found = dict(re.findall(r'^([\w-]+) = "([^"]+)"$', section.group(1), re.M))
    assert found, "no entry points parsed out of [project.scripts]"
    return found


SCRIPTS = scripts()

# Every `uv run <name>` in the install table. The table is the one place a reader
# finds out a command exists, with its arguments.
TABLED = {m.group(1) for m in re.finditer(r"^\| `uv run ([\w-]+)", README, re.M)}


@pytest.mark.parametrize("name", sorted(SCRIPTS), ids=lambda n: n)
def test_script_is_not_prefixed(name):
    assert not name.startswith("tos-"), f"{name}: `tos-` is for slash commands; a console script is a bare verb"


@pytest.mark.parametrize("name", sorted(SCRIPTS), ids=lambda n: n)
def test_script_has_a_row_in_the_readme_table(name):
    assert name in TABLED, f"`uv run {name}` has no row in the README's install table"


def test_the_table_lists_no_script_that_does_not_exist():
    assert TABLED <= set(SCRIPTS)


def test_every_script_target_is_importable():
    """A renamed key that lost its module would only surface at `uv sync` time."""
    import importlib

    for name, target in SCRIPTS.items():
        module, _, attr = target.partition(":")
        assert hasattr(importlib.import_module(module), attr), f"{name} points at a missing {target}"
