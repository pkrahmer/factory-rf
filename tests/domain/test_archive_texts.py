"""The journal text of a merged work item's archive."""

import pytest

from bill_support import completed_records
from factory.domain.bills import bill, cost_line
from factory.domain.post_texts import done_entry_text

PREFIX = "done (pull request merged); cost: "


@pytest.mark.parametrize("count", [0, 3])
def test_the_done_entry_names_the_merge_and_ends_with_the_cost_line(count: int) -> None:
    the_bill = bill(completed_records("F0001-S0001", count))

    text = done_entry_text(the_bill)

    assert text.startswith(PREFIX)
    assert text.endswith(cost_line(the_bill))
    assert text == PREFIX + cost_line(the_bill)
