"""The name check: exactly the texts the `Name` type accepts."""

import pytest

from factory.domain.identifiers import is_name


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("coder", True),
        ("smoke-tester", True),
        ("a1", True),
        ("Coder", False),
        ("README", False),
        ("1coder", False),
        ("co der", False),
        ("coder.md", False),
        ("", False),
    ],
)
def test_is_name_accepts_exactly_the_names(text: str, expected: bool) -> None:
    assert is_name(text) is expected
