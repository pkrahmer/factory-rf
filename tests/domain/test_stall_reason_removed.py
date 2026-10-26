"""The stall reasons without `left_branch`: the value and its sentence are gone, the rest stay."""

import ast
from collections.abc import Callable
from pathlib import Path
from typing import get_args

import pytest

import factory.domain.post_texts
from factory.domain.journal import StallReason
from factory.domain.post_texts import stall_cause
from source_search import string_literals

REMOVED = "left_branch"


def _not_a_reason() -> None:
    assert REMOVED not in get_args(StallReason)


def _no_sentence() -> None:
    path = Path(factory.domain.post_texts.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert REMOVED not in string_literals(tree)


def _has_its_sentence(reason: StallReason) -> Callable[[], None]:
    def check() -> None:
        assert stall_cause(reason) != ""

    return check


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_not_a_reason, id="not-a-reason"),
        pytest.param(_no_sentence, id="no-sentence"),
        *[pytest.param(_has_its_sentence(reason), id=reason) for reason in get_args(StallReason)],
    ],
)
def test_left_branch_is_no_stall_reason_and_every_other_keeps_its_sentence(
    check: Callable[[], None],
) -> None:
    check()
