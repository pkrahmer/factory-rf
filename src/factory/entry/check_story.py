"""The story check command: where each story sits and whether its form is complete."""

import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from factory.application.files import WorkItemReader
from factory.domain.errors import WorkItemFormatError
from factory.domain.paths import (
    FEATURE_FILE_NAME,
    FEATURES_DIRECTORY,
    STORY_FORM_FILE,
    LifecycleFolder,
)
from factory.domain.story_form import (
    FormFinding,
    check_story_form,
    check_story_place,
    lifecycle_folder_of_location,
)
from factory.domain.work_item import WorkItemDocument
from factory.entry.wiring import build_work_item_reader

_USAGE = "usage: factory-check-story <path>..."
_NO_FRONT_MATTER = "no front matter"
_OK = 0
_FINDINGS = 1
_FAILURE = 2


class _UnreadableError(Exception):
    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"cannot read {path}: {reason}")


class _Read(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    document: WorkItemDocument
    folder: LifecycleFolder


def _read_text(root: Path, path: str) -> str:
    try:
        return (root / path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise _UnreadableError(path, str(error)) from error


def _read_started(reader: WorkItemReader, text: str, folder: LifecycleFolder) -> _Read:
    try:
        return _Read(document=reader.parse(text), folder=folder)
    except WorkItemFormatError as error:
        if error.fault != _NO_FRONT_MATTER:
            raise
    # On main a started story is the human's moved file; its state lives on the
    # work item's branch, so it is checked as a specification.
    return _Read(document=reader.parse_specification(text), folder="backlog")


def _form_findings(
    reader: WorkItemReader, text: str, form: str, folder: LifecycleFolder
) -> list[FormFinding]:
    try:
        if folder == "backlog":
            read = _Read(document=reader.parse_specification(text), folder=folder)
        else:
            read = _read_started(reader, text, folder)
    except WorkItemFormatError as error:
        return [FormFinding(line=None, message=error.fault)]
    return check_story_form(read.document, form, folder=read.folder)


def _feature_file_exists(root: Path, path: str) -> bool:
    directory = path.split("/")[2]
    return (root / FEATURES_DIRECTORY / directory / FEATURE_FILE_NAME).is_file()


def _check(
    reader: WorkItemReader, root: Path, path: str, form: str, folder: LifecycleFolder
) -> list[FormFinding]:
    feature_file_exists = _feature_file_exists(root, path)
    text = _read_text(root, path)
    return [
        *check_story_place(path, feature_file_exists=feature_file_exists),
        *_form_findings(reader, text, form, folder),
    ]


def _print_findings(path: str, findings: Sequence[FormFinding]) -> None:
    if not findings:
        print(f"{path}: ok")
    for finding in findings:
        where = path if finding.line is None else f"{path}:{finding.line}"
        print(f"{where}: {finding.message}")


def _check_all(reader: WorkItemReader, root: Path, paths: Sequence[str], form: str) -> int:
    status = _OK
    for path in paths:
        folder = lifecycle_folder_of_location(path)
        if folder is None:
            # Not a work item location: nothing else is said, and the file is not read.
            findings = check_story_place(path, feature_file_exists=True)
        else:
            findings = _check(reader, root, path, form, folder)
        _print_findings(path, findings)
        if findings:
            status = _FINDINGS
    return status


def main(argv: Sequence[str] | None = None, *, root: Path | None = None) -> int:
    """Check each story path, print its findings or "ok", and return the exit status."""
    paths = list(sys.argv[1:] if argv is None else argv)
    base = Path.cwd() if root is None else root
    if not paths:
        print(_USAGE, file=sys.stderr)
        return _FAILURE
    try:
        form = _read_text(base, STORY_FORM_FILE)
        return _check_all(build_work_item_reader(), base, paths, form)
    except _UnreadableError as error:
        print(error, file=sys.stderr)
        return _FAILURE


if __name__ == "__main__":
    sys.exit(main())
