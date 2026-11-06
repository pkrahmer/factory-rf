"""The documents command's report of the examples: the skipped blocks and the time line."""

import re
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.shared.domain.documents import README
from support.check_documents_support import TIME_LINE, line_of
from support.document_texts import FENCE, clean_texts, readme, write_documents

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
