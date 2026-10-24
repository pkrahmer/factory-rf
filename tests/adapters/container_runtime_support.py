"""What the runtime tests in a container share: the played dataset, its environment, a record."""

import sys
from datetime import timedelta
from pathlib import Path

from adapters.opencode_stand_in import opencode_request
from factory.domain.agent_runs import AgentRunRequest
from factory.domain.containers import WORK_HOME, Mount

LANG = "C.UTF-8"
LIMIT = timedelta(seconds=30)


def make_workspace(tmp_path: Path) -> Path:
    """The folder the fake plays `/work` as, with its `checkout/` and `home/` made."""
    workspace = tmp_path / "workspace"
    (workspace / "checkout").mkdir(parents=True)
    (workspace / "home").mkdir()
    return workspace


def container_environment(stand_in_bin: Path) -> dict[str, str]:
    """A request's environment in a container: `HOME` in the dataset, the stand-in on `PATH`."""
    return {"HOME": WORK_HOME, "LANG": LANG, "PATH": f"{stand_in_bin}:/usr/bin:/bin"}


def read_only(path: Path) -> Mount:
    """The mount of `path` read-only at its own path."""
    return Mount(source=path, target=str(path), read_only=True)


def write_record_program(folder: Path) -> tuple[Path, Path]:
    """A program that writes a record file when started; its path and the record's path."""
    folder.mkdir(parents=True)
    record = folder / "started"
    program = folder / "leftovers"
    program.write_text(
        f"#!{sys.executable} -B\n"
        "from pathlib import Path\n"
        f"Path({str(record)!r}).write_text('started', encoding='utf-8')\n",
        encoding="utf-8",
    )
    program.chmod(0o755)
    return program, record


def files_in(folder: Path) -> list[Path]:
    """Every file left in `folder`, none when it does not exist."""
    if not folder.exists():
        return []
    return sorted(folder.iterdir())


def container_request(
    tmp_path: Path, *, time_limit: timedelta = LIMIT, os_user: str | None = None
) -> AgentRunRequest:
    """An opencode request whose environment is a container's, the stand-in under `bin/`."""
    return opencode_request(
        tmp_path / "work",
        environment=container_environment(tmp_path / "bin"),
        time_limit=time_limit,
        os_user=os_user,
    )


def make_state(tmp_path: Path) -> Path:
    """The runtime's state folder, `tmp_path / "state"`, made when it is missing."""
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    return state
