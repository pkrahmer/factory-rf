"""A stand-in program that records its arguments, and the calls it recorded."""

import json
from pathlib import Path

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


def recorded_calls(executable: Path) -> list[list[str]]:
    """The argument lists the stand-in `executable` recorded, oldest first; none when never run."""
    calls = executable.parent / "calls"
    if not calls.exists():
        return []
    return [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()]
