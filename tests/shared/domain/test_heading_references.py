"""References to another page's heading are found, resolved and checked against its headings."""

import pytest

from factory.shared.domain.heading_references import (
    HeadingReference,
    heading_references,
    page_headings,
    unresolved_headings,
)

DOCUMENT = "docs/project-guide/shared.md"
MACHINE = "docs/project-guide/machine.md"
PIPELINE = "docs/project-guide/pipeline.md"
INSTALL = "docs/operator-guide/install.md"


def _page(line: str) -> str:
    return f"# The shared area\n\nThe factory works on work items.\n\n{line}\n\nThe end.\n"


REFERENCE_LINE = 5


def _found(heading: str, target: str) -> list[HeadingReference]:
    return [
        HeadingReference(document=DOCUMENT, line=REFERENCE_LINE, heading=heading, target=target)
    ]


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        pytest.param(
            "See *The two passes* in [machine.md](machine.md).",
            _found("The two passes", MACHINE),
            id="italics-in",
        ),
        pytest.param(
            'See "The two passes" of [machine.md](machine.md).',
            _found("The two passes", MACHINE),
            id="quotes-of",
        ),
        pytest.param(
            "(see *The two passes*) in [machine.md](machine.md).",
            _found("The two passes", MACHINE),
            id="closing-parenthesis-before-in",
        ),
        pytest.param(
            "See *The two passes*, in [machine.md](machine.md).",
            _found("The two passes", MACHINE),
            id="comma-before-in",
        ),
        pytest.param(
            'See "The *two* passes" in [machine.md](machine.md).',
            _found("The two passes", MACHINE),
            id="asterisks-inside",
        ),
        pytest.param(
            "See *The shared area* in [shared.md](shared.md).",
            [],
            id="own-file",
        ),
        pytest.param(
            "See *`StageFinisher.finish`* in [pipeline.md](pipeline.md).",
            _found("StageFinisher.finish", PIPELINE),
            id="backticks",
        ),
        pytest.param(
            "See *Install* in [install.md](../operator-guide/install.md).",
            _found("Install", INSTALL),
            id="other-folder",
        ),
        pytest.param(
            "See *Install* in [install.md](../operator-guide/install.md#install).",
            [],
            id="anchor",
        ),
        pytest.param(
            "See *The script* in [setup.sh](../../operator/vm/setup.sh).",
            [],
            id="not-a-markdown-file",
        ),
        pytest.param(
            "See *The two passes* and [machine.md](machine.md).",
            [],
            id="neither-in-nor-of",
        ),
    ],
)
def test_a_reference_to_another_pages_heading_is_found_with_its_line_heading_and_target(
    line: str, expected: list[HeadingReference]
) -> None:
    assert heading_references(DOCUMENT, _page(line)) == expected


REFERENCE = HeadingReference(document=DOCUMENT, line=7, heading="The two passes", target=MACHINE)


@pytest.mark.parametrize(
    ("page", "expected"),
    [
        pytest.param(
            {"The machine area", "The idle shutdown"},
            [f"{DOCUMENT}:7: The two passes is no heading of {MACHINE}"],
            id="missing-heading",
        ),
        pytest.param({"The machine area", "The two passes"}, [], id="existing-heading"),
        pytest.param(None, [], id="no-document-of-the-check"),
    ],
)
def test_a_reference_to_a_heading_the_linked_page_does_not_have_is_one_finding(
    page: set[str] | None, expected: list[str]
) -> None:
    def headings(target: str) -> set[str] | None:
        assert target == MACHINE
        return page

    assert unresolved_headings([REFERENCE], headings) == expected


@pytest.mark.parametrize(
    ("heading_line", "reference", "matches"),
    [
        pytest.param(
            "## What `factory-bill` shows", "What factory-bill shows", True, id="backticks"
        ),
        pytest.param("## The *two* passes", "The two passes", True, id="asterisks"),
        pytest.param(
            "### `StageFinisher.finish(aftermath)`",
            "StageFinisher.finish",
            False,
            id="only-code-marks-are-stripped",
        ),
    ],
)
def test_a_pages_headings_lose_their_code_marks_and_nothing_else(
    heading_line: str, reference: str, matches: bool
) -> None:
    text = f"# A page\n\nThe factory works on work items.\n\n{heading_line}\n\nThe end.\n"

    assert (reference in page_headings(text)) is matches
