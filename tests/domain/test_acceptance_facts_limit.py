"""The reviewer's facts end at story number 9999 with a message of their own."""

import pytest

from factory.domain.acceptance import FeatureFiles, acceptance_facts


@pytest.mark.parametrize(
    ("highest", "next_story"),
    [("F0002-S9998-y.md", "F0002-S9999"), ("F0002-S9999-z.md", None)],
    ids=["9998", "9999"],
)
def test_the_next_story_number_ends_at_9999(highest: str, next_story: str | None) -> None:
    files = FeatureFiles(feature="F0002", done=["F0002-S0001-a.md", highest])

    if next_story is not None:
        assert acceptance_facts(files, "cost").next_story == next_story
    else:
        with pytest.raises(ValueError) as raised:
            acceptance_facts(files, "cost")
        assert type(raised.value) is ValueError
        assert str(raised.value) == "feature F0002 has no free story number after 9999"
