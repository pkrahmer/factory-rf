"""A copy of a shared test helper is found by its body, whatever its name and parameters."""

import ast
from collections.abc import Mapping
from pathlib import Path

import pytest

from function_support import functions, without_docstring

TESTS = Path(__file__).parent
SHARED: dict[str, str] = {
    "log_lines": "log_support.py",
    "pushed": "stage_run_support.py",
    "pushed_state": "stage_run_support.py",
    "remote_document": "branch_reading.py",
    "push_state": "branch_reading.py",
}
THE_LOG_BODY = (
    '    log = tmp_path / "state" / "factory.log"\n'
    '    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []\n'
)


def body_of(function: ast.FunctionDef) -> str:
    """The function's statements, a leading docstring left aside, as `ast.unparse` prints each."""
    return "\n".join(ast.unparse(statement) for statement in without_docstring(function.body))


def shared_bodies(root: Path) -> dict[str, str]:
    """The body of each helper `SHARED` names, read with `ast` from its own module under `root`."""
    bodies: dict[str, str] = {}
    for name, module in SHARED.items():
        source = (root / module).read_text(encoding="utf-8")
        [function] = [function for function in functions(source) if function.name == name]
        bodies[name] = body_of(function)
    return bodies


def copies(source: str, bodies: Mapping[str, str]) -> list[str]:
    """The helpers that the top-level functions of `source` copy, by their body."""
    return [
        name
        for function in functions(source)
        for name, body in bodies.items()
        if body_of(function) == body
    ]


def _test_modules() -> list[Path]:
    return sorted(TESTS.rglob("*.py"))


@pytest.fixture(scope="module")
def bodies() -> dict[str, str]:
    """The shared helpers' bodies, read from this tree."""
    return shared_bodies(TESTS)


@pytest.mark.parametrize(
    ("shared", "expected"),
    [
        pytest.param("log_lines", ["log_support.py"], id="log_lines"),
        pytest.param("pushed", ["stage_run_support.py"], id="pushed"),
        pytest.param("pushed_state", ["stage_run_support.py"], id="pushed_state"),
        pytest.param("remote_document", ["branch_reading.py"], id="remote_document"),
        pytest.param("push_state", ["branch_reading.py"], id="push_state"),
    ],
)
def test_each_shared_helper_is_written_in_one_module(
    bodies: dict[str, str], shared: str, expected: list[str]
) -> None:
    holding = sorted(
        path.relative_to(TESTS).as_posix()
        for path in _test_modules()
        if shared in copies(path.read_text(encoding="utf-8"), bodies)
    )

    assert holding == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "def _the_log(tmp_path: Path) -> list[str]:\n" + THE_LOG_BODY,
            ["log_lines"],
            id="the-log-under-another-name",
        ),
        pytest.param(
            'def _the_log(tmp_path: Path) -> list[str]:\n    """Read the log."""\n' + THE_LOG_BODY,
            ["log_lines"],
            id="with-a-docstring",
        ),
        pytest.param(
            "@pytest.fixture\ndef _the_log(tmp_path: Path) -> list[str]:\n" + THE_LOG_BODY,
            ["log_lines"],
            id="under-a-decorator",
        ),
        pytest.param(
            "def _branch_document(boundaries, checkout):\n"
            "    checkout.fetch()\n"
            '    text = checkout.show_file(f"origin/{BRANCH}", PATH)\n'
            "    assert text is not None\n"
            "    return boundaries.work_item_reader.parse(text)\n",
            ["remote_document"],
            id="the-remote-document-without-annotations",
        ),
        pytest.param(
            "def _the_log(tmp_path: Path) -> list[str]:\n"
            '    log = tmp_path / "state" / "factory.log"\n'
            "    log.touch()\n"
            '    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []\n',
            [],
            id="one-more-statement",
        ),
        pytest.param(
            "class Rig:\n    def log(self, tmp_path):\n"
            + "".join(f"    {line}\n" for line in THE_LOG_BODY.splitlines()),
            [],
            id="a-method-in-a-class",
        ),
        pytest.param(
            "def log_lines(tmp_path):\n    return []\n",
            [],
            id="a-name-alone",
        ),
    ],
)
def test_the_guard_finds_a_copy_by_its_body_and_nothing_else(
    bodies: dict[str, str], source: str, expected: list[str]
) -> None:
    assert copies(source, bodies) == expected


def test_each_body_is_read_from_its_own_module() -> None:
    [function] = [
        function
        for function in functions((TESTS / "log_support.py").read_text(encoding="utf-8"))
        if function.name == "log_lines"
    ]

    assert shared_bodies(TESTS)["log_lines"] == body_of(function)


@pytest.mark.parametrize(
    "path",
    [pytest.param(path, id=path.relative_to(TESTS).as_posix()) for path in _test_modules()],
)
def test_no_test_module_holds_a_copy(bodies: dict[str, str], path: Path) -> None:
    found = copies(path.read_text(encoding="utf-8"), bodies)

    if path.name in SHARED.values():
        assert found, "a module that defines a shared helper holds its own helpers"
    else:
        assert found == []
