"""The operator's skill: its texts give the repository's current name."""

from pathlib import Path

import pytest

from operator_support import ROOT

SKILL_DIRECTORY = ROOT / "operator" / "skill" / "kumpel"


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(SKILL_DIRECTORY / "SKILL.md", id="skill"),
        pytest.param(
            SKILL_DIRECTORY / "references" / "standing-orders.md",
            id="standing-orders",
        ),
    ],
)
def test_the_skill_texts_do_not_name_the_old_repository(text: Path) -> None:
    assert "factory-rf" not in text.read_text(encoding="utf-8")
