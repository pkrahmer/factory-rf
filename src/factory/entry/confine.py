"""The start wrapper: confines its writes to a run's rules, then becomes the command."""

import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO

from pydantic import ValidationError

from factory.adapters.landlock import abi_version, restrict_writes
from factory.adapters.process import replace_process
from factory.domain.confinement import Confinement, abi_fault
from factory.domain.errors import ConfinementError

_PREFIX = "factory-confine: "
_USAGE = "usage: factory-confine --rules <file> -- <command> [<argument>...]"
_RULES_OPTION = "--rules"
_SEPARATOR = "--"
_FAILED = 1
_TEMPORARY_FOLDER_MODE = 0o700


class _Stop(Exception):
    """A fault before the command starts; its message is the line to write."""


def main(
    argv: Sequence[str] | None = None,
    *,
    stderr: TextIO | None = None,
    abi: Callable[[], int] | None = None,
) -> int:
    """Confine this process's writes to the rules, then become the command; 1 when it cannot."""
    arguments = sys.argv[1:] if argv is None else list(argv)
    errors = sys.stderr if stderr is None else stderr
    kernel_abi = abi_version if abi is None else abi
    try:
        rules_file, command = _parse(arguments)
        _confine_and_start(_read_rules(rules_file), command, kernel_abi)
    except _Stop as stop:
        errors.write(f"{_PREFIX}{stop}\n")
    return _FAILED


def _parse(arguments: list[str]) -> tuple[Path, list[str]]:
    # Exactly `--rules <file> -- <command> [<argument>...]`, so no option is mistaken for another.
    if len(arguments) < 4 or arguments[0] != _RULES_OPTION or arguments[2] != _SEPARATOR:
        raise _Stop(_USAGE)
    return Path(arguments[1]), arguments[3:]


def _read_rules(rules_file: Path) -> Confinement:
    try:
        return Confinement.model_validate_json(rules_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValidationError) as error:
        fault = " ".join(str(error).splitlines())
        raise _Stop(f"cannot read the rules {rules_file}: {fault}") from error


def _confine_and_start(rules: Confinement, command: list[str], abi: Callable[[], int]) -> None:
    fault = abi_fault(abi())
    if fault is not None:
        raise _Stop(fault)
    _make_folders(rules.folders)
    _make_temporary_folder(rules.temporary_directory)
    try:
        restrict_writes([*rules.folders, rules.temporary_directory], rules.files)
    except ConfinementError as error:
        raise _Stop(error.detail) from error
    environment = {**os.environ, "TMPDIR": str(rules.temporary_directory)}
    try:
        replace_process(command, environment)
    except OSError as error:
        raise _Stop(f"cannot start {command[0]}: {error.strerror}") from error


def _make_folders(folders: list[Path]) -> None:
    for folder in folders:
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise _Stop(f"cannot make the folder {folder}: {error.strerror}") from error


def _make_temporary_folder(path: Path) -> None:
    # Never `exist_ok`: a folder or link someone made beforehand could be read by them.
    try:
        os.mkdir(path, _TEMPORARY_FOLDER_MODE)
    except OSError as error:
        raise _Stop(f"cannot make the temporary folder {path}: {error.strerror}") from error


if __name__ == "__main__":
    raise SystemExit(main())
