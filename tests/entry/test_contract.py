"""The contract command: it writes the records' JSON Schemas, and the committed ones are current."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

import factory
import factory.entry.contract
from contract_support import USAGE, WRITTEN, MainRow
from factory.domain.contract import CONTRACT, ContractEntry, contract_schema, schema_file_name
from factory.entry.contract import main, write_contract

COMMITTED = Path(factory.__file__).parent / "contract"
SCHEMA_FILES = [
    "work-item-state.schema.json",
    "acceptance-state.schema.json",
    "cost-record.schema.json",
    "stop-record.schema.json",
    "pipeline-definition.schema.json",
]
OTHER_TEXT = "not a schema\n"


def _nothing(folder: Path) -> None:
    del folder


def _other_file(folder: Path) -> None:
    folder.mkdir()
    (folder / "other.txt").write_text(OTHER_TEXT, encoding="utf-8")


def _stale_schema(folder: Path) -> None:
    folder.mkdir()
    (folder / "stop-record.schema.json").write_text("{}", encoding="utf-8")


@pytest.mark.parametrize(
    "before",
    [
        pytest.param(_nothing, id="no-folder"),
        pytest.param(_other_file, id="other-file"),
        pytest.param(_stale_schema, id="stale-schema"),
    ],
)
def test_write_contract_writes_every_schema_into_the_folder(
    tmp_path: Path, before: Callable[[Path], None]
) -> None:
    folder = tmp_path / "out"
    before(folder)
    other_before = (folder / "other.txt").is_file()

    paths = write_contract(folder)

    assert paths == [folder / schema_file_name(entry) for entry in CONTRACT]
    for entry in CONTRACT:
        assert (folder / schema_file_name(entry)).read_text(encoding="utf-8") == contract_schema(
            entry
        )
    if other_before:
        assert (folder / "other.txt").read_text(encoding="utf-8") == OTHER_TEXT


@pytest.mark.parametrize("name", [*SCHEMA_FILES, None], ids=[*SCHEMA_FILES, "no-other-file"])
def test_the_committed_schemas_are_the_generated_ones(tmp_path: Path, name: str | None) -> None:
    write_contract(tmp_path)

    if name is None:
        assert sorted(path.name for path in COMMITTED.iterdir()) == sorted(SCHEMA_FILES)
    else:
        assert (COMMITTED / name).read_bytes() == (tmp_path / name).read_bytes()


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(MainRow(lambda tmp: [str(tmp)], lambda tmp: tmp, WRITTEN, "", 0), id="folder"),
        pytest.param(
            MainRow(lambda _: [], lambda tmp: tmp / "default", WRITTEN, "", 0), id="default"
        ),
        pytest.param(MainRow(lambda tmp: [str(tmp), "x"], None, "", USAGE, 2), id="two-arguments"),
    ],
)
def test_main_writes_the_schemas_into_the_folder_given_or_the_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    row: MainRow,
) -> None:
    assert factory.entry.contract.CONTRACT_FOLDER == COMMITTED
    monkeypatch.setattr(factory.entry.contract, "CONTRACT_FOLDER", tmp_path / "default")

    returned = main(row.arguments(tmp_path))

    captured = capsys.readouterr()
    assert returned == row.code
    assert captured.out == row.out
    assert captured.err == row.err
    if row.written is None:
        assert list(tmp_path.iterdir()) == []
    else:
        written = row.written(tmp_path)
        assert sorted(path.name for path in written.iterdir()) == sorted(SCHEMA_FILES)


@pytest.mark.parametrize("entry", CONTRACT, ids=[entry.name for entry in CONTRACT])
def test_a_committed_schema_requires_exactly_the_required_fields(entry: ContractEntry) -> None:
    schema = json.loads((COMMITTED / schema_file_name(entry)).read_text(encoding="utf-8"))
    fields = entry.model.model_fields
    required = {name for name, field in fields.items() if field.is_required()}

    assert set(schema.get("required", [])) == required
    assert set(fields) <= set(schema["properties"])
