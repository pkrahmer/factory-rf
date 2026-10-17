"""The preflight's stamp: the image the machine passed on and the commits of main it probed."""

import pytest
from pydantic import ValidationError

from factory.domain.preflight import PreflightStamp


@pytest.mark.parametrize("field", ["main_probed", "main_failed"])
@pytest.mark.parametrize(
    ("value", "accepted"),
    [
        ("a" * 40, True),
        (None, True),
        ("a" * 39, False),
        ("A" * 40, False),
        ("g" * 40, False),
    ],
    ids=["forty-hex", "none", "thirty-nine", "upper-case", "not-hex"],
)
def test_the_commit_fields_hold_a_commit_id_or_none(
    field: str, value: str | None, accepted: bool
) -> None:
    if accepted:
        stamp = PreflightStamp.model_validate({"image": "build-7", field: value})
        assert getattr(stamp, field) == value
    else:
        with pytest.raises(ValidationError):
            PreflightStamp.model_validate({"image": "build-7", field: value})
