"""Tests of the mask over the hidden values of a message."""

import pytest

from factory.domain.tokens import masked


@pytest.mark.parametrize(
    ("message", "hidden", "expected"),
    [
        pytest.param(
            "token tok-1 and s3 s3", ["tok-1", "s3"], "token *** and *** ***", id="every-occurrence"
        ),
        pytest.param("nothing here", ["tok-1"], "nothing here", id="no-occurrence"),
        pytest.param("a b", ["", "b"], "a ***", id="empty-value-left-out"),
        pytest.param("x", [], "x", id="no-values"),
    ],
)
def test_every_non_empty_hidden_value_is_replaced_by_the_mask(
    message: str, hidden: list[str], expected: str
) -> None:
    assert masked(message, hidden) == expected
