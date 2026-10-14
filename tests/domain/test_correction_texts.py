"""The texts of a correction: the move-back entry and the note on the pull request."""

from factory.domain.post_texts import MOVED_BACK_MARKER, correction_note, move_back_entry_text


def test_the_moved_back_marker_is_the_words_moved_back() -> None:
    assert MOVED_BACK_MARKER == "moved back"


def test_the_move_back_entry_names_the_illegal_change() -> None:
    assert move_back_entry_text("doing", "approval") == (
        "illegal stage change doing -> approval, moved back."
    )


def test_the_correction_note_says_the_stage_is_back_where_it_was() -> None:
    assert correction_note("doing", "approval") == (
        "The stage was changed from doing to approval, which factory/pipeline.yml does not "
        "allow; it is back at doing."
    )
