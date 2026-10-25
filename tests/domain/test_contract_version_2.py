"""The records contract at version 2.0: the pipeline definition without `tool_paths`."""

from collections.abc import Callable

import pytest

from factory.domain.contract import (
    CONTRACT,
    CONTRACT_KEY,
    RECORDS_CONTRACT,
    ContractEntry,
    contract_schema,
    schema_file_name,
)
from source_search import SRC

SCHEMAS = SRC / "contract"


def _committed(entry: ContractEntry) -> str:
    return (SCHEMAS / schema_file_name(entry)).read_text(encoding="utf-8")


def _version() -> None:
    assert RECORDS_CONTRACT == "3.0"


def _schema_check(entry: ContractEntry) -> Callable[[], None]:
    def check() -> None:
        text = _committed(entry)
        assert f'"{CONTRACT_KEY}": "3.0"' in text
        assert text == contract_schema(entry)

    return check


def _no_tool_paths() -> None:
    assert "tool_paths" not in (SCHEMAS / "pipeline-definition.schema.json").read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_version, id="version"),
        *(pytest.param(_schema_check(entry), id=entry.name) for entry in CONTRACT),
        pytest.param(_no_tool_paths, id="no-tool-paths"),
    ],
)
def test_the_records_contract_is_at_version_2_without_tool_paths(
    check: Callable[[], None],
) -> None:
    check()
