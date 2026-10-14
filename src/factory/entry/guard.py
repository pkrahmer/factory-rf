"""The guard command: refuses a Claude Code tool call that writes outside the write paths."""

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from factory.domain.errors import GuardSettingsInvalid
from factory.entry.wiring import judge, read_guard_settings

_USAGE = "usage: factory-guard --settings <file>"
_SETTINGS_OPTION = "--settings"
_ALLOWED = 0
# Claude Code blocks the tool call on this status and shows stderr to the agent.
_REFUSED = 2


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Judge the hook payload on stdin; 0 allows the tool call, 2 refuses it."""
    arguments = sys.argv[1:] if argv is None else list(argv)
    source = sys.stdin if stdin is None else stdin
    errors = sys.stderr if stderr is None else stderr
    settings_path = _settings_path(arguments)
    if settings_path is None:
        return _refuse(errors, _USAGE)
    try:
        settings = read_guard_settings(settings_path)
    except GuardSettingsInvalid as error:
        return _refuse(errors, str(error))
    verdict = judge(source.read(), settings)
    if verdict.allowed:
        return _ALLOWED
    return _refuse(errors, verdict.message)


def _settings_path(arguments: list[str]) -> Path | None:
    if _SETTINGS_OPTION not in arguments:
        return None
    index = arguments.index(_SETTINGS_OPTION) + 1
    if index >= len(arguments):
        return None
    return Path(arguments[index])


def _refuse(errors: TextIO, message: str) -> int:
    errors.write(message + "\n")
    return _REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
