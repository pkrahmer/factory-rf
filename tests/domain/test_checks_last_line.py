"""The last line of a make output: the recipe's own last line, make's messages skipped."""

import pytest

from factory.domain.checks import last_line


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        pytest.param(["boom", "make: *** [Makefile:3: sync] Error 1"], "boom", id="make-message"),
        pytest.param(["boom", "make[2]: Leaving directory '/x'"], "boom", id="sub-make-message"),
        pytest.param(["boom", ""], "boom", id="trailing-blank"),
        pytest.param(["first", "boom"], "boom", id="recipe-last-line"),
        pytest.param(["make: *** [Makefile:3: sync] Error 2", "make[1]: x"], "", id="make-only"),
        pytest.param([], "", id="no-lines"),
    ],
)
def test_the_last_line_is_the_recipes_own(lines: list[str], expected: str) -> None:
    assert last_line(lines) == expected
