"""The preflight's item for the kernel's write guard: Landlock's ABI and the wrapper on `PATH`."""

from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.preflight import confinement_item
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_preflight
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone

KERNEL_ADVICE = (
    ": update the kernel (on WSL: wsl --update), or allow the Landlock system calls"
    " in the container runtime's seccomp profile"
)
ABI_0 = "the kernel offers Landlock ABI 0, the write guard needs ABI 3 or higher" + KERNEL_ADVICE
ABI_2 = "the kernel offers Landlock ABI 2, the write guard needs ABI 3 or higher" + KERNEL_ADVICE
NOT_ON_PATH = "factory-confine is not on the agent run's PATH /usr/bin"
ON_PATH = {"PATH": "/usr/bin"}


def _found(name: str, path: str) -> str | None:
    return f"{path.split(':', maxsplit=1)[0]}/{name}"


def _not_found(_name: str, _path: str) -> str | None:
    return None


def _every_tool(name: str) -> str | None:
    return f"/usr/bin/{name}"


@pytest.mark.parametrize(
    ("abi", "environment", "find", "expected"),
    [
        pytest.param(
            3, ON_PATH, _found, PreflightItem(name="confinement", passed=True), id="abi-3"
        ),
        pytest.param(
            7, ON_PATH, _found, PreflightItem(name="confinement", passed=True), id="abi-7"
        ),
        pytest.param(
            0,
            ON_PATH,
            _found,
            PreflightItem(name="confinement", passed=False, detail=ABI_0),
            id="abi-0",
        ),
        pytest.param(
            2,
            ON_PATH,
            _found,
            PreflightItem(name="confinement", passed=False, detail=ABI_2),
            id="abi-2",
        ),
        pytest.param(
            7,
            ON_PATH,
            _not_found,
            PreflightItem(name="confinement", passed=False, detail=NOT_ON_PATH),
            id="not-on-path",
        ),
        pytest.param(
            7,
            {},
            _found,
            PreflightItem(name="confinement", passed=False, detail="the agent run has no PATH"),
            id="no-path",
        ),
    ],
)
def test_the_item_passes_with_landlock_abi_3_and_the_wrapper_on_path_and_names_each_fault(
    *,
    abi: int,
    environment: Mapping[str, str],
    find: Callable[[str, str], str | None],
    expected: PreflightItem,
) -> None:
    item = confinement_item(lambda: abi, environment, find)

    assert item == expected


def test_the_kernels_fault_comes_before_the_wrappers() -> None:
    item = confinement_item(lambda: 2, ON_PATH, _not_found)

    assert not item.passed
    assert item.detail == f"{ABI_2}; {NOT_ON_PATH}"


def test_the_wrapper_is_looked_for_on_the_environments_path() -> None:
    calls: list[tuple[str, str]] = []

    def find(name: str, path: str) -> str | None:
        calls.append((name, path))
        return f"/opt/factory/.venv/bin/{name}"

    confinement_item(lambda: 7, {"PATH": "/opt/factory/.venv/bin:/usr/bin"}, find)

    assert calls == [("factory-confine", "/opt/factory/.venv/bin:/usr/bin")]


def test_a_failed_confinement_item_stops_the_machine_before_any_agent_run(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    remote: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    human.push_file("main", "Makefile", "lint:\n\ttrue\n")
    boundaries.git.fetch()
    settings = InstanceSettings(
        repository_url=str(remote),
        instance="factory-1",
        image="build-7",
        checkout=tmp_path / "instance-checkout",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        claude_executable=str(tmp_path / "no-claude"),
        pinned_agent_version="fake",
    )
    environment = {"PATH": "/usr/bin", "HOME": str(tmp_path)}
    preflight = build_preflight(
        boundaries,
        settings,
        _every_tool,
        [lambda: confinement_item(lambda: 2, environment, _found)],
    )

    reason = preflight.run()

    assert reason == "preflight_failed"
    [stop] = boundaries.health.read().stops
    assert (stop.scope, stop.reason) == ("machine", "preflight_failed")
    assert f"confinement: {ABI_2}" in stop.detail
    assert agent_runtime.requests() == []
