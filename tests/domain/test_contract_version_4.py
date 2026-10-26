"""The records contract at version 4.0: the stall reasons without `left_branch`."""

from collections.abc import Callable

import pytest

from contract_support import committed_is_generated, schemas_naming
from factory.domain.contract import CONTRACT, RECORDS_CONTRACT


def _version() -> None:
    assert RECORDS_CONTRACT == "4.0"


def _no_left_branch() -> None:
    assert schemas_naming("left_branch") == []


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_version, id="version"),
        *[pytest.param(committed_is_generated(entry, "4.0"), id=entry.name) for entry in CONTRACT],
        pytest.param(_no_left_branch, id="no-left-branch"),
    ],
)
def test_the_records_contract_is_at_version_4_without_left_branch(
    check: Callable[[], None],
) -> None:
    check()
