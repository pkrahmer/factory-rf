"""The documents command prints the settings findings of the operator guide."""

from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.shared.domain.settings import SETTINGS
from support.check_documents_support import drop_settings_row, write_checked_list

_DROPPED = SETTINGS[0].name


def _lines_naming(output: str, name: str) -> list[str]:
    return [line for line in output.splitlines() if name in line]


def test_settings_findings_are_printed_without_changing_the_exit_status(
    minimal: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_checked_list(minimal, [])
    status_with_row = main(["--root", str(minimal)])
    output_with_row = capsys.readouterr().out
    drop_settings_row(minimal, _DROPPED)

    status_without_row = main(["--root", str(minimal)])
    output_without_row = capsys.readouterr().out

    assert _lines_naming(output_with_row, _DROPPED) == []
    assert _lines_naming(output_without_row, _DROPPED) != []
    assert status_without_row == status_with_row
