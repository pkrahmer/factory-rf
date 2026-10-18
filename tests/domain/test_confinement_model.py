"""The rules of one confined run: absolute folders, files and temporary folder."""

import pytest
from pydantic import ValidationError

from factory.domain.confinement import Confinement

ABSOLUTE = {"folders": ["/a/b"], "files": ["/a/f.txt"], "temporary_directory": "/r/run"}


@pytest.mark.parametrize(
    ("field", "value", "valid"),
    [
        pytest.param("folders", ["/a/b"], True, id="all-absolute"),
        pytest.param("folders", ["a/b"], False, id="relative-folder"),
        pytest.param("files", ["f.txt"], False, id="relative-file"),
        pytest.param("temporary_directory", "run", False, id="relative-temporary-folder"),
    ],
)
def test_a_relative_path_in_any_field_is_refused(
    field: str, value: str | list[str], *, valid: bool
) -> None:
    data = {**ABSOLUTE, field: value}

    if valid:
        confinement = Confinement.model_validate(data)
        assert str(confinement.temporary_directory) == "/r/run"
    else:
        with pytest.raises(ValidationError):
            Confinement.model_validate(data)
