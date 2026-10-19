"""The template's Makefile header calls `mutants` a sweep by hand, not a report."""

import pytest

from shipped_agents import ROOT

_NEW_HEADER_LINE = (
    "# `duplicates` is a report outside `check`; `mutants` is for a sweep by hand, never a stage."
)


@pytest.mark.parametrize(
    ("text", "count", "line_number"),
    [
        pytest.param(_NEW_HEADER_LINE, 1, 4, id="new-line-4"),
        pytest.param("`duplicates` and `mutants` are reports", 0, None, id="old-phrase"),
        pytest.param("# A Python example with a src layout.", None, 5, id="line-5"),
    ],
)
def test_template_makefile_header_calls_mutants_a_sweep_by_hand(
    text: str, count: int | None, line_number: int | None
) -> None:
    makefile = (ROOT / "template" / "Makefile").read_text(encoding="utf-8")
    if count is not None:
        assert makefile.count(text) == count
    if line_number is not None:
        assert makefile.splitlines()[line_number - 1] == text
