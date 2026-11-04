"""Where Claude Code keeps a session: its `projects/<folder>/<session>.jsonl` under the home."""

from pathlib import Path

import pytest

from factory.adapters.claude_runtime import ClaudeCodeRuntime

SESSION = "0b7c4a1e-5d2f-4c3a-9e8b-1a2b3c4d5e6f"
LINES = b'{"type": "user"}\n{"type": "assistant"}\n'


@pytest.fixture
def runtime(tmp_path: Path) -> ClaudeCodeRuntime:
    return ClaudeCodeRuntime("claude", tmp_path / "state")


def test_a_session_is_read_from_its_project_folder(
    tmp_path: Path, runtime: ClaudeCodeRuntime
) -> None:
    home = tmp_path / "home"
    folder = home / "projects" / "-work-checkout"
    folder.mkdir(parents=True)
    (folder / f"{SESSION}.jsonl").write_bytes(LINES)

    transcript = runtime.read_transcript(home, SESSION)

    assert transcript is not None
    assert transcript.content == LINES


def test_a_session_without_a_file_has_no_transcript(
    tmp_path: Path, runtime: ClaudeCodeRuntime
) -> None:
    home = tmp_path / "home"
    (home / "projects" / "-work-checkout").mkdir(parents=True)

    assert runtime.read_transcript(home, SESSION) is None
