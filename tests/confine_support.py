"""The run layout and the request of the runtime's guard tests."""

import json
import stat
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import NoReturn

from pydantic import BaseModel

from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, GuardSettings

STAND_IN_TOOL_PATH = "stand-in/*"
LIMIT = timedelta(seconds=30)
USAGE = "factory-confine: usage: factory-confine --rules <file> -- <command> [<argument>...]\n"


@dataclass(frozen=True)
class Layout:
    """The folders of one run: checkout, home, state, temporary root and the stand-ins'."""

    checkout: Path
    home: Path
    state: Path
    temporary_root: Path
    stand_in: Path
    confine_bin: Path
    sudo_bin: Path
    shell_bin: Path


def build_layout(tmp_path: Path) -> Layout:
    """Return a checkout with `src` and `other`, a home and a temporary root under `tmp_path`."""
    checkout = tmp_path / "checkout"
    for folder in (checkout / "src", checkout / "other", tmp_path / "home", tmp_path / "tmp"):
        folder.mkdir(parents=True)
    return Layout(
        checkout=checkout,
        home=tmp_path / "home",
        state=tmp_path / "state",
        temporary_root=tmp_path / "tmp",
        stand_in=checkout / "stand-in",
        confine_bin=tmp_path / "confine-bin",
        sudo_bin=tmp_path / "sudo-bin",
        shell_bin=tmp_path / "shell-bin",
    )


def write_script(path: Path, script: str) -> Path:
    """Write `script` as an executable run by the test's interpreter and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!{sys.executable} -B\n{script}", encoding="utf-8")
    path.chmod(0o755)
    return path


def read_records[M: BaseModel](path: Path, model: type[M]) -> list[M]:
    """Return the records of the JSON lines file at `path`, none when it is missing."""
    if not path.exists():
        return []
    return [
        model.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines()
    ]


def run_request(
    layout: Layout,
    *,
    write_paths: tuple[str, ...] = ("src/*",),
    tool_paths: tuple[str, ...] = (STAND_IN_TOOL_PATH,),
    with_home: bool = True,
    os_user: str | None = None,
    time_limit: timedelta = LIMIT,
) -> AgentRunRequest:
    """Return a coder's request in the layout's checkout, guarded by these paths."""
    return AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Bash"],
            budget_usd=Decimal("1"),
            instructions="Write the code.",
        ),
        prompt="Stage: doing",
        allowed_decisions=["doing", "question"],
        time_limit=time_limit,
        working_directory=layout.checkout,
        environment={"HOME": str(layout.home)} if with_home else {},
        guard=GuardSettings(
            root=layout.checkout,
            write_paths=list(write_paths),
            protected_paths=[],
            tool_paths=list(tool_paths),
        ),
        os_user=os_user,
    )


def write_rules(
    tmp_path: Path, folders: list[Path], files: list[Path], temporary: Path | str
) -> Path:
    """Write the wrapper's rules of these folders, files and temporary folder; return the file."""
    path = tmp_path / "rules.json"
    path.write_text(
        json.dumps(
            {
                "folders": [str(folder) for folder in folders],
                "files": [str(file) for file in files],
                "temporary_directory": str(temporary),
            }
        ),
        encoding="utf-8",
    )
    return path


class Replaced(Exception):
    """Raised by the recording `replace` in place of becoming the command."""


class Steps:
    """Records the calls to `restrict` and `replace` and what the disk held at `restrict`."""

    def __init__(
        self,
        restrict_fault: Exception | None = None,
        replace_fault: Exception | None = None,
    ) -> None:
        """Record every call; raise the given faults instead of returning."""
        self.calls: list[str] = []
        self.restricted: list[tuple[list[Path], list[Path]]] = []
        self.replaced: list[tuple[list[str], dict[str, str]]] = []
        self.watched: list[Path] = []
        self.seen: dict[Path, int | None] = {}
        self.restrict_fault = restrict_fault
        self.replace_fault = replace_fault

    def restrict(self, folders: Sequence[Path], files: Sequence[Path]) -> None:
        """Record the rules and the mode of every watched path at this moment."""
        self.calls.append("restrict")
        self.restricted.append((list(folders), list(files)))
        for path in self.watched:
            self.seen[path] = stat.S_IMODE(path.lstat().st_mode) if path.is_dir() else None
        if self.restrict_fault is not None:
            raise self.restrict_fault

    def replace(self, command: Sequence[str], environment: Mapping[str, str]) -> NoReturn:
        """Record the command and its environment, then stop the wrapper's run."""
        self.calls.append("replace")
        self.replaced.append((list(command), dict(environment)))
        raise self.replace_fault if self.replace_fault is not None else Replaced
