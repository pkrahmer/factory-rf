"""A sealed run given its own runner calls it instead of the runtime, sealed as ever."""

import stat
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from application.test_sealed_runs import (
    ENVIRONMENT,
    OPEN_FILE,
    OPEN_FOLDER,
    Swap,
    _leave,
    _swap_for_folder,
)
from factory.adapters.clock import ManualClock, ManualWaiter
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.application.sealed_runs import run_sealed
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.errors import RepositoryUnsealed
from factory.domain.settings import InstanceSettings
from git_support import install_agents
from sealed_run_support import COMPLETED, run_request


class Runner:
    """Records each request and the modes of `.git` it saw, does `swap`, then completes."""

    def __init__(self, checkout: Path, swap: Swap) -> None:
        self._checkout = checkout
        self._swap = swap
        self.requests: list[AgentRunRequest] = []
        self.modes: list[tuple[int, int]] = []

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        folder = self._checkout / ".git"
        self.requests.append(request)
        self.modes.append(
            (
                stat.S_IMODE(folder.lstat().st_mode),
                stat.S_IMODE((folder / "config").lstat().st_mode),
            )
        )
        self._swap(self._checkout)
        return COMPLETED


@pytest.mark.parametrize(
    ("swap", "unsealed"),
    [
        pytest.param(_leave, False, id="sealed"),
        pytest.param(_swap_for_folder, True, id="swapped"),
    ],
)
def test_a_sealed_run_calls_its_runner_instead_of_the_runtime(
    boundaries: Boundaries, agent_runtime: FakeAgentRuntime, *, swap: Swap, unsealed: bool
) -> None:
    folder = boundaries.checkout / ".git"
    folder.chmod(OPEN_FOLDER)
    (folder / "config").chmod(OPEN_FILE)
    runner = Runner(boundaries.checkout, swap)
    request = run_request(boundaries.checkout)

    if unsealed:
        with pytest.raises(RepositoryUnsealed):
            run_sealed(boundaries, request, run=runner.run)
    else:
        assert run_sealed(boundaries, request, run=runner.run).result == COMPLETED

    assert runner.requests == [request]
    assert runner.modes == [(0o2755, 0o644)]
    assert agent_runtime.requests() == []


def test_the_probe_does_not_wait_out_a_provider_limit(
    boundaries: Boundaries,
    *,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    clock: ManualClock,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, ["coder"])
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
    )
    limited = AgentRunResult(
        end_reason="provider_limit", duration=timedelta(seconds=5), session="ses_a"
    )
    agent_runtime.queue(ScriptedRun(result=limited))
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    waiter = ManualWaiter(clock)
    patient = replace(boundaries, waiter=waiter, settings=settings)

    item = agent_run_probe_item(patient, settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert not item.passed
    assert item.detail is not None
    assert item.detail.startswith("the probe run ended provider_limit; ")
    assert len(agent_runtime.requests()) == 1
    assert waiter.waits == []
