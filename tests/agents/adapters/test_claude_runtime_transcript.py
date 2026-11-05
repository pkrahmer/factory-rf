"""Where Claude Code keeps a session: `.claude/projects/<folder>/<session>.jsonl` in its home."""

from pathlib import Path

import pytest

from factory.agents.adapters.claude_runtime import ClaudeCodeRuntime

SESSION = "0b7c4a1e-5d2f-4c3a-9e8b-1a2b3c4d5e6f"
LINES = b'{"type": "user"}\n{"type": "assistant"}\n'


@pytest.fixture
def runtime(tmp_path: Path) -> ClaudeCodeRuntime:
    return ClaudeCodeRuntime("claude", tmp_path / "state")


@pytest.mark.parametrize(
    ("file_written", "asked", "found"),
    [
        pytest.param(True, SESSION, True, id="found"),
        pytest.param(False, SESSION, False, id="missing"),
        pytest.param(True, f"../{SESSION}", False, id="parent-folder"),
        pytest.param(True, "*", False, id="glob-character"),
        pytest.param(True, "a/b", False, id="path-separator"),
    ],
)
def test_a_session_is_read_from_its_project_folder_and_nothing_else_is(
    tmp_path: Path,
    runtime: ClaudeCodeRuntime,
    *,
    file_written: bool,
    asked: str,
    found: bool,
) -> None:
    home = tmp_path / "home"
    folder = home / ".claude" / "projects" / "-work-checkout"
    folder.mkdir(parents=True)
    if file_written:
        (folder / f"{SESSION}.jsonl").write_bytes(LINES)
        (folder / "a").mkdir()
        (folder / "a" / "b.jsonl").write_bytes(LINES)
        (home / ".claude" / "projects" / f"{SESSION}.jsonl").write_bytes(LINES)

    transcript = runtime.read_transcript(home, asked)

    if found:
        assert transcript is not None
        assert transcript.extension == "jsonl"
        assert transcript.content == LINES
    else:
        assert transcript is None
