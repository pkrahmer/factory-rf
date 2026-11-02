"""A stand-in program that records its arguments, and the calls it recorded."""

import json
from pathlib import Path
from typing import Any

from git_support import write_executable


def recording_stand_in(folder: Path, *, printed: str = "") -> Path:
    """A program that appends its arguments, one JSON list a line, to `calls` beside it."""
    folder.mkdir(parents=True)
    calls = folder / "calls"
    return write_executable(
        folder,
        "import json, sys\n"
        f"with open({str(calls)!r}, 'a', encoding='utf-8') as file:\n"
        "    file.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        f"sys.stdout.write({printed!r})\n",
    )


def read_records(path: Path) -> list[Any]:
    """The JSON values a stand-in wrote to `path`, one a line, oldest first; none when never run."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def recorded_calls(executable: Path) -> list[list[str]]:
    """The argument lists the stand-in `executable` recorded, oldest first; none when never run."""
    return read_records(executable.parent / "calls")
