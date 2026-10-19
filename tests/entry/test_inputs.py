"""A command's input file, read as UTF-8 text in one place."""

from pathlib import Path

import pytest

from factory.entry import check_duplicates
from factory.entry.inputs import UnreadableInput, read_input


@pytest.mark.parametrize(
    ("content", "text"),
    [
        pytest.param("killed ǁ text\n".encode(), "killed ǁ text\n", id="utf-8"),
        pytest.param(None, None, id="missing"),
        pytest.param(b"\xff\xfe", None, id="not-utf-8"),
    ],
)
def test_an_input_is_read_as_utf_8_or_reported_unreadable(
    tmp_path: Path, content: bytes | None, text: str | None
) -> None:
    path = tmp_path / "input.txt"
    if content is not None:
        path.write_bytes(content)

    if text is not None:
        assert read_input(path) == text
    else:
        with pytest.raises(UnreadableInput) as raised:
            read_input(path)
        assert str(raised.value).startswith(f"cannot read {path}: ")


def test_check_duplicates_has_no_reader_of_its_own() -> None:
    assert not hasattr(check_duplicates, "_read")
