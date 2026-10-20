"""The duplicates readers skip another symbol and a blank line and still read what follows."""

import json
from collections.abc import Callable

import pytest

from factory.domain.duplicates import DuplicateFinding, dead_code_findings, similar_code_findings

OTHER_SYMBOL = {"symbol": "unused-import", "message": "Unused import os"}
DUPLICATE_CODE = {
    "symbol": "duplicate-code",
    "message": "Similar lines in 2 files\n==factory.a:[1:5]\n==factory.b:[2:6]\nx = 1\n",
}
SIMILAR = DuplicateFinding(
    key="similar-code factory.a, factory.b: x = 1",
    where="factory.a:[1:5], factory.b:[2:6]",
    message="Similar lines in 2 files",
)
VULTURE_LINE = "src/factory/x.py:3: unused import 'os' (90% confidence)\n"
DEAD = DuplicateFinding(
    key="dead-code src/factory/x.py: unused import 'os'",
    where="src/factory/x.py:3",
    message="unused import 'os' (90% confidence)",
)


@pytest.mark.parametrize(
    ("reader", "text", "findings"),
    [
        pytest.param(
            similar_code_findings,
            json.dumps([OTHER_SYMBOL, DUPLICATE_CODE]),
            [SIMILAR],
            id="other-symbol-first",
        ),
        pytest.param(
            similar_code_findings, json.dumps([DUPLICATE_CODE]), [SIMILAR], id="duplicate-only"
        ),
        pytest.param(dead_code_findings, "\n" + VULTURE_LINE, [DEAD], id="blank-line-first"),
        pytest.param(dead_code_findings, VULTURE_LINE, [DEAD], id="finding-only"),
    ],
)
def test_a_skipped_element_or_line_leaves_what_follows_it_read(
    reader: Callable[[str], list[DuplicateFinding]], text: str, findings: list[DuplicateFinding]
) -> None:
    assert reader(text) == findings
