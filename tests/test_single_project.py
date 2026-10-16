"""One instance runs one project: no list of repositories is left in the code."""

import re

from source_search import SRC


def test_no_module_names_a_list_of_repositories() -> None:
    pattern = re.compile(r"\bREPOS\b")
    found = [
        str(path.relative_to(SRC))
        for path in sorted(SRC.rglob("*.py"))
        if pattern.search(path.read_text(encoding="utf-8"))
    ]

    assert found == []
