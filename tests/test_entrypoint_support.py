"""The entrypoint tests' layout and line helper are written in their support module alone."""

from pathlib import Path

TESTS = Path(__file__).parent
THIS = Path(__file__).name


def _containing(text: str) -> list[str]:
    return sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if path.name != THIS and text in path.read_text(encoding="utf-8")
    )


def test_the_entrypoint_layout_lives_in_its_support_module_alone() -> None:
    # The texts are split so that the search does not depend on this module's own source.
    assert _containing("class " + "Layout:") == ["confine_support.py", "entrypoint_support.py"]
    assert _containing("from test_" + "entrypoint import") == []
    assert _containing("def _" + "texts(output") == []
