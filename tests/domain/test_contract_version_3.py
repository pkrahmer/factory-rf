"""The records contract at version 3.0: the stall reasons without `nested_repository`."""

from collections.abc import Callable

import pytest

from contract_support import committed_is_generated, schemas_naming
from factory.domain.contract import CONTRACT, RECORDS_CONTRACT


def _version() -> None:
    assert RECORDS_CONTRACT == "4.0"


def _no_nested_repository() -> None:
    assert schemas_naming("nested_repository") == []


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_version, id="version"),
        *[pytest.param(committed_is_generated(entry, "4.0"), id=entry.name) for entry in CONTRACT],
        pytest.param(_no_nested_repository, id="no-nested-repository"),
    ],
)
def test_the_records_contract_is_at_version_3_without_nested_repository(
    check: Callable[[], None],
) -> None:
    check()
