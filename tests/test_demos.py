"""Every demo this repository ships passes the demo check."""

from pathlib import Path

from factory.entry.check_demos import main

REPOSITORY = Path(__file__).parents[1]


def test_the_shipped_demos_pass_the_demo_check() -> None:
    assert main(["--root", str(REPOSITORY)]) == 0
