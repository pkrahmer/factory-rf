"""The run layout and the request of the runtime tests."""

import sys
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel

from factory.domain.agent_runs import AgentDefinition, AgentRunRequest

LIMIT = timedelta(seconds=30)


@dataclass(frozen=True)
class Layout:
    """The folders of one run: checkout, home, state, temporary root and the stand-ins'."""

    checkout: Path
    home: Path
    state: Path
    temporary_root: Path
    stand_in: Path
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
    with_home: bool = True,
    time_limit: timedelta = LIMIT,
) -> AgentRunRequest:
    """Return a coder's request in the layout's checkout."""
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
    )
