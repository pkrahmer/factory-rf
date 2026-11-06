"""The documents command: the findings of the documents and the guide's files, one per line."""

import argparse
import importlib
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from factory.hosting.adapters.checkout_fixture import CheckoutFixture
from factory.hosting.adapters.git_cli import GitCli
from factory.hosting.adapters.instance_fixture import InstanceFixture
from factory.shared.adapters.document_examples import ProcessExampleRunner
from factory.shared.application.document_examples import ExampleRunner, Fixture
from factory.shared.domain import settings
from factory.shared.domain.documents import (
    CHECKED_DOCUMENTS,
    DEFAULT_FIXTURE,
    DOCUMENT_PATHS,
    INSTANCE_FIXTURE,
    OPERATOR_GUIDE_FOLDER,
    OPERATOR_INSTALL,
    PROJECT_GUIDE_FOLDER,
    README,
    SETTINGS_SECTION,
    GatedFinding,
    Reference,
    check_documents,
    checked_list_findings,
    examples,
    guide_tables,
    is_guide_file,
    named_references,
    read_checked_documents,
    refusal_findings,
    settings_findings,
    split_findings,
    unresolved,
)

_PROGRAM = "check-documents"
_CLEAN = 0
_FINDINGS = 1
_REPORT_HEADING = "Report (not checked yet):"


def _read(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _guide_files(root: Path) -> list[str]:
    folder = root / PROJECT_GUIDE_FOLDER
    if not folder.is_dir():
        return []
    files = (entry for entry in folder.iterdir() if entry.is_file())
    paths = (f"{PROJECT_GUIDE_FOLDER}/{entry.name}" for entry in files)
    return [path for path in paths if is_guide_file(path)]


def _named_documents(root: Path) -> list[str]:
    folders = (root / OPERATOR_GUIDE_FOLDER, root / PROJECT_GUIDE_FOLDER)
    inside = sorted(
        path
        for folder in folders
        if folder.is_dir()
        for path in folder.rglob("*.md")
        if path.is_file()
    )
    readme = [root / README] if (root / README).is_file() else []
    return [path.relative_to(root).as_posix() for path in [*readme, *inside]]


def _module_or_attribute_exists(name: str) -> bool:
    parts = name.split(".")
    for length in range(len(parts), 0, -1):
        try:
            found: object = importlib.import_module(".".join(parts[:length]))
        except ImportError:
            continue
        for attribute in parts[length:]:
            if not hasattr(found, attribute):
                return False
            found = getattr(found, attribute)
        return True
    return False


def _path_exists(root: Path, name: str) -> bool:
    target = (root / name).resolve()
    return target.is_relative_to(root.resolve()) and target.exists()


def _existence(root: Path) -> Callable[[Reference], bool]:
    def exists(reference: Reference) -> bool:
        if reference.kind == "module":
            return _module_or_attribute_exists(reference.name)
        return _path_exists(root, reference.name)

    return exists


def _name_findings(root: Path, documents: Sequence[str]) -> list[GatedFinding]:
    top_level = frozenset(entry.name for entry in root.iterdir())
    exists = _existence(root)
    return [
        GatedFinding(document=document, line=line)
        for document in documents
        for line in unresolved(
            named_references(document, (root / document).read_text(encoding="utf-8"), top_level),
            exists,
        )
    ]


def _settings_guide_findings(root: Path) -> list[GatedFinding]:
    text = _read(root / OPERATOR_INSTALL)
    if text is None:
        return []
    tables = guide_tables(text, SETTINGS_SECTION)
    source = Path(settings.__file__).read_text(encoding="utf-8")
    messages = [
        *settings_findings(tables, settings.SETTINGS),
        *refusal_findings(tables, source),
    ]
    return [
        GatedFinding(document=OPERATOR_INSTALL, line=f"{OPERATOR_INSTALL}: {message}")
        for message in messages
    ]


def _example_results(
    root: Path,
    documents: Sequence[str],
    runner: ExampleRunner,
    fixtures: Mapping[str, Fixture],
) -> tuple[list[GatedFinding], list[str]]:
    findings: list[GatedFinding] = []
    not_run: list[str] = []
    for document in documents:
        found = examples((root / document).read_text(encoding="utf-8"))
        if found.runnable:
            lines = runner.run_document(document, found.runnable, fixtures)
            findings += [GatedFinding(document=document, line=line) for line in lines]
        not_run += [f"{document}:{block.line}: not run ({block.kind})" for block in found.skipped]
    return findings, not_run


def _checked_documents(root: Path) -> list[str]:
    text = _read(root / CHECKED_DOCUMENTS)
    return [] if text is None else read_checked_documents(text)


def main(argv: Sequence[str] | None = None) -> int:
    """Print the blocking findings, then the report, then the time when nothing blocks.

    Blocking are the document findings of every file, the listed paths of
    `docs/checked-documents.txt` that are no document of the check, and the findings of the
    name, settings and example checks in a listed document; each fails the command with
    exit status 1. The other findings of those three checks and one line per example not
    run follow under `Report (not checked yet):`, a heading left out when there is nothing
    to report. When nothing blocks, the last line is `documents ok (<seconds> s)`.
    """
    started = time.monotonic()
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    root: Path = arguments.root
    paths = [*DOCUMENT_PATHS, *_guide_files(root)]
    findings = check_documents({path: _read(root / path) for path in paths})
    documents = _named_documents(root)
    listed = _checked_documents(root)
    git = GitCli(root)
    fixtures = {DEFAULT_FIXTURE: CheckoutFixture(git), INSTANCE_FIXTURE: InstanceFixture(git)}
    example_findings, not_run = _example_results(root, documents, ProcessExampleRunner(), fixtures)
    gated_findings = [
        *_name_findings(root, documents),
        *_settings_guide_findings(root),
        *example_findings,
    ]
    split = split_findings(gated_findings, frozenset(listed))
    blocking = [
        *(f"{finding.document}: {finding.message}" for finding in findings),
        *checked_list_findings(listed, documents),
        *split.blocking,
    ]
    _print_lines(blocking)
    reported = [*split.reported, *not_run]
    if reported:
        print(_REPORT_HEADING)
        _print_lines(reported)
    if blocking:
        return _FINDINGS
    print(f"documents ok ({time.monotonic() - started:.1f} s)")
    return _CLEAN


def _print_lines(lines: Sequence[str]) -> None:
    for line in lines:
        print(line)


if __name__ == "__main__":
    raise SystemExit(main())
