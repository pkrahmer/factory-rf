"""The committed schemas equal their generation, and no schema names `nested_repository`."""

from collections.abc import Callable

import pytest

from contract_support import committed_is_generated, schemas_naming
from factory.domain.contract import CONTRACT


def _no_nested_repository() -> None:
    assert schemas_naming("nested_repository") == []


@pytest.mark.parametrize(
    "check",
    [
        *[pytest.param(committed_is_generated(entry), id=entry.name) for entry in CONTRACT],
        pytest.param(_no_nested_repository, id="no-nested-repository"),
    ],
)
def test_the_committed_schemas_are_generated_and_name_no_nested_repository(
    check: Callable[[], None],
) -> None:
    check()
