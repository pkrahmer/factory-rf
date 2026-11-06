"""The documents command runs a real example in the git repository of the minimal documents."""

import re
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.hosting.adapters.instance_fixture import INSTANCE_NAME
from factory.shared.domain.documents import INSTANCE_FIXTURE
from factory.shared.domain.settings import INSTANCE_VARIABLE
from support.check_documents_support import (
    REPORT_HEADING,
    append_block,
    findings_from,
    write_checked_list,
)

LISTED = "docs/project-guide/machine.md"
UNLISTED = "docs/project-guide/shared.md"


def _append_example(root: Path, document: str, command: str, output: str) -> int:
    """List only the listed page, append a `console` block to `document`; the block's line."""
    write_checked_list(root, [LISTED] if document == LISTED else [])
    return append_block(root, document, "console", [f"$ {command}", output])


@pytest.mark.parametrize("document", [UNLISTED, LISTED], ids=["unlisted", "listed"])
def test_a_matching_example_in_a_copied_document_gives_no_finding(
    minimal: Path, capsys: pytest.CaptureFixture[str], document: str
) -> None:
    first_line = _append_example(minimal, document, "echo hi", "hi")

    main(["--root", str(minimal)])

    lines = capsys.readouterr().out.splitlines()
    assert findings_from(lines, document, first_line) == []


@pytest.mark.parametrize(
    ("document", "blocks", "exit_status"),
    [
        pytest.param(UNLISTED, False, 0, id="unlisted-reported"),
        pytest.param(LISTED, True, 1, id="listed-fails"),
    ],
)
def test_a_wrong_example_in_a_copied_document_fails_only_a_listed_one(
    minimal: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    document: str,
    blocks: bool,
    exit_status: int,
) -> None:
    first_line = _append_example(minimal, document, "echo one", "two")

    status = main(["--root", str(minimal)])

    printed = capsys.readouterr().out.splitlines()
    lines = [line for line in printed if not line.endswith(" does not exist")]
    findings = findings_from(lines, document, first_line)
    assert len(findings) == 1
    assert re.fullmatch(rf"{re.escape(document)}:\d+: the example printed one", findings[0])
    report = lines.index(REPORT_HEADING) if REPORT_HEADING in lines else len(lines)
    assert (lines.index(findings[0]) < report) is blocks
    assert status == exit_status


@pytest.mark.parametrize(
    ("output", "findings"),
    [
        pytest.param(INSTANCE_NAME, [], id="matching"),
        pytest.param("another", [f"the example printed {INSTANCE_NAME}"], id="wrong"),
    ],
)
def test_an_instance_example_runs_in_a_valid_instance(
    minimal: Path, capsys: pytest.CaptureFixture[str], *, output: str, findings: list[str]
) -> None:
    write_checked_list(minimal, [LISTED])
    first_line = append_block(
        minimal,
        LISTED,
        f"console fixture={INSTANCE_FIXTURE}",
        [f"$ printenv {INSTANCE_VARIABLE}", output],
    )

    status = main(["--root", str(minimal)])

    lines = findings_from(capsys.readouterr().out.splitlines(), LISTED, first_line)
    assert [line.split(": ", 1)[1] for line in lines] == findings
    assert status == (1 if findings else 0)
