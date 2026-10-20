"""Searches the test modules under `tests` for a pattern."""

import re
from pathlib import Path

TESTS = Path(__file__).parent


def modules_matching(pattern: str, leave_out: str) -> list[str]:
    """The sorted paths, relative to `tests`, of the modules that match `pattern`.

    The module named `leave_out` is not searched, so that a test's own source does not count.
    """
    found = re.compile(pattern, re.MULTILINE | re.DOTALL)
    return sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if path.name != leave_out and found.search(path.read_text(encoding="utf-8"))
    )
