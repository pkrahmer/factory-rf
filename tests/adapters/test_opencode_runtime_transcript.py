"""opencode's transcript: the event stream of a session's last run, one event per line."""

from pathlib import Path

from adapters.opencode_stand_in import (
    REPLY,
    REPLY_EVENTS,
    SESSION,
    opencode_request,
    stand_in_runtime,
)

OTHER_SESSION = "ses_other"


def test_a_session_transcript_is_the_event_stream_of_its_run(tmp_path: Path) -> None:
    runtime = stand_in_runtime(tmp_path, [REPLY])
    result = runtime.run(opencode_request(tmp_path / "work"))
    assert result.session == SESSION

    transcript = runtime.read_transcript(tmp_path / "home", SESSION)

    assert transcript is not None
    assert transcript.extension == "jsonl"
    assert transcript.content == REPLY_EVENTS.encode("utf-8")


def test_a_session_the_runtime_never_saw_has_no_transcript(tmp_path: Path) -> None:
    runtime = stand_in_runtime(tmp_path, [REPLY])
    runtime.run(opencode_request(tmp_path / "work"))

    assert runtime.read_transcript(tmp_path / "home", OTHER_SESSION) is None
