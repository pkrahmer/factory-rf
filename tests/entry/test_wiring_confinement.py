"""The wiring confines every agent run through `factory-confine` unless it is told not to."""

import ast
import inspect
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.settings import InstanceSettings
from factory.entry import run
from factory.entry.wiring import boundaries_from_environment, build_boundaries

CREDENTIAL = "example-value"


@pytest.fixture
def settings(tmp_path: Path) -> InstanceSettings:
    """Settings whose checkout, state directory and agent home lie in `tmp_path`."""
    root = tmp_path.resolve()
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
    )


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
    settings: InstanceSettings,
    *,
    build: Callable[[InstanceSettings], Boundaries],
    expected: str | None,
) -> None:
    assert _claude_runtime(build(settings)).confine_executable == expected


def test_every_run_of_the_factory_builds_a_confined_runtime(tmp_path: Path) -> None:
    token = tmp_path / "hosting-token"
    token.write_text("example-value\n", encoding="utf-8")
    image = tmp_path / "image-id"
    image.write_text("build-7\n", encoding="utf-8")
    environ = {
        "FACTORY_REPOSITORY_URL": "https://github.com/example/project.git",
        "FACTORY_INSTANCE": "factory-1",
        "FACTORY_IMAGE_ID_FILE": str(image),
        "FACTORY_TOKEN_FILE": str(token),
    }

    _, boundaries = boundaries_from_environment(environ, hosting=FakeHostingService())

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
