"""No source or schema file of the package still names the removed stall reason."""

from source_search import SRC

NAMES = ["left_branch", "the agent left the work item's branch"]


def test_no_source_or_schema_file_names_left_branch() -> None:
    found = [
        (str(path.relative_to(SRC)), name)
        for pattern in ["*.py", "*.json"]
        for path in sorted(SRC.rglob(pattern))
        for name in NAMES
        if name in path.read_text(encoding="utf-8")
    ]

    assert found == []
