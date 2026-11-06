"""The documents command prints the settings findings of the operator guide."""

from pathlib import Path

import pytest

from factory.entry.check_documents import main

_INSTALL = "docs/operator-guide/install.md"
_DROPPED = "FACTORY_ZFS"


def _drop_row(root: Path, name: str) -> None:
    path = root / _INSTALL
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if not line.startswith(f"| `{name}` |")]
    assert len(kept) == len(lines) - 1
    path.write_text("".join(kept), encoding="utf-8")


def _lines_naming(output: str, name: str) -> list[str]:
    return [line for line in output.splitlines() if name in line]


def test_settings_findings_are_printed_without_changing_the_exit_status(
    documents: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status_with_row = main(["--root", str(documents)])
    output_with_row = capsys.readouterr().out
    _drop_row(documents, _DROPPED)

    status_without_row = main(["--root", str(documents)])
    output_without_row = capsys.readouterr().out

    assert _lines_naming(output_with_row, _DROPPED) == []
    assert _lines_naming(output_without_row, _DROPPED) != []
    assert status_without_row == status_with_row
