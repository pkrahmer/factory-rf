"""The walk that clears an agent's home of its own entries but the kept paths."""

import stat
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.home_files import clear_home
from home_files_support import build_home, listing, owned_but, refusing


@pytest.fixture
def home(tmp_path: Path) -> Path:
    folder = tmp_path / "home"
    folder.mkdir()
    return folder


def test_clear_home_keeps_kept_paths_and_foreign_entries_and_removes_the_rest(home: Path) -> None:
    build_home(
        home,
        [
            ".claude/agents/a.md",
            ".claude/settings.json",
            ".claude/CLAUDE.md",
            ".claude/rules/x.md",
            ".claude/projects/p/t.jsonl",
            ".claude/.credentials.json",
            ".config/opencode/",
            ".config/sso/login",
            ".cache/uv/f",
            ".profile",
            ".claude-token",
        ],
    )
    owned = owned_but(
        home,
        [
            ".claude",
            ".claude/agents",
            ".claude/agents/a.md",
            ".claude/settings.json",
            ".config/opencode",
        ],
    )

    faults = clear_home(
        home, [".claude-token", ".claude/.credentials.json", ".config/sso"], owned=owned
    )

    assert faults == []
    assert listing(home) == {
        ".claude",
        ".claude/agents",
        ".claude/agents/a.md",
        ".claude/settings.json",
        ".claude/.credentials.json",
        ".config",
        ".config/opencode",
        ".config/sso",
        ".config/sso/login",
        ".claude-token",
    }


def test_an_own_folder_closed_to_its_owner_is_removed_whole(home: Path) -> None:
    build_home(home, [".claude/projects/p.jsonl"])
    (home / ".claude/projects").chmod(0o000)

    faults = clear_home(home, [])

    assert faults == []
    assert not (home / ".claude/projects").exists()


def _link_outside(home: Path, outside: Path) -> tuple[str, list[Path]]:
    build_home(outside, ["f"])
    (home / ".claude").mkdir()
    (home / ".claude/link").symlink_to(outside, target_is_directory=True)
    return ".claude/link", [outside, outside / "f"]


def _link_to_kept(home: Path, _outside: Path) -> tuple[str, list[Path]]:
    build_home(home, [".config/sso/login", ".claude/"])
    (home / ".claude/link").symlink_to(home / ".config/sso", target_is_directory=True)
    return ".claude/link", [home / ".config/sso", home / ".config/sso/login"]


def _link_above_kept(home: Path, outside: Path) -> tuple[str, list[Path]]:
    build_home(outside, ["sso/login", "work.py"])
    (home / ".config").symlink_to(outside, target_is_directory=True)
    return ".config", [outside, outside / "sso/login", outside / "work.py"]


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_link_outside, id="to-outside-folder"),
        pytest.param(_link_to_kept, id="to-kept-path"),
        pytest.param(_link_above_kept, id="named-above-kept-path"),
    ],
)
def test_an_own_link_is_removed_and_never_followed(
    home: Path, tmp_path: Path, build: Callable[[Path, Path], tuple[str, list[Path]]]
) -> None:
    link, staying = build(home, tmp_path / "outside")

    faults = clear_home(home, [".config/sso"])

    assert faults == []
    assert not (home / link).is_symlink()
    assert not (home / link).exists()
    assert all(path.exists() for path in staying)


def test_a_fault_at_an_entry_is_recorded_and_the_walk_goes_on(home: Path) -> None:
    build_home(home, [".cache/a", ".cache/b"])

    faults = clear_home(home, [], owned=refusing(home, ".cache/a"))

    assert faults == [".cache/a: Permission denied"]
    assert not (home / ".cache/b").exists()


def test_the_modes_of_foreign_entries_stay_as_they_are(home: Path) -> None:
    build_home(home, [".claude/agents/", ".claude/settings.json"])
    (home / ".claude/settings.json").chmod(0o444)
    (home / ".claude/agents").chmod(0o500)
    owned = owned_but(home, [".claude", ".claude/agents", ".claude/settings.json"])

    clear_home(home, [], owned=owned)

    assert stat.S_IMODE((home / ".claude/agents").stat().st_mode) == 0o500
    assert stat.S_IMODE((home / ".claude/settings.json").stat().st_mode) == 0o444


def test_an_own_folder_holding_a_foreign_entry_stays_and_an_own_empty_one_goes(home: Path) -> None:
    build_home(home, [".cache/x/f", ".cache/y/", ".claude-token"])

    faults = clear_home(home, [".claude-token"], owned=owned_but(home, [".cache/x/f"]))

    assert faults == []
    assert (home / ".cache/x/f").is_file()
    assert not (home / ".cache/y").exists()
