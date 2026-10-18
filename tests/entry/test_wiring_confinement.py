"""The wiring confines every agent run through `factory-confine` unless it is told not to."""

import ast
import inspect
from collections.abc import Callable

import pytest

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.settings import InstanceSettings
from factory.entry import run
from factory.entry.wiring import boundaries_from_environment, build_boundaries
from wiring_support import CREDENTIAL


def _claude_runtime(boundaries: Boundaries) -> ClaudeCodeRuntime:
    runtime = boundaries.agent_runtime
    assert isinstance(runtime, ClaudeCodeRuntime)
    return runtime


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        pytest.param(
            lambda settings: build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService()),
            "factory-confine",
            id="default",
        ),
        pytest.param(
            lambda settings: build_boundaries(
                settings, CREDENTIAL, hosting=FakeHostingService(), confine_executable=None
            ),
            None,
            id="none",
        ),
    ],
)
def test_build_boundaries_confines_the_runtime_unless_told_not_to(
    local_settings: InstanceSettings,
    *,
    build: Callable[[InstanceSettings], Boundaries],
    expected: str | None,
) -> None:
    assert _claude_runtime(build(local_settings)).confine_executable == expected


def test_every_run_of_the_factory_builds_a_confined_runtime(
    hosted_environment: dict[str, str],
) -> None:
    _, boundaries = boundaries_from_environment(hosted_environment, hosting=FakeHostingService())

    tree = ast.parse(inspect.getsource(run))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "build_boundaries"
    ]
    assert _claude_runtime(boundaries).confine_executable == "factory-confine"
    assert calls
    assert all(keyword.arg != "confine_executable" for call in calls for keyword in call.keywords)
