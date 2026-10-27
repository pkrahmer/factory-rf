"""The documents command: the findings of the four documents under a root as lines."""

import sys
from pathlib import Path

import pytest

from check_documents_support import MISSING_LINES
from document_texts import clean_texts, operator_guide, project_guide, readme, write_documents
from factory.adapters.process import ProcessRequest, run_process
from factory.domain.documents import (
    DECISION_LOG,
    OPERATOR_GUIDE,
    OPERATOR_GUIDE_SECTIONS,
    PROJECT_GUIDE,
    PROJECT_GUIDE_SECTIONS,
    README,
)
from factory.entry.check_documents import main


def test_clean_documents_print_documents_ok_and_return_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_documents(tmp_path, clean_texts())

    status = main(["--root", str(tmp_path)])

    assert capsys.readouterr().out == "documents ok\n"
    assert status == 0


def test_each_finding_prints_one_line_in_order_and_returns_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    texts = clean_texts()
    texts[README] = None
    texts[OPERATOR_GUIDE] = operator_guide(
        sections=[name for name in OPERATOR_GUIDE_SECTIONS if name != "Install"]
    )
    texts[PROJECT_GUIDE] = project_guide(
        sections=[name for name in PROJECT_GUIDE_SECTIONS if name != "Kill points"]
    )
    texts[DECISION_LOG] = "  \n"
    write_documents(tmp_path, texts)

    status = main(["--root", str(tmp_path)])

    assert capsys.readouterr().out == (
        "README.md: missing\n"
        "docs/operator-guide.md: section 'Install' is missing\n"
        "docs/project-guide/README.md: section 'Kill points' is missing\n"
        "docs/decisions.md: empty\n"
    )
    assert status == 1


def test_without_a_root_the_current_directory_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_documents(tmp_path, clean_texts())
    monkeypatch.chdir(tmp_path)

    status = main([])

    assert capsys.readouterr().out == "documents ok\n"
    assert status == 0


@pytest.mark.parametrize(
    ("clean", "exit_status", "output"),
    [(True, 0, "documents ok\n"), (False, 1, MISSING_LINES)],
    ids=["clean", "empty-directory"],
)
def test_the_module_run_as_a_process_exits_with_the_status_of_main(
    tmp_path: Path, clean: bool, exit_status: int, output: str
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    if clean:
        write_documents(root, clean_texts())

    result = run_process(
        ProcessRequest(
            argv=[sys.executable, "-m", "factory.entry.check_documents", "--root", str(root)],
            cwd=tmp_path,
        )
    )

    assert result.exit_status == exit_status
    assert result.stdout == output


def test_documents_are_read_as_utf_8(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    texts = clean_texts()
    texts[README] = readme(suffix="The café opens at noon — every day.")
    write_documents(tmp_path, texts)

    status = main(["--root", str(tmp_path)])

    assert capsys.readouterr().out == "documents ok\n"
    assert status == 0
