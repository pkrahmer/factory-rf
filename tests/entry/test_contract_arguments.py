"""The contract command reads its arguments from `sys.argv` and creates missing parents."""

import sys
from pathlib import Path

import pytest

import factory.entry.contract
from contract_support import USAGE, WRITTEN, MainRow
from factory.domain.contract import CONTRACT, schema_file_name
from factory.entry.contract import main, write_contract

SCHEMA_NAMES = sorted(schema_file_name(entry) for entry in CONTRACT)


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(
            MainRow(
                lambda tmp: ["contract", str(tmp / "given")],
                lambda tmp: tmp / "given",
                WRITTEN,
                "",
                0,
            ),
            id="folder",
        ),
        pytest.param(
            MainRow(lambda _: ["contract"], lambda tmp: tmp / "default", WRITTEN, "", 0),
            id="no-folder",
        ),
        pytest.param(
            MainRow(lambda _: ["contract", "a", "b"], None, "", USAGE, 2), id="two-arguments"
        ),
    ],
)
def test_main_without_argv_reads_the_arguments_after_the_program_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    row: MainRow,
) -> None:
    default = tmp_path / "default"
    default.mkdir()
    monkeypatch.setattr(factory.entry.contract, "CONTRACT_FOLDER", default)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", row.arguments(tmp_path))

    returned = main()

    captured = capsys.readouterr()
    assert returned == row.code
    assert captured.out == row.out
    assert captured.err == row.err
    if row.written is None:
        assert [path for path in tmp_path.rglob("*") if path.is_file()] == []
        assert not (tmp_path / "a").exists()
        assert not (tmp_path / "b").exists()
    else:
        written = row.written(tmp_path)
        assert sorted(path.name for path in written.iterdir()) == SCHEMA_NAMES
        if written != default:
            assert list(default.iterdir()) == []


@pytest.mark.parametrize("a_exists", [False, True], ids=["no-parent", "parent-exists"])
def test_write_contract_creates_the_folder_and_its_missing_parents(
    tmp_path: Path, a_exists: bool
) -> None:
    if a_exists:
        (tmp_path / "a").mkdir()
    folder = tmp_path / "a" / "b"

    paths = write_contract(folder)

    assert paths == [folder / schema_file_name(entry) for entry in CONTRACT]
    for path in paths:
        assert path.is_file()
