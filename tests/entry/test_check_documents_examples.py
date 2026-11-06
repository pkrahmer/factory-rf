"""The documents command's report of the examples: the skipped blocks and the time line."""

import re
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.shared.domain.documents import CHECKED_DOCUMENTS, README
from support.check_documents_support import REPORT_HEADING, TIME_LINE, line_of
from support.document_texts import FENCE, clean_texts, readme, write_documents
from support.minimal_documents_support import add_and_commit

SHARED = "docs/project-guide/shared.md"
NO_COMMAND = "the example has no command"
PRINTED = re.compile(rf"{re.escape(SHARED)}:\d+: the example printed .*")

SKIPPED_BLOCKS = "\n".join(
    [
        f"{FENCE}console vm",
        "$ factory status",
        "...",
        FENCE,
        "",
        f"{FENCE}console",
        "$ make check",
        "check: green",
        FENCE,
    ]
)


def test_the_report_lists_every_skipped_block_and_ends_with_the_time_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    texts = clean_texts()
    text = readme(suffix=SKIPPED_BLOCKS)
    texts[README] = text
    write_documents(tmp_path, texts)

    status = main(["--root", str(tmp_path)])

    lines = capsys.readouterr().out.splitlines()
    vm = line_of(text, f"{FENCE}console vm")
    suite = line_of(text, f"{FENCE}console")
    assert f"{README}:{vm}: not run (vm)" in lines
    assert f"{README}:{suite}: not run (suite)" in lines
    assert re.fullmatch(TIME_LINE, lines[-1])
    assert status == 0


def test_an_examples_finding_comes_before_the_skipped_blocks_and_does_not_block(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    blocks = "\n".join(
        [
            f"{FENCE}console fixture=nowhere",
            "$ echo hi",
            "hi",
            FENCE,
            "",
            f"{FENCE}console vm",
            "$ factory status",
            "...",
            FENCE,
        ]
    )
    texts = clean_texts()
    text = readme(suffix=blocks)
    texts[README] = text
    write_documents(tmp_path, texts)

    status = main(["--root", str(tmp_path)])

    lines = capsys.readouterr().out.splitlines()
    finding = f"{README}:{line_of(text, f'{FENCE}console fixture=nowhere')}: no fixture nowhere"
    skipped = f"{README}:{line_of(text, f'{FENCE}console vm')}: not run (vm)"
    assert finding in lines
    assert skipped in lines
    assert lines.index(finding) < lines.index(skipped)
    assert re.fullmatch(TIME_LINE, lines[-1])
    assert status == 0


def _append_step(root: Path, fence_indent: str, body: list[str], *, listed: bool) -> int:
    """Append a numbered step with a `console` block to the shared page; its fence line."""
    text = (root / SHARED).read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    step = ["", "1. Run it:", "", f"{fence_indent}{FENCE}console", *body, f"{fence_indent}{FENCE}"]
    files = {SHARED: text + "\n".join(step) + "\n"}
    files[CHECKED_DOCUMENTS] = f"{SHARED}\n" if listed else ""
    add_and_commit(root, files)
    return line_of(files[SHARED], f"{fence_indent}{FENCE}console")


@pytest.mark.parametrize(
    "fence_indent",
    [pytest.param("", id="column-0"), pytest.param("   ", id="indented")],
)
def test_a_console_block_without_a_command_is_a_finding_at_its_fence(
    minimal: Path, capsys: pytest.CaptureFixture[str], fence_indent: str
) -> None:
    fence_line = _append_step(minimal, fence_indent, [f"{fence_indent}hi"], listed=False)

    main(["--root", str(minimal)])

    lines = capsys.readouterr().out.splitlines()
    assert f"{SHARED}:{fence_line}: {NO_COMMAND}" in lines


@pytest.mark.parametrize(
    ("body", "listed"),
    [
        pytest.param(["   hi"], True, id="no-command-listed"),
        pytest.param(["   hi"], False, id="no-command-not-listed"),
        pytest.param(["   $ echo one", "   two"], False, id="mismatch-not-listed"),
    ],
)
def test_an_example_finding_blocks_in_a_listed_file_and_is_reported_in_any_other(
    minimal: Path,
    capsys: pytest.CaptureFixture[str],
    body: list[str],
    listed: bool,
) -> None:
    _append_step(minimal, "   ", body, listed=listed)

    status = main(["--root", str(minimal)])

    lines = capsys.readouterr().out.splitlines()
    marked = [
        index
        for index, line in enumerate(lines)
        if line.startswith(f"{SHARED}:") and (NO_COMMAND in line or PRINTED.fullmatch(line))
    ]
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
    ("body", "listed", "outcome"),
    [
        pytest.param(["   $ echo hi", "   hi"], False, (re.compile(TIME_LINE), 0), id="match"),
        pytest.param(["   $ echo one", "   two"], True, (PRINTED, 1), id="mismatch-listed"),
    ],
)
def test_an_indented_example_is_run_and_a_mismatch_in_a_listed_file_blocks(
    minimal: Path,
    capsys: pytest.CaptureFixture[str],
    body: list[str],
    listed: bool,
    outcome: tuple[re.Pattern[str], int],
) -> None:
    only_line, status = outcome
    _append_step(minimal, "   ", body, listed=listed)

    result = main(["--root", str(minimal)])

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert only_line.fullmatch(lines[0])
    assert result == status
