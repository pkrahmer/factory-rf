"""The test remote's definition and the factory log are each read by one shared function."""

import ast
from collections.abc import Callable
from pathlib import Path

import pytest

from definition_support import pipeline_definition
from factory.application.boundaries import Boundaries
from factory.domain.pipeline_definition import PipelineDefinition

TESTS = Path(__file__).parent
DEFINITION_BODY = "return boundaries.pipeline_reader.parse(PIPELINE_YAML)"
LOG_NAMES = ("log_lines", "_log_lines")


def _functions(source: str) -> list[ast.FunctionDef]:
    return [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)]


def _without_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    match body[0]:
        case ast.Expr(value=ast.Constant(value=str())):
            return body[1:]
        case _:
            return body


def _copies_the_definition(source: str) -> bool:
    for function in _functions(source):
        rest = _without_docstring(function.body)
        if len(rest) == 1 and ast.unparse(rest[0]) == DEFINITION_BODY:
            return True
    return False


def _copies_the_log_reading(source: str) -> bool:
    return any(
        function.name in LOG_NAMES
        and [argument.arg for argument in function.args.posonlyargs + function.args.args]
        == ["tmp_path"]
        and not function.args.kwonlyargs
        and function.args.vararg is None
        and function.args.kwarg is None
        for function in _functions(source)
    )


def test_the_shared_definition_is_the_fixtures_definition(
    boundaries: Boundaries, definition: PipelineDefinition
) -> None:
    shared = pipeline_definition(boundaries)

    assert shared == definition
    assert shared.acceptance_stage == "acceptance"


@pytest.mark.parametrize(
    ("copies", "expected"),
    [
        pytest.param(_copies_the_definition, ["definition_support.py"], id="definition"),
        pytest.param(_copies_the_log_reading, ["log_support.py"], id="log"),
    ],
)
def test_each_shared_reading_is_written_in_one_module(
    copies: Callable[[str], bool], expected: list[str]
) -> None:
    holding = sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if copies(path.read_text(encoding="utf-8"))
    )

    assert holding == expected


@pytest.mark.parametrize(
    ("source", "is_definition", "is_log"),
    [
        pytest.param(
            "def _definition(boundaries: Boundaries) -> PipelineDefinition:\n"
            "    return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n",
            True,
            False,
            id="the-definition-copy",
        ),
        pytest.param(
            'def read_it(boundaries):\n    """Read it."""\n'
            "    return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n",
            True,
            False,
            id="the-definition-under-another-name",
        ),
        pytest.param(
            "def _definition(boundaries, text):\n"
            "    return boundaries.pipeline_reader.parse(text)\n",
            False,
            False,
            id="a-definition-of-another-text",
        ),
        pytest.param(
            "def _log_lines(tmp_path):\n    return []\n",
            False,
            True,
            id="the-log-reading-copy",
        ),
        pytest.param(
            "class Rig:\n    def log_lines(self):\n        return []\n",
            False,
            False,
            id="a-method-named-log-lines",
        ),
        pytest.param(
            "def _log_lines(state_directory):\n    return []\n",
            False,
            False,
            id="a-log-reading-of-another-folder",
        ),
        pytest.param(
            "def _definition(boundaries):\n"
            "    boundaries.reset()\n"
            "    return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n",
            False,
            False,
            id="a-definition-of-more-than-one-statement",
        ),
        pytest.param(
            "class Rig:\n"
            "    def definition(self, boundaries):\n"
            "        return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n",
            False,
            False,
            id="a-method-reading-the-definition",
        ),
        pytest.param(
            "def _log_lines(tmp_path, name):\n    return []\n",
            False,
            False,
            id="a-log-reading-of-more-than-the-folder",
        ),
    ],
)
def test_the_guard_finds_a_copy_by_its_body_and_nothing_else(
    source: str, *, is_definition: bool, is_log: bool
) -> None:
    assert _copies_the_definition(source) is is_definition
    assert _copies_the_log_reading(source) is is_log
