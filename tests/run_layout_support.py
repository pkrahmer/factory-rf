"""The run layout and the request of the runtime tests."""

import sys
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel

from factory.application.agent_runtime import AgentRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.errors import AgentRuntimeError

LIMIT = timedelta(seconds=30)


@dataclass(frozen=True)
class Layout:
    """The folders of one run: checkout, home, state and the stand-ins'."""

    checkout: Path
    home: Path
    state: Path
    stand_in: Path
    shell_bin: Path


def build_layout(tmp_path: Path) -> Layout:
    """Return a checkout with `src` and `other`, and a home under `tmp_path`."""
    checkout = tmp_path / "checkout"
    for folder in (checkout / "src", checkout / "other", tmp_path / "home"):
        folder.mkdir(parents=True)
    return Layout(
        checkout=checkout,
        home=tmp_path / "home",
        state=tmp_path / "state",
        stand_in=checkout / "stand-in",
        shell_bin=tmp_path / "shell-bin",
    )


def write_script(path: Path, script: str) -> Path:
    """Write `script` as an executable run by the test's interpreter and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!{sys.executable} -B\n{script}", encoding="utf-8")
    path.chmod(0o755)
    return path


def write_login_file(layout: Layout) -> Path:
    """Write a stand-in login file beside the checkout, readable by its owner alone."""
    path = layout.checkout.parent / "login"
    path.write_text("stand-in-login\n", encoding="utf-8")
    path.chmod(0o600)
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


def run_end(runtime: AgentRuntime, layout: Layout) -> tuple[str | None, str | None]:
    """Run the layout's request: the refusal's detail, or the run's end reason."""
    try:
        result = runtime.run(run_request(layout))
    except AgentRuntimeError as error:
        return error.detail, None
    return None, result.end_reason
