"""The rule of the fresh home: which paths are inside a home, which are kept and what goes."""

from pathlib import Path

import pytest

from factory.domain.agent_home import HomeFate, fate, inside_home, kept_paths, removed_when_empty
from factory.domain.errors import SettingsInvalid
from factory.domain.settings import OPENCODE_FOLDERS_VARIABLE, read_settings
from settings_support import BASE

KEPT = [".claude-token", ".config/sso"]


@pytest.mark.parametrize(
    ("relative", "expected"),
    [
        pytest.param(".config/sso", True, id="nested"),
        pytest.param("a", True, id="one-segment"),
        pytest.param("", False, id="empty"),
        pytest.param("/a", False, id="absolute"),
        pytest.param("a//b", False, id="empty-segment"),
        pytest.param("./a", False, id="leading-dot"),
        pytest.param("a/.", False, id="trailing-dot"),
        pytest.param("a/..", False, id="trailing-parent"),
        pytest.param("..", False, id="parent"),
    ],
)
def test_a_path_is_inside_a_home_only_when_relative_without_empty_dot_or_parent_segments(
    relative: str, expected: bool
) -> None:
    assert inside_home(relative) is expected


@pytest.mark.parametrize(
    ("value", "expected", "fault"),
    [
        pytest.param(".config/sso", [".config/sso"], None, id="inside"),
        pytest.param(
            ".config/sso,a/../b",
            None,
            "holds a/../b, which is not a folder inside the agent's home",
            id="inner-parent",
        ),
    ],
)
def test_the_opencode_folders_setting_refuses_a_path_outside_the_home(
    value: str, expected: list[str] | None, fault: str | None
) -> None:
    environ = {**BASE, OPENCODE_FOLDERS_VARIABLE: value}

    if fault is None:
        assert read_settings(environ).opencode_folders == expected
        return
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ)

    assert raised.value.variable == "FACTORY_OPENCODE_FOLDERS"
    assert raised.value.fault == fault


@pytest.mark.parametrize(
    ("state_files", "folders", "refused"),
    [
        pytest.param(
            [".claude/.credentials.json"], [".config/sso", ".claude-token"], None, id="valid"
        ),
        pytest.param([".claude/.credentials.json"], ["/abs"], "/abs", id="absolute-folder"),
        pytest.param(["../x"], [".config/sso"], "../x", id="parent-state-file"),
    ],
)
def test_kept_paths_are_the_logins_inside_the_home_then_state_files_then_folders(
    state_files: list[str], folders: list[str], refused: str | None
) -> None:
    def kept() -> list[str]:
        return kept_paths(
            Path("/home/agent"),
            login_files=[Path("/home/agent/.claude-token"), None, Path("/run/key")],
            state_files=state_files,
            folders=folders,
        )

    if refused is None:
        assert kept() == [".claude-token", ".claude/.credentials.json", ".config/sso"]
        return
    with pytest.raises(ValueError, match=refused):
        kept()


@pytest.mark.parametrize(
    ("relative", "owned", "folder", "expected"),
    [
        pytest.param(".claude-token", False, False, "keep", id="kept-file"),
        pytest.param(".config/sso", True, True, "keep", id="kept-folder"),
        pytest.param(".config/sso/login", True, False, "keep", id="beneath-kept"),
        pytest.param(".config", True, True, "descend", id="above-kept"),
        pytest.param(".claude", False, True, "descend", id="foreign-folder"),
        pytest.param(".claude/projects", True, True, "descend", id="own-folder"),
        pytest.param(".claude/CLAUDE.md", True, False, "remove", id="own-file"),
        pytest.param(".claude/settings.json", False, False, "keep", id="foreign-file"),
        pytest.param(".config-old", True, False, "remove", id="kept-prefix-only"),
        pytest.param(".config", True, False, "remove", id="own-non-folder-above-kept"),
        pytest.param(".config", False, False, "keep", id="foreign-non-folder-above-kept"),
    ],
)
def test_the_fate_of_an_entry_follows_kept_paths_folders_and_ownership(
    relative: str, owned: bool, folder: bool, expected: HomeFate
) -> None:
    assert fate(relative, owned=owned, folder=folder, kept=KEPT) == expected


@pytest.mark.parametrize(
    ("relative", "owned", "expected"),
    [
        pytest.param(".cache", True, True, id="own"),
        pytest.param(".config", True, False, id="kept-beneath"),
        pytest.param(".claude", False, False, id="foreign"),
    ],
)
def test_an_empty_folder_is_removed_only_when_owned_and_above_no_kept_path(
    relative: str, owned: bool, expected: bool
) -> None:
    assert removed_when_empty(relative, owned=owned, kept=KEPT) is expected
