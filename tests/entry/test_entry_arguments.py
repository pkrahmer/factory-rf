"""The commands read the process's arguments when they are given none."""

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from document_texts import clean_texts, write_documents
from factory.domain.stops import HealthStatus
from factory.entry import check_documents, health, watch
from factory.entry.wiring import health_store


# Each builds the process's command line: the program name, then its arguments.
def _clean_documents(root: Path) -> list[str]:
    write_documents(root, clean_texts())
    return ["check_documents", "--root", str(root)]


def _empty_health_status(root: Path) -> list[str]:
    health_store(root).write(HealthStatus(stops=[]))
    return ["health", "--state-directory", str(root)]


def _colour(_root: Path) -> list[str]:
    return ["check_documents", "--colour"]


def _follow(_root: Path) -> list[str]:
    return ["watch", "--follow"]


@pytest.mark.parametrize(
    ("main", "command_line", "expected"),
    [
        (check_documents.main, _clean_documents, 0),
        (health.main, _empty_health_status, 0),
        (check_documents.main, _colour, 2),
        (watch.main, _follow, 2),
    ],
)
def test_main_without_arguments_reads_the_process_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    main: Callable[[], int],
    command_line: Callable[[Path], list[str]],
    expected: int,
) -> None:
    monkeypatch.setattr(sys, "argv", command_line(tmp_path))
    if expected == 0:
        assert main() == 0
        return
    with pytest.raises(SystemExit) as refusal:
        main()
    assert refusal.value.code == expected
