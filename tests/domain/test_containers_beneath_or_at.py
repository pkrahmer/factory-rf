"""`beneath_or_at` lives with the container rules and answers as it did before its move."""

import pytest

from factory.domain.containers import beneath_or_at


@pytest.mark.parametrize(
    ("relative", "above", "expected"),
    [
        pytest.param("a/b", "a/b", True, id="equal"),
        pytest.param("a/b/c", "a/b", True, id="beneath"),
        pytest.param("ab", "a", False, id="sibling-with-the-same-prefix"),
        pytest.param("c/d", "a/b", False, id="unrelated"),
        pytest.param("", "", True, id="empty-above-empty"),
        pytest.param("a", "", False, id="empty-above-relative"),
        pytest.param("/a", "", True, id="empty-above-absolute"),
    ],
)
def test_beneath_or_at_gives_the_answers_it_gave_in_agent_home(
    relative: str, above: str, *, expected: bool
) -> None:
    assert beneath_or_at(relative, above) is expected
