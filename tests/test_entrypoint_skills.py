"""The entrypoint leaves the agent's home with empty skills and commands it cannot fill."""

import os
import stat
from collections.abc import Callable
from pathlib import Path

import pytest

from entrypoint_support import Layout, texts


def _nothing(home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True)


def _planted(home: Path) -> None:
    (home / "skills" / "planted").mkdir(parents=True)
    (home / "skills" / "planted" / "SKILL.md").write_text("planted\n", encoding="utf-8")
    (home / "commands").mkdir()
    (home / "commands" / "plant.md").write_text("plant\n", encoding="utf-8")


def _file_and_nested_folder(home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True)
    (home / "skills").write_text("a file\n", encoding="utf-8")
    (home / "commands" / "sub").mkdir(parents=True)
    (home / "commands" / "sub" / "plant.md").write_text("plant\n", encoding="utf-8")


@pytest.mark.parametrize(
    "prepare",
    [
        pytest.param(_nothing, id="nothing"),
        pytest.param(_planted, id="planted-skill-and-command"),
        pytest.param(_file_and_nested_folder, id="file-and-nested-folder"),
    ],
)
def test_each_start_leaves_skills_and_commands_empty_and_read_only_to_the_agent(
    image_layout: Layout, prepare: Callable[[Path], None]
) -> None:
    prepare(image_layout.claude_home)

    result = image_layout.run()

    assert result.exit_status == 0
    assert texts(result.stderr) + texts(result.stdout) == [
        f"installed agents and settings into {image_layout.claude_home}",
        f"prepared {image_layout.state}/runs",
        "starting instance unset",
    ]
    for name in ("skills", "commands"):
        folder = image_layout.claude_home / name
        assert folder.is_dir()
        assert not folder.is_symlink()
        assert list(folder.iterdir()) == []
        status = folder.stat()
        assert status.st_uid == os.getuid()
        assert stat.S_IMODE(status.st_mode) == 0o755
