"""The journal entry of an expiry names the stage and the commit its work is discarded back to."""

from factory.domain.recovery import expiry_entry_text


def test_the_expiry_entry_names_the_stage_the_count_and_the_commit() -> None:
    assert expiry_entry_text("doing", 1, "b" * 40) == (
        "expiry 1: the lease of stage doing ran out. Its work is discarded back to commit "
        + "b" * 40
        + "."
    )
