"""The reviewer's checklist goes through all five groups in every review."""

import re
import zlib

import pytest

from support.shipped_agents import SHIPPED_NAMES, agent_body

_ALL_GROUPS = (
    "Checklist, in this order. Go through all of groups 1 to 5 in every review, also when an "
    "earlier group fails, and report every finding of every group in this one entry; do not "
    "pad the report. Item 6 is part of every review."
)

_STOP_AT_THE_FIRST = (
    "Checklist, in this order. Stop at the first failing group of 1 to 5 and report it; do not "
    "pad the report. Item 6 is part of every review, whichever group failed."
)

# The CRC-32 of the reviewer's body on `main` before the checklist sentence changed.
_EARLIER_BODY_CRC32 = 3903663111

# The docs route's subsection, from its heading to the next heading, which a later story added.
_DOCS_REVIEW_SUBSECTION = re.compile(r"^### docs-review\n(?:(?!#).*\n|\n)*", re.MULTILINE)


def test_the_checklist_sentence_asks_for_all_five_groups_right_before_item_one() -> None:
    assert f"\n{_ALL_GROUPS}\n\n1. **Acceptance criteria**" in agent_body("reviewer")


def test_the_reviewer_no_longer_says_stop_at_the_first_failing_group() -> None:
    assert "Stop at the first failing group" not in agent_body("reviewer")


@pytest.mark.parametrize("name", [name for name in SHIPPED_NAMES if name != "reviewer"])
def test_no_other_agent_asks_for_all_five_groups(name: str) -> None:
    assert "Go through all of groups 1 to 5" not in agent_body(name)


def test_the_rest_of_the_reviewer_body_is_unchanged() -> None:
    body = _DOCS_REVIEW_SUBSECTION.sub("", agent_body("reviewer"))
    assert body.count(_ALL_GROUPS) == 1

    untested_side_is_a_note = (
        "A point on an acceptance criterion, the architecture, security or anything under "
        "`src/` is still a finding and sends it back with `doing`. One exception holds from "
        "round 0: a side of a stated limit that has no test is a note, not a finding, when you "
        "have read the code and it handles that side as the Interface says; the note names the "
        "side, the code's location and the missing row. A side the code does not handle, or "
        "handles otherwise, is a finding."
    )
    untested_side_is_a_finding = (
        "A point on an acceptance criterion (an untested side of a stated limit among them), "
        "the architecture, security or anything under `src/` is still a finding and sends it "
        "back with `doing`."
    )
    earlier = body.replace(_ALL_GROUPS, _STOP_AT_THE_FIRST).replace(
        untested_side_is_a_note, untested_side_is_a_finding
    )

    assert zlib.crc32(earlier.encode()) == _EARLIER_BODY_CRC32
