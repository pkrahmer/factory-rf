"""Test modules are named after what they test: the interfaces are no protocols."""

from pathlib import Path

TESTS = Path(__file__).parent


def test_no_test_module_is_named_after_a_protocol() -> None:
    named = [path for path in TESTS.rglob("*.py") if "protocol" in path.name]

    assert named == []
    assert (TESTS / "application" / "test_git_interface.py").is_file()
    assert (TESTS / "application" / "test_hosting_interface.py").is_file()
