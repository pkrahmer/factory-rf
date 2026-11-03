"""The operator's skill: its texts give the repository's current name."""

from pathlib import Path

import pytest

from operator_skill_support import SKILL


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(SKILL / "SKILL.md", id="skill"),
        pytest.param(
            SKILL / "references" / "standing-orders.md",
            id="standing-orders",
        ),
    ],
)
def test_the_skill_texts_do_not_name_the_old_repository(text: Path) -> None:
    assert "factory-rf" not in text.read_text(encoding="utf-8")
