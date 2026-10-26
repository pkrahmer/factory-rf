"""The records contract at version 4.0: the stall reasons without `left_branch`."""

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


def _version() -> None:
    assert RECORDS_CONTRACT == "4.0"


def _committed_is_generated(entry: ContractEntry) -> Callable[[], None]:
    def check() -> None:
        text = (SCHEMAS / schema_file_name(entry)).read_text(encoding="utf-8")
        assert f'"{CONTRACT_KEY}": "4.0"' in text
        assert text == contract_schema(entry)

    return check


def _no_left_branch() -> None:
    named = [
        path.name
        for path in sorted(SCHEMAS.glob("*.schema.json"))
        if "left_branch" in path.read_text(encoding="utf-8")
    ]
    assert named == []


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_version, id="version"),
        *[pytest.param(_committed_is_generated(entry), id=entry.name) for entry in CONTRACT],
        pytest.param(_no_left_branch, id="no-left-branch"),
    ],
)
def test_the_records_contract_is_at_version_4_without_left_branch(
    check: Callable[[], None],
) -> None:
    check()
