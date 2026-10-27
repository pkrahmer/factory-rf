"""The committed schemas equal their generation; the pipeline definition names no `tool_paths`."""

from collections.abc import Callable

import pytest

from contract_support import committed_is_generated, schemas_naming
from factory.domain.contract import CONTRACT


def _no_tool_paths() -> None:
    assert "pipeline-definition.schema.json" not in schemas_naming("tool_paths")


@pytest.mark.parametrize(
    "check",
    [
        *[pytest.param(committed_is_generated(entry), id=entry.name) for entry in CONTRACT],
        pytest.param(_no_tool_paths, id="no-tool-paths"),
    ],
)
def test_the_committed_schemas_are_generated_and_the_pipeline_definition_has_no_tool_paths(
    check: Callable[[], None],
) -> None:
    check()
