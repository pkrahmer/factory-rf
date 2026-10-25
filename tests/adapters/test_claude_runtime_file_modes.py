"""The files of a run are readable by the agent's group and writable by the factory alone."""

import json
import os
import sys
from collections.abc import Iterator
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest

MODES = "modes.json"

# Records the mode of every file its arguments name and of the files beside them, which
# include the guard file the hooks file names.
SCRIPT = r"""
import json
import stat
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
modes = {}
for argument in sys.argv[1:]:
    try:
        path = Path(argument)
        if path.is_file():
            for sibling in path.parent.iterdir():
                if sibling.is_file():
                    modes[sibling.name] = stat.S_IMODE(sibling.stat().st_mode)
    except (OSError, ValueError):
        pass
(here / "modes.json").write_text(json.dumps(modes), encoding="utf-8")
"""


@pytest.fixture
def open_umask() -> Iterator[None]:
    """Run the test under the umask `0000` and restore the previous one afterwards."""
    previous = os.umask(0)
    yield
    os.umask(previous)


def _stand_in(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "claude"
    path.write_text(f"#!{sys.executable} -B\n{SCRIPT}", encoding="utf-8")
    path.chmod(0o755)
    return path


def _request(tmp_path: Path) -> AgentRunRequest:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    return AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Read"],
            budget_usd=Decimal("1"),
            instructions="Write the code.",
        ),
        prompt="Stage: doing",
        allowed_decisions=["doing", "question"],
        time_limit=timedelta(seconds=30),
        working_directory=work,
        environment={"LANG": "C.UTF-8"},
    )


@pytest.mark.usefixtures("open_umask")
@pytest.mark.parametrize("prefixes", [["instructions-"]], ids=["run"])
def test_the_files_of_a_run_are_0640_when_the_agent_starts(
    tmp_path: Path, prefixes: list[str]
) -> None:
    executable = _stand_in(tmp_path / "bin")
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state")

    runtime.run(_request(tmp_path))

    modes: dict[str, int] = json.loads((tmp_path / "bin" / MODES).read_text(encoding="utf-8"))
    assert sorted(name.split("-")[0] + "-" for name in modes) == prefixes
    assert set(modes.values()) == {0o640}
