"""The tree id: 40 lower-case hex characters, the pattern of a commit id."""

import pytest
from pydantic import TypeAdapter, ValidationError

from factory.domain.git import TreeId

TREE_ID: TypeAdapter[str] = TypeAdapter(TreeId)


@pytest.mark.parametrize(
    ("value", "accepted"),
    [
        pytest.param("a" * 40, True, id="a40"),
        pytest.param("0" * 40, True, id="zero40"),
        pytest.param("a" * 39, False, id="a39"),
        pytest.param("a" * 41, False, id="a41"),
        pytest.param("A" * 40, False, id="upper"),
        pytest.param("g" * 40, False, id="not-hex"),
    ],
)
def test_a_tree_id_is_forty_lower_case_hex_characters(value: str, accepted: bool) -> None:
    if accepted:
        assert TREE_ID.validate_python(value) == value
    else:
        with pytest.raises(ValidationError):
            TREE_ID.validate_python(value)
