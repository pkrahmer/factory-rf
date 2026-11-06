"""The documents command blocks on the new checks' findings in the listed files only."""

import re
import shutil
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.pipeline.domain.stop_table import STOP_TABLE
from factory.shared.domain.documents import (
    CHECKED_DOCUMENTS,
    OPERATOR_INSTALL,
    OPERATOR_STOPS,
    PROJECT_GUIDE,
    read_checked_documents,
)
from support.check_documents_support import REPORT_HEADING, TIME_LINE, line_of
from support.document_texts import (
    FENCE,
    clean_texts,
    operator_install,
    operator_stops,
    project_guide,
    write_documents,
)
from support.git_support import commit_all, run_git
from support.operator_support import ROOT

STYLE = "docs/project-guide/style.md"
GLOSSARY = "docs/project-guide/glossary.md"
MISSING_NAME = "factory.nothing_here"
OTHER_MISSING_NAME = "factory.still_missing"
UNKNOWN_SETTING = "FACTORY_NOTHING_HERE"
SETTINGS_TABLE = f"| Variable | Meaning |\n|---|---|\n| `{UNKNOWN_SETTING}` | nothing |\n"
_NOT_COPIED = (
    ".git",
    ".venv",
    ".cache",
    ".ruff_cache",
    ".mypy_cache",
    ".pytest_cache",
    ".reports",
    "mutants",
    "__pycache__",
)
EXAMPLE_BLOCK = f"{FENCE}console fixture=nowhere\n$ echo hi\nhi\n{FENCE}"
VM_BLOCK = f"{FENCE}console vm\n$ factory status\n...\n{FENCE}"


def _guide_page(body: str) -> str:
    return f"# A page\n\n{body}\n\nThe end.\n"


def _write(root: Path, extra: dict[str, str], listed: list[str] | None) -> None:
    texts = clean_texts()
    texts.update(extra)
    if listed is not None:
        texts[CHECKED_DOCUMENTS] = "".join(f"{path}\n" for path in listed)
    write_documents(root, texts)


def _run(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, list[str]]:
    status = main(["--root", str(root)])
    return status, [line.strip() for line in capsys.readouterr().out.splitlines()]


def _name_finding(document: str, text: str, name: str) -> str:
    return f"{document}:{line_of(text, f'See `{name}`.')}: {name} does not exist"


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            (STYLE, _guide_page(f"See `{MISSING_NAME}`."), f"{MISSING_NAME} does not exist"),
            id="name",
        ),
        pytest.param(
            (
                OPERATOR_INSTALL,
                operator_install(suffix=SETTINGS_TABLE),
                f"setting {UNKNOWN_SETTING} is named by the guide",
            ),
            id="settings",
        ),
        pytest.param((STYLE, _guide_page(EXAMPLE_BLOCK), "no fixture nowhere"), id="example"),
    ],
)
@pytest.mark.parametrize("listed", [True, False], ids=["listed", "not-listed"])
def test_a_new_finding_blocks_in_a_listed_file_and_is_reported_in_any_other(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case: tuple[str, str, str],
    listed: bool,
) -> None:
    document, text, marker = case
    _write(tmp_path, {document: text}, [document] if listed else [PROJECT_GUIDE])

    status, lines = _run(tmp_path, capsys)

    marked = [index for index, line in enumerate(lines) if marker in line]
    assert marked
    if listed:
        assert status == 1
        assert REPORT_HEADING not in lines
        assert not any(re.fullmatch(TIME_LINE, line) for line in lines)
    else:
        assert status == 0
        assert REPORT_HEADING in lines
        assert min(marked) > lines.index(REPORT_HEADING)
        assert re.fullmatch(TIME_LINE, lines[-1])


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            (OPERATOR_STOPS, operator_stops(without_stop=STOP_TABLE[0].id), STOP_TABLE[0].id),
            id="missing-stop-row",
        ),
        pytest.param(
            (OPERATOR_INSTALL, operator_install(sections=("Install",)), "Configuration"),
            id="missing-section",
        ),
        pytest.param((STYLE, _guide_page("Every ticket waits."), "ticket"), id="old-word"),
    ],
)
@pytest.mark.parametrize("listed", [True, False], ids=["listed", "not-listed"])
def test_a_finding_of_the_checks_of_before_fails_for_every_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case: tuple[str, str, str],
    listed: bool,
) -> None:
    document, text, message = case
    _write(tmp_path, {document: text}, [document] if listed else [PROJECT_GUIDE])

    status, lines = _run(tmp_path, capsys)

    assert status == 1
    assert any(line.startswith(f"{document}: ") and message in line for line in lines)
    assert REPORT_HEADING not in lines
    assert not any(re.fullmatch(TIME_LINE, line) for line in lines)


def test_todays_documents_with_the_first_list_give_a_report_and_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    copy = tmp_path / "checkout"
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(*_NOT_COPIED))
    (copy / CHECKED_DOCUMENTS).write_text(f"{STYLE}\n{GLOSSARY}\n", encoding="utf-8")
    run_git(copy, "init", "-q")
    commit_all(copy, "The copied repository")

    status, lines = _run(copy, capsys)

    assert REPORT_HEADING in lines
    assert re.fullmatch(TIME_LINE, lines[-1])
    assert status == 0


@pytest.mark.parametrize(
    "listed",
    [
        pytest.param("docs/project-guide/nothing-here.md", id="missing-path"),
        pytest.param("docs/decisions.md", id="not-a-checked-document"),
    ],
)
def test_a_listed_path_that_is_no_document_of_the_check_is_one_blocking_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], listed: str
) -> None:
    _write(tmp_path, {}, [listed])

    status, lines = _run(tmp_path, capsys)

    assert status == 1
    assert len(lines) == 1
    assert listed in lines[0]


def test_the_output_is_the_blocking_findings_then_the_report_and_nothing_more(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    style = _guide_page(f"See `{MISSING_NAME}`.")
    glossary = _guide_page(f"See `{OTHER_MISSING_NAME}`.")
    _write(tmp_path, {STYLE: style, GLOSSARY: glossary}, [STYLE])

    _, lines = _run(tmp_path, capsys)

    assert lines == [
        _name_finding(STYLE, style, MISSING_NAME),
        REPORT_HEADING,
        _name_finding(GLOSSARY, glossary, OTHER_MISSING_NAME),
    ]


def test_the_failing_side_prints_one_line_per_blocking_finding_then_the_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    style = _guide_page(f"See `{MISSING_NAME}`.\n\nSee `{OTHER_MISSING_NAME}`.")
    glossary = _guide_page(f"See `{MISSING_NAME}`.")
    _write(tmp_path, {STYLE: style, GLOSSARY: glossary}, [STYLE])

    status, lines = _run(tmp_path, capsys)

    assert lines[:3] == [
        _name_finding(STYLE, style, MISSING_NAME),
        _name_finding(STYLE, style, OTHER_MISSING_NAME),
        REPORT_HEADING,
    ]
    assert not any(line.startswith("documents ok") for line in lines)
    assert status == 1


@pytest.mark.parametrize(
    "listed",
    [pytest.param([STYLE], id="nothing-to-report")],
)
def test_the_report_heading_is_left_out_when_there_is_nothing_to_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], listed: list[str]
) -> None:
    _write(tmp_path, {STYLE: _guide_page("Plain words.")}, listed)

    status, lines = _run(tmp_path, capsys)

    assert REPORT_HEADING not in lines
    assert re.fullmatch(TIME_LINE, lines[-1])
    assert status == 0


@pytest.mark.parametrize(
    ("planted", "files", "expected"),
    [
        pytest.param("`factory.env`", [], [], id="file-name-env"),
        pytest.param("`factory.local.env`", [], [], id="file-name-local-env"),
        pytest.param(
            "`tests/x.py::test_y`", [], ["tests/x.py does not exist"], id="node-id-missing"
        ),
        pytest.param("`tests/x.py::test_y`", ["tests/x.py"], [], id="node-id-existing"),
        pytest.param("`tests/x.py`", [], ["tests/x.py does not exist"], id="path-without-node"),
        pytest.param("`$HOME/a/b.txt`", [], [], id="shell-expression"),
        pytest.param("`$HOME/factory.nothing.here`", [], [], id="shell-expression-whole"),
        pytest.param(
            "`factory.shared.domain.yml_reader`",
            [],
            ["factory.shared.domain.yml_reader does not exist"],
            id="module-ending-like-an-extension",
        ),
    ],
)
def test_file_names_node_ids_and_shell_texts_are_read_exactly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    planted: str,
    files: list[str],
    expected: list[str],
) -> None:
    for name in files:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("", encoding="utf-8")
    text = project_guide(suffix=planted)
    _write(tmp_path, {PROJECT_GUIDE: text}, [PROJECT_GUIDE])

    _, lines = _run(tmp_path, capsys)

    line = line_of(text, planted)
    found = [entry for entry in lines if entry.endswith(" does not exist")]
    assert found == [f"{PROJECT_GUIDE}:{line}: {name}" for name in expected]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(
            f"# The checked documents\n\n{STYLE}\n\n# Rewritten next\n{GLOSSARY}\n",
            [STYLE, GLOSSARY],
            id="comment-and-blank-lines",
        ),
    ],
)
def test_a_comment_line_and_a_blank_line_give_no_entry(text: str, expected: list[str]) -> None:
    assert read_checked_documents(text) == expected


@pytest.mark.parametrize(
    "document",
    [pytest.param(STYLE, id="no-list-file")],
)
def test_without_a_list_file_every_new_finding_is_reported_and_none_blocks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], document: str
) -> None:
    text = _guide_page(f"See `{MISSING_NAME}`.")
    _write(tmp_path, {document: text}, None)

    status, lines = _run(tmp_path, capsys)

    finding = _name_finding(document, text, MISSING_NAME)
    assert finding in lines
    assert lines.index(REPORT_HEADING) < lines.index(finding)
    assert re.fullmatch(TIME_LINE, lines[-1])
    assert status == 0


@pytest.mark.parametrize("listed", [True, False], ids=["listed", "not-listed"])
def test_an_example_not_run_is_reported_after_the_reported_findings_and_never_blocks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], listed: bool
) -> None:
    style = _guide_page(VM_BLOCK)
    glossary = _guide_page(f"See `{MISSING_NAME}`.")
    _write(tmp_path, {STYLE: style, GLOSSARY: glossary}, [STYLE] if listed else [PROJECT_GUIDE])

    status, lines = _run(tmp_path, capsys)

    finding = _name_finding(GLOSSARY, glossary, MISSING_NAME)
    not_run = f"{STYLE}:{line_of(style, f'{FENCE}console vm')}: not run (vm)"
    assert lines.index(REPORT_HEADING) < lines.index(finding) < lines.index(not_run)
    assert re.fullmatch(TIME_LINE, lines[-1])
    assert status == 0
