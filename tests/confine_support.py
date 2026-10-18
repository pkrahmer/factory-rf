"""The run layout, the stand-in confine executable and the request of the runtime's guard tests."""

import sys
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from factory.adapters.claude_runtime import SUDO_EXECUTABLE, ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, GuardSettings

# The installed wrapper, beside the interpreter that runs the tests.
CONFINE = str(Path(sys.executable).parent / "factory-confine")
LINE = "factory-confine: the kernel offers Landlock ABI 2, the write guard needs ABI 3 or higher"
STAND_IN_TOOL_PATH = "stand-in/*"
LIMIT = timedelta(seconds=30)

# A confine executable that records its arguments and the rules file's text and mode, then
# plays its line or runs what follows `--`.
CONFINE_SCRIPT = r"""
import json
import os
import stat
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
arguments = sys.argv[1:]
rules = Path(arguments[arguments.index("--rules") + 1])
record = {
    "arguments": arguments,
    "rules_text": rules.read_text(encoding="utf-8"),
    "rules_mode": stat.S_IMODE(rules.stat().st_mode),
}
with (here / "confine-calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
played = here / "played.json"
if played.exists():
    play = json.loads(played.read_text(encoding="utf-8"))
    sys.stderr.write(play["stderr"])
    sys.stderr.flush()
    sys.stdout.write(play["stdout"])
    sys.stdout.flush()
    time.sleep(play["wait_seconds"])
    sys.exit(play["exit_status"])
rest = arguments[arguments.index("--") + 1 :]
os.execvp(rest[0], rest)
"""


class Played(BaseModel):
    """What the stand-in confine executable plays instead of running the call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stderr: str = f"{LINE}\n"
    stdout: str = ""
    wait_seconds: float = 0
    exit_status: int = 1


class ConfineCall(BaseModel):
    """What the stand-in confine executable saw: its arguments and the rules file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    rules_text: str
    rules_mode: int


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
    path.write_text(f"#!{sys.executable}\n{script}", encoding="utf-8")
    path.chmod(0o755)
    return path


def read_records[M: BaseModel](path: Path, model: type[M]) -> list[M]:
    """Return the records of the JSON lines file at `path`, none when it is missing."""
    if not path.exists():
        return []
    return [
        model.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines()
    ]


def write_confine(layout: Layout, played: Played | None = None) -> Path:
    """Write the stand-in confine executable, playing `played` instead of the call if given."""
    path = write_script(layout.confine_bin / "factory-confine", CONFINE_SCRIPT)
    if played is not None:
        (layout.confine_bin / "played.json").write_text(played.model_dump_json(), encoding="utf-8")
    return path


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


def confined_runtime(
    layout: Layout, executable: Path, confine: str = CONFINE, sudo: Path | None = None
) -> ClaudeCodeRuntime:
    """Return a runtime that starts `executable` through `confine` in the layout's folders."""
    return ClaudeCodeRuntime(
        str(executable),
        layout.state,
        sudo_executable=SUDO_EXECUTABLE if sudo is None else str(sudo),
        confine_executable=confine,
        temporary_root=layout.temporary_root,
    )
