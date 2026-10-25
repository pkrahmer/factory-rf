"""The leftovers program, its modules and every name that started or configured it are gone."""

import importlib.util
import inspect
from collections.abc import Callable

import pytest

from factory.adapters import agent_launch, process
from factory.adapters.agent_launch import Starters
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.entry import wiring
from factory.entry.wiring import build_boundaries
from source_search import SRC


def _no_parameter(function: Callable[..., object], name: str) -> bool:
    return name not in inspect.signature(function).parameters


@pytest.mark.parametrize("module", ["factory.entry.leftovers", "factory.domain.leftovers"])
def test_the_leftovers_modules_are_gone(module: str) -> None:
    assert importlib.util.find_spec(module) is None


@pytest.mark.parametrize(
    "gone",
    [
        *(
            pytest.param(lambda module=module, name=name: not hasattr(module, name), id=name)
            for module, name in (
                (process, "own_identity"),
                (process, "signal_every_other"),
                (agent_launch, "LEFTOVERS_TIME_LIMIT"),
                (agent_launch, "LEFTOVERS_FAULT"),
                (agent_launch, "leftovers_due"),
                (agent_launch, "leftovers_launch"),
                (agent_launch, "due_leftovers_launch"),
                (agent_launch, "leftovers_fault"),
                (wiring, "leftovers_command"),
                (wiring, "LEFTOVERS_MODULE"),
            )
        ),
        pytest.param(
            lambda: list(Starters.model_fields) == ["login_files"],
            id="starters-fields",
        ),
        pytest.param(lambda: not hasattr(ClaudeCodeRuntime, "leftovers"), id="claude-property"),
        pytest.param(lambda: not hasattr(OpencodeRuntime, "leftovers"), id="opencode-property"),
        pytest.param(
            lambda: _no_parameter(ClaudeCodeRuntime.__init__, "leftovers"), id="claude-keyword"
        ),
        pytest.param(
            lambda: _no_parameter(OpencodeRuntime.__init__, "leftovers"), id="opencode-keyword"
        ),
        pytest.param(
            lambda: _no_parameter(build_boundaries, "end_leftovers"), id="boundaries-keyword"
        ),
    ],
)
def test_the_names_that_started_the_leftovers_program_are_gone(gone: Callable[[], bool]) -> None:
    assert gone()


def test_no_module_names_the_leftovers_program_or_its_fault() -> None:
    holders = {
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        for text in (path.read_text(encoding="utf-8"),)
        if "factory.entry.leftovers" in text or "cannot end the agent's processes" in text
    }

    assert holders == set()
