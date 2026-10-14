"""The text of the report the factory posts when it stops retrying an event."""

from factory.domain.post_texts import error_report_text


def test_the_error_report_names_the_event_the_error_and_the_short_remote_state() -> None:
    text = error_report_text("run:F0001-S0001", "ValueError: boom", "c" * 40, 3)

    assert text == (
        "The factory failed 3 times on `run:F0001-S0001` and has stopped retrying it."
        " Last error: ValueError: boom. A new commit on the work item's branch"
        " (now at cccccccccccc) makes the factory try again."
    )
