"""The documents command's report of the examples: the skipped blocks and the time line."""

import re
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.shared.domain.documents import README
from support.check_documents_support import TIME_LINE
from support.document_texts import clean_texts, readme, write_documents

FENCE = "```"
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


def _line_of(text: str, line: str) -> int:
    return text.split("\n").index(line) + 1


def test_the_report_lists_every_skipped_block_and_ends_with_the_time_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    texts = clean_texts()
    text = readme(suffix=SKIPPED_BLOCKS)
    texts[README] = text
    write_documents(tmp_path, texts)

    status = main(["--root", str(tmp_path)])

    lines = capsys.readouterr().out.splitlines()
    vm = _line_of(text, f"{FENCE}console vm")
    suite = _line_of(text, f"{FENCE}console")
    assert f"{README}:{vm}: not run (vm)" in lines
    assert f"{README}:{suite}: not run (suite)" in lines
    assert re.fullmatch(TIME_LINE, lines[-1])
    assert status == 0
