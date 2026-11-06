"""The minimal documents pass the document check and follow the code's tables."""

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.pipeline.domain import stop_table
from factory.shared.domain import documents, kill_point_cases, settings
from support.check_documents_support import TIME_LINE
from support.git_support import run_git
from support.minimal_documents_support import add_and_commit, minimal_documents


def _passes(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    status = main(["--root", str(root)])

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert re.fullmatch(TIME_LINE, lines[0])
    assert status == 0


def test_the_minimal_documents_pass_the_check_in_a_clean_work_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = minimal_documents(tmp_path / "root")

    _passes(root, capsys)
    assert run_git(root, "status", "--porcelain") == ""


def _one_more_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    added = stop_table.STOP_TABLE[0].model_copy(update={"id": "a_stop_of_the_test"})
    extended = (*stop_table.STOP_TABLE, added)
    monkeypatch.setattr(stop_table, "STOP_TABLE", extended)
    monkeypatch.setattr(documents, "STOP_TABLE", extended)


def _one_more_kill_point(monkeypatch: pytest.MonkeyPatch) -> None:
    added = kill_point_cases.KILL_POINT_CASES[0].model_copy(update={"id": "a_case_of_the_test"})
    extended = (*kill_point_cases.KILL_POINT_CASES, added)
    monkeypatch.setattr(kill_point_cases, "KILL_POINT_CASES", extended)
    monkeypatch.setattr(documents, "KILL_POINT_CASES", extended)


def _one_more_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    added = settings.SETTINGS[0].model_copy(update={"name": "FACTORY_A_SETTING_OF_THE_TEST"})
    monkeypatch.setattr(settings, "SETTINGS", (*settings.SETTINGS, added))


@pytest.mark.parametrize(
    "extend",
    [
        pytest.param(_one_more_stop, id="stop"),
        pytest.param(_one_more_kill_point, id="kill-point"),
        pytest.param(_one_more_setting, id="setting"),
    ],
)
def test_the_minimal_documents_follow_one_more_row_of_the_codes_tables(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    extend: Callable[[pytest.MonkeyPatch], None],
) -> None:
    extend(monkeypatch)

    root = minimal_documents(tmp_path / "root")

    _passes(root, capsys)


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("docs/project-guide/added.md", id="existing-folder"),
        pytest.param("docs/a-new-folder/deeper/added.md", id="new-subfolder"),
    ],
)
def test_added_files_are_committed_and_tracked(tmp_path: Path, path: str) -> None:
    root = minimal_documents(tmp_path / "root")

    add_and_commit(root, {path: "# Added\n\nA page.\n"})

    assert run_git(root, "status", "--porcelain") == ""
    assert run_git(root, "ls-files", "--error-unmatch", path) == f"{path}\n"
