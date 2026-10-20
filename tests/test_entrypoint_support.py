"""The entrypoint tests' layout and line helper are written in their support module alone."""

import re
from pathlib import Path

from search_support import modules_matching

THIS = Path(__file__).name


def _containing(text: str) -> list[str]:
    return modules_matching(re.escape(text), THIS)


def test_the_entrypoint_layout_lives_in_its_support_module_alone() -> None:
    # The texts are split so that the search does not depend on this module's own source.
    assert _containing("class " + "Layout:") == ["confine_support.py", "entrypoint_support.py"]
    assert _containing("from test_" + "entrypoint import") == []
    assert _containing("def _" + "texts(output") == []
