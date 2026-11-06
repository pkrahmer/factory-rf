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
    DEFAULT_FIXTURE,
    DOCUMENT_PATHS,
    OPERATOR_GUIDE_FOLDER,
    OPERATOR_INSTALL,
    PROJECT_GUIDE_FOLDER,
    README,
    SETTINGS_SECTION,
    Reference,
    check_documents,
    examples,
    guide_tables,
    is_guide_file,
    named_references,
    refusal_findings,
    settings_findings,
    unresolved,
)

_PROGRAM = "check-documents"
_INSTANCE_FIXTURE = "instance"
_CLEAN = 0
_FINDINGS = 1


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


def _name_findings(root: Path) -> list[str]:
    top_level = frozenset(entry.name for entry in root.iterdir())
    references = [
        reference
        for document in _named_documents(root)
        for reference in named_references(
            document, (root / document).read_text(encoding="utf-8"), top_level
        )
    ]
    return unresolved(references, _existence(root))


def _settings_guide_findings(root: Path) -> list[str]:
    text = _read(root / OPERATOR_INSTALL)
    if text is None:
        return []
    tables = guide_tables(text, SETTINGS_SECTION)
    source = Path(settings.__file__).read_text(encoding="utf-8")
    return [
        *settings_findings(tables, settings.SETTINGS),
        *refusal_findings(tables, source),
    ]


def _example_lines(root: Path, runner: ExampleRunner, fixtures: Mapping[str, Fixture]) -> list[str]:
    findings: list[str] = []
    not_run: list[str] = []
    for document in _named_documents(root):
        found = examples((root / document).read_text(encoding="utf-8"))
        if found.runnable:
            findings += runner.run_document(document, found.runnable, fixtures)
        not_run += [f"{document}:{block.line}: not run ({block.kind})" for block in found.skipped]
    return [*findings, *not_run]


def main(argv: Sequence[str] | None = None) -> int:
    """Print one line per finding, the examples' findings and skipped blocks, then the time.

    The document findings come first and alone decide the exit status: 1 when there is one,
    else 0 and a last line `documents ok (<seconds> s)`. The names, paths and links the
    documents name that do not exist follow, then where the operator guide's settings
    disagree with the settings code, then what the runnable examples printed otherwise and
    one line per example not run.
    """
    started = time.monotonic()
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    root: Path = arguments.root
    paths = [*DOCUMENT_PATHS, *_guide_files(root)]
    findings = check_documents({path: _read(root / path) for path in paths})
    for finding in findings:
        print(f"{finding.document}: {finding.message}")
    for name_finding in _name_findings(root):
        print(name_finding)
    for settings_finding in _settings_guide_findings(root):
        print(f"{OPERATOR_INSTALL}: {settings_finding}")
    git = GitCli(root)
    fixtures = {DEFAULT_FIXTURE: CheckoutFixture(git), _INSTANCE_FIXTURE: InstanceFixture(git)}
    for example_line in _example_lines(root, ProcessExampleRunner(), fixtures):
        print(example_line)
    if findings:
        return _FINDINGS
    print(f"documents ok ({time.monotonic() - started:.1f} s)")
    return _CLEAN


if __name__ == "__main__":
    raise SystemExit(main())
