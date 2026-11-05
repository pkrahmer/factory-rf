"""No file names the agent files' old folder or the image's old place for them."""

import re
from pathlib import Path

import pytest

from support.guide_files_support import searched_files

ROOT = Path(__file__).parents[2]
SEARCHED = (
    ROOT / "src",
    ROOT / "tests",
    ROOT / "operator",
    ROOT / "docs",
    ROOT / "README.md",
)
NOT_SEARCHED = (ROOT / "docs" / "decisions.md", ROOT / "docs" / "runs")
# Built from their parts, so that this file does not name them itself.
OLD_NAMES = ("claude" + "/agents/", "claude" + "/settings.json", "/etc/factory/" + "claude")


@pytest.mark.parametrize("old_name", OLD_NAMES)
def test_no_file_names_the_old_agent_folder(old_name: str) -> None:
    naming = [
        str(path.relative_to(ROOT))
        for path in searched_files(SEARCHED, NOT_SEARCHED)
        if re.search(
            r"(?<![\w.])" + re.escape(old_name), path.read_text(encoding="utf-8", errors="ignore")
        )
    ]

    assert naming == []
