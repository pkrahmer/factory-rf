"""The records contract at version 2.0: the pipeline definition without `tool_paths`."""

from collections.abc import Callable

import pytest

from contract_support import committed_is_generated, schemas_naming
from factory.domain.contract import CONTRACT, RECORDS_CONTRACT


def _version() -> None:
    assert RECORDS_CONTRACT == "4.0"


def _no_tool_paths() -> None:
    assert "pipeline-definition.schema.json" not in schemas_naming("tool_paths")


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_version, id="version"),
        *[pytest.param(committed_is_generated(entry, "4.0"), id=entry.name) for entry in CONTRACT],
        pytest.param(_no_tool_paths, id="no-tool-paths"),
    ],
)
def test_the_records_contract_is_at_version_2_without_tool_paths(
    check: Callable[[], None],
) -> None:
    check()
