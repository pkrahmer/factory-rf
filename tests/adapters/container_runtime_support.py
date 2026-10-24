"""What the runtime tests in a container share: the played dataset, its environment, a record."""

import sys
from pathlib import Path

from factory.domain.containers import WORK_HOME, Mount

LANG = "C.UTF-8"


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
