"""The fresh-home program: its arguments, its refusals and its faults."""

import io
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.entry.fresh_home import main
from home_files_support import build_home, listing, refusing

PREFIX = "factory-fresh-home: "
USAGE = f"{PREFIX}usage: fresh_home --home <folder> [--keep <path>]..."
FILES = {"a", "b"}


def _not_a_folder(folder: str) -> str:
    return f"{PREFIX}--home {folder} is not an absolute folder other than /"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    folder = tmp_path / "home"
    folder.mkdir()
    build_home(folder, FILES)
    return folder


@pytest.mark.parametrize(
    ("argv", "status", "lines", "remaining"),
    [
        pytest.param(lambda h: ["--home", str(h)], 0, [], set(), id="clears"),
        pytest.param(lambda h: ["--home", str(h), "--keep", "a"], 0, [], {"a"}, id="keeps"),
        pytest.param(lambda _h: [], 2, [USAGE], FILES, id="no-arguments"),
        pytest.param(lambda _h: ["--keep", "a"], 2, [USAGE], FILES, id="no-home"),
        pytest.param(
            lambda _h: ["--home", "relative"], 2, [_not_a_folder("relative")], FILES, id="relative"
        ),
        pytest.param(lambda _h: ["--home", "/"], 2, [_not_a_folder("/")], FILES, id="root"),
        pytest.param(
            lambda h: ["--home", str(h.parent / "missing")],
            2,
            [_not_a_folder("<missing>")],
            FILES,
            id="missing",
        ),
        pytest.param(
            lambda h: ["--home", str(h), "--keep", "../x"],
            2,
            [f"{PREFIX}--keep ../x is not a path inside the home"],
            FILES,
            id="keep-outside",
        ),
        pytest.param(lambda _h: ["--home"], 2, [USAGE], FILES, id="home-without-folder"),
        pytest.param(
            lambda h: ["--home", str(h), "--keep"], 2, [USAGE], FILES, id="keep-without-path"
        ),
        pytest.param(
            lambda h: ["--home", str(h), "--kept", "a"], 2, [USAGE], FILES, id="unknown-option"
        ),
    ],
)
def test_main_clears_the_named_home_or_refuses_its_arguments_untouched(
    home: Path,
    argv: Callable[[Path], list[str]],
    status: int,
    lines: list[str],
    remaining: set[str],
) -> None:
    expected = [line.replace("<missing>", str(home.parent / "missing")) for line in lines]
    stderr = io.StringIO()

    assert main(argv(home), stderr=stderr) == status
    assert stderr.getvalue().splitlines() == expected
    assert listing(home) == remaining


def test_main_writes_each_fault_and_returns_one(tmp_path: Path) -> None:
    home = tmp_path / "home"
    build_home(home, [".cache/a", ".cache/b"])
    stderr = io.StringIO()

    status = main(["--home", str(home)], stderr=stderr, owned=refusing(home, ".cache/a"))

    assert status == 1
    assert stderr.getvalue().splitlines() == [f"{PREFIX}.cache/a: Permission denied"]
