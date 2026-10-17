"""The agent's home: the factory owns its agents and settings, the agent only adds its own files."""

import stat
from pathlib import Path

import pytest

from test_entrypoint import AGENT_TEXT, Layout
from test_image import DOCKERFILE, _path_settings

CREDENTIALS_TEXT = '{"token": "stand-in"}\n'


@pytest.fixture
def layout(tmp_path: Path) -> Layout:
    """Return the image layout, homes, state and stubs of one run under `tmp_path`."""
    return Layout(tmp_path)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


@pytest.mark.parametrize(
    ("path", "owner", "mode"),
    [
        pytest.param("/home/agent/.claude", "factory", "3775", id="agent-home"),
        pytest.param("/work", None, "2775", id="work"),
    ],
)
def test_the_agent_home_is_the_factorys_with_the_sticky_bit_and_work_stays_shared(
    path: str, owner: str | None, mode: str
) -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    user, _, group = _path_settings(dockerfile, "chown")[path].partition(":")

    assert _path_settings(dockerfile, "chmod")[path] == mode
    assert group == "factory-work"
    if owner is not None:
        assert user == owner


@pytest.mark.parametrize(
    ("relative", "mode"),
    [
        pytest.param("agents", 0o755, id="agents"),
        pytest.param("agents/coder.md", 0o644, id="coder"),
        pytest.param("agents/reviewer.md", 0o644, id="reviewer"),
        pytest.param("settings.json", 0o644, id="settings"),
    ],
)
def test_the_installed_agents_and_settings_are_not_writable_by_group_or_others(
    layout: Layout, relative: str, mode: int
) -> None:
    image = layout.opt / "claude"
    (image / "agents" / "reviewer.md").write_text(AGENT_TEXT, encoding="utf-8")
    # The image's copies may arrive group-writable; the installed ones must not stay so.
    image.joinpath("agents").chmod(0o775)
    for path in [*image.joinpath("agents").iterdir(), image / "settings.json"]:
        path.chmod(0o664)

    result = layout.run()

    assert result.exit_status == 0
    installed = _mode(layout.claude_home / relative)
    assert installed == mode
    assert installed & 0o022 == 0


def test_a_file_the_agent_made_in_the_home_is_left_as_it_was(layout: Layout) -> None:
    credentials = layout.claude_home / ".credentials.json"
    credentials.parent.mkdir(parents=True)
    credentials.write_text(CREDENTIALS_TEXT, encoding="utf-8")
    credentials.chmod(0o600)

    result = layout.run()

    assert result.exit_status == 0
    assert credentials.read_text(encoding="utf-8") == CREDENTIALS_TEXT
    assert _mode(credentials) == 0o600
