"""Whether the paths between two commits are the stop records file alone."""

import pytest

from factory.domain.git import ChangedPath, ChangeKind
from factory.domain.preflight import changes_only_stop_records

STOPS = "factory/stops.jsonl"


def _changed(*paths: tuple[str, ChangeKind]) -> list[ChangedPath]:
    return [ChangedPath(path=path, change=change) for path, change in paths]


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        pytest.param([], False, id="empty"),
        pytest.param(_changed((STOPS, "modified")), True, id="modified"),
        pytest.param(_changed((STOPS, "added")), True, id="added"),
        pytest.param(_changed((STOPS, "deleted")), True, id="deleted"),
        pytest.param(_changed((STOPS, "modified"), ("src/a.py", "modified")), False, id="mixed"),
        pytest.param(_changed(("src/a.py", "modified")), False, id="other"),
        pytest.param(_changed((f"{STOPS}.bak", "added")), False, id="similar-name"),
        pytest.param(_changed(("factory/other.jsonl", "modified")), False, id="other-jsonl"),
    ],
)
def test_only_the_stop_records_file_is_a_change_of_stop_records_only(
    paths: list[ChangedPath], expected: bool
) -> None:
    assert changes_only_stop_records(paths) is expected
