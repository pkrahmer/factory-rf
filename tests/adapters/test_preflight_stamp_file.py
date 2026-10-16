"""The preflight stamp file: JSON, replaced atomically, absent when missing or damaged."""

import json
from pathlib import Path

import pytest

from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.domain.preflight import PreflightStamp

NAME = "preflight-stamp.json"
STAMP = PreflightStamp(image="build-7", main_probed="a" * 40, main_failed=None)


def test_a_written_stamp_reads_back_as_one_json_object_of_three_keys(tmp_path: Path) -> None:
    store = JsonPreflightStampFile(tmp_path / NAME)

    store.write(STAMP)

    assert store.read() == STAMP
    assert json.loads((tmp_path / NAME).read_text(encoding="utf-8")) == {
        "image": "build-7",
        "main_probed": "a" * 40,
        "main_failed": None,
    }


@pytest.mark.parametrize(
    "text",
    [None, "not a stamp", '{"image": "build-7", "main_probed": "' + "a" * 39 + '"}'],
    ids=["missing", "not-a-stamp", "commit-breaks-the-pattern"],
)
def test_a_missing_or_invalid_file_reads_as_no_stamp(tmp_path: Path, text: str | None) -> None:
    if text is not None:
        (tmp_path / NAME).write_text(text, encoding="utf-8")

    assert JsonPreflightStampFile(tmp_path / NAME).read() is None


def test_a_write_leaves_no_file_but_the_stamp_in_its_directory(tmp_path: Path) -> None:
    directory = tmp_path / "state"

    JsonPreflightStampFile(directory / NAME).write(STAMP)

    assert [path.name for path in directory.iterdir()] == [NAME]
