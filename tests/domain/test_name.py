"""Names: lower-case words joined by hyphens, starting with a letter."""

import pytest
from pydantic import TypeAdapter, ValidationError

from factory.domain.identifiers import Name

NAME = TypeAdapter(Name)


@pytest.mark.parametrize(
    ("text", "accepted"),
    [
        ("coder", True),
        ("smoke-tester", True),
        ("Coder", False),
        ("1x", False),
        ("a b", False),
        ("", False),
    ],
)
def test_name_accepts_lower_case_hyphenated_words_only(text: str, accepted: bool) -> None:
    if accepted:
        assert NAME.validate_python(text) == text
    else:
        with pytest.raises(ValidationError):
            NAME.validate_python(text)
