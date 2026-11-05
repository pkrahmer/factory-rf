"""The records contract at version 4.2: the cost record's optional machine measures."""

from collections.abc import Callable

import pytest

from factory.shared.domain.contract import CONTRACT, RECORDS_CONTRACT
from support.contract_support import committed_is_generated, schemas_naming


def _version() -> None:
    assert RECORDS_CONTRACT == "4.4"


def _machine_named() -> None:
    assert schemas_naming("memory_peak_since_boot_bytes") == ["cost-record.schema.json"]


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_version, id="version"),
        *[pytest.param(committed_is_generated(entry, "4.4"), id=entry.name) for entry in CONTRACT],
        pytest.param(_machine_named, id="machine-in-the-cost-record"),
    ],
)
def test_the_records_contract_is_at_version_4_2_with_the_machine_measures(
    check: Callable[[], None],
) -> None:
    check()
