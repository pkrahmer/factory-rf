"""The pipeline definition is loaded at a git ref, its agents checked, a refusal reported."""

import dataclasses
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.machine import HealthStatusStore
from factory.application.pipeline_loading import PIPELINE_REF, PipelineLoader
from factory.application.stops import StopService
from factory.domain.errors import GitError, PipelineDefinitionInvalid
from factory.domain.stops import HealthStatus, RepositoryStop
from git_support import CHECKOUT, PIPELINE_YAML, clone, install_agents, run_git
from human_clone import HumanClone
from log_support import log_lines

PIPELINE_FILE = "factory/pipeline.yml"
ROLES = [
    "intake",
    "tester",
    "coder",
    "reviewer",
    "documenter",
    "smoke-tester",
    "acceptance-reviewer",
]
WITHOUT_CONTRACT = PIPELINE_YAML.replace('contract: "1.0"\n', "")
STAMP = "2026-10-12T12:00:00Z"


class _UnwritableHealth(HealthStatusStore):
    """A health status store that reads an empty status and refuses every write."""

    @override
    def read(self) -> HealthStatus:
        return HealthStatus(stops=[])

    @override
    def write(self, status: HealthStatus) -> None:
        raise OSError("the health status cannot be written")


def _push(human: HumanClone, checkout: GitCli, branch: str, text: str) -> None:
    human.push_file(branch, PIPELINE_FILE, text)
    checkout.fetch()


def _stop(detail: str, clock: ManualClock) -> RepositoryStop:
    return RepositoryStop(
        scope="repository", reason="pipeline_definition_invalid", detail=detail, at=clock.now()
    )


def _refused(loader: PipelineLoader, ref: str = PIPELINE_REF) -> str:
    with pytest.raises(PipelineDefinitionInvalid) as caught:
        loader.load(ref)
    return caught.value.fault


def test_the_pipeline_ref_is_main_on_the_remote() -> None:
    assert PIPELINE_REF == "origin/main"


def test_load_reads_main_on_the_remote_not_the_work_tree(
    boundaries: Boundaries, agent_home: Path, tmp_path: Path
) -> None:
    install_agents(agent_home, ROLES)
    work_tree_file = tmp_path / CHECKOUT / PIPELINE_FILE
    work_tree_file.write_text(
        PIPELINE_YAML.replace("attempts_cap: 2", "attempts_cap: 5"), encoding="utf-8"
    )

    definition = PipelineLoader(boundaries).load()

    assert definition.attempts_cap == 2


def test_load_at_a_branch_reads_the_file_on_that_branch(
    boundaries: Boundaries, agent_home: Path, human: HumanClone, checkout: GitCli
) -> None:
    install_agents(agent_home, ROLES)
    _push(human, checkout, "other", PIPELINE_YAML.replace("attempts_cap: 2", "attempts_cap: 4"))

    definition = PipelineLoader(boundaries).load("origin/other")

    assert definition.attempts_cap == 4


def test_a_definition_without_contract_is_refused_with_its_fault(
    boundaries: Boundaries, agent_home: Path, human: HumanClone, checkout: GitCli
) -> None:
    install_agents(agent_home, ROLES)
    _push(human, checkout, "main", WITHOUT_CONTRACT)

    assert _refused(PipelineLoader(boundaries)) == "missing key: contract"


def test_a_refusal_raises_one_stop_and_writes_its_line(
    boundaries: Boundaries,
    *,
    agent_home: Path,
    human: HumanClone,
    checkout: GitCli,
    clock: ManualClock,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, ROLES)
    _push(human, checkout, "main", WITHOUT_CONTRACT)
    clock.advance(timedelta(seconds=5))

    _refused(PipelineLoader(boundaries))

    assert boundaries.health.read().stops == [_stop("missing key: contract", clock)]
    assert log_lines(tmp_path) == [
        "2026-10-12T12:00:05Z stop repository pipeline_definition_invalid: missing key: contract"
    ]


def test_a_refusal_opens_no_pull_request_and_posts_nothing(
    boundaries: Boundaries,
    agent_home: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
) -> None:
    install_agents(agent_home, ROLES)
    _push(human, checkout, "main", WITHOUT_CONTRACT)

    _refused(PipelineLoader(boundaries))

    assert hosting.pull_requests() == []


def test_a_missing_key_with_a_default_takes_the_default(
    boundaries: Boundaries, agent_home: Path, human: HumanClone, checkout: GitCli, tmp_path: Path
) -> None:
    install_agents(agent_home, ROLES)
    _push(human, checkout, "main", PIPELINE_YAML.replace("crash_cap: 2\n", ""))

    definition = PipelineLoader(boundaries).load()

    assert definition.crash_cap == 2
    assert {role.lease_duration for role in definition.roles.values()} == {60}
    assert list(definition.roles) == ROLES
    assert boundaries.health.read().stops == []
    assert log_lines(tmp_path) == []


def test_a_definition_missing_on_main_is_refused_and_stops(
    boundaries: Boundaries,
    *,
    agent_home: Path,
    remote: Path,
    checkout: GitCli,
    clock: ManualClock,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, ROLES)
    remover = clone(remote, tmp_path / "remover")
    run_git(remover, "rm", "-q", PIPELINE_FILE)
    run_git(remover, "commit", "-q", "-m", "remove the pipeline definition")
    run_git(remover, "push", "-q", "origin", "main")
    checkout.fetch()

    fault = _refused(PipelineLoader(boundaries))

    assert fault == "factory/pipeline.yml is missing at origin/main"
    assert boundaries.health.read().stops == [_stop(fault, clock)]


def test_a_successful_load_clears_the_stop_and_keeps_other_stops(
    boundaries: Boundaries, agent_home: Path, clock: ManualClock, tmp_path: Path
) -> None:
    loader = PipelineLoader(boundaries)
    _refused(loader)
    fetch_stop = RepositoryStop(
        scope="repository", reason="fetch_failed", detail="origin unreachable", at=clock.now()
    )
    StopService(boundaries).raise_stop(fetch_stop)
    install_agents(agent_home, ROLES)

    loader.load()

    assert boundaries.health.read().stops == [fetch_stop]
    assert log_lines(tmp_path)[-1] == f"{STAMP} stop cleared pipeline_definition_invalid"


@pytest.mark.parametrize("case", ["git_fails", "unknown_ref"])
def test_a_git_error_propagates_and_raises_no_stop(
    case: str, boundaries: Boundaries, agent_home: Path, tmp_path: Path
) -> None:
    install_agents(agent_home, ROLES)
    if case == "git_fails":
        failing = GitCli(tmp_path / "nowhere")
        loader = PipelineLoader(dataclasses.replace(boundaries, git=failing))
        ref = PIPELINE_REF
    else:
        loader = PipelineLoader(boundaries)
        ref = "origin/nowhere"

    with pytest.raises(GitError):
        loader.load(ref)

    assert boundaries.health.read().stops == []
    assert log_lines(tmp_path) == []


@pytest.mark.parametrize(
    ("missing", "expected"),
    [
        (["coder"], "role coder: agent is not installed"),
        (
            ["reviewer", "tester"],
            "role tester: agent is not installed; role reviewer: agent is not installed",
        ),
    ],
)
def test_roles_without_an_installed_agent_are_refused_in_role_order(
    missing: list[str],
    expected: str,
    boundaries: Boundaries,
    agent_home: Path,
    clock: ManualClock,
) -> None:
    install_agents(agent_home, [role for role in ROLES if role not in missing])

    fault = _refused(PipelineLoader(boundaries))

    assert fault == expected
    assert boundaries.health.read().stops == [_stop(expected, clock)]


def test_installed_agents_for_every_role_load_and_extra_agents_do_not_matter(
    boundaries: Boundaries, agent_home: Path, tmp_path: Path
) -> None:
    install_agents(agent_home, [*ROLES, "linguist"])

    definition = PipelineLoader(boundaries).load()

    assert definition.first_stage() == "intake"
    assert boundaries.health.read().stops == []
    assert log_lines(tmp_path) == []


def test_an_unavailable_agent_home_is_refused_and_stops(
    boundaries: Boundaries, clock: ManualClock
) -> None:
    fault = _refused(PipelineLoader(boundaries))

    assert fault.startswith("agent home unavailable: ")
    assert boundaries.health.read().stops == [_stop(fault, clock)]


@pytest.mark.parametrize("case", ["missing_contract", "agent_not_installed"])
def test_a_refusal_at_another_ref_raises_but_changes_no_stop(
    case: str,
    boundaries: Boundaries,
    *,
    agent_home: Path,
    human: HumanClone,
    checkout: GitCli,
    tmp_path: Path,
) -> None:
    if case == "missing_contract":
        install_agents(agent_home, ROLES)
        text, expected = WITHOUT_CONTRACT, "missing key: contract"
    else:
        install_agents(agent_home, [role for role in ROLES if role != "coder"])
        text = PIPELINE_YAML.replace("attempts_cap: 2", "attempts_cap: 3")
        expected = "role coder: agent is not installed"
    _push(human, checkout, "other", text)

    fault = _refused(PipelineLoader(boundaries), "origin/other")

    assert fault == expected
    assert boundaries.health.read() == HealthStatus(stops=[])
    assert log_lines(tmp_path) == []


def test_a_successful_load_at_another_ref_leaves_the_stop_in_place(
    boundaries: Boundaries,
    agent_home: Path,
    human: HumanClone,
    checkout: GitCli,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, ROLES)
    _push(human, checkout, "main", WITHOUT_CONTRACT)
    loader = PipelineLoader(boundaries)
    _refused(loader)
    status = boundaries.health.read()
    lines = log_lines(tmp_path)
    _push(human, checkout, "other", PIPELINE_YAML.replace("attempts_cap: 2", "attempts_cap: 3"))

    loader.load("origin/other")

    assert boundaries.health.read() == status
    assert [stop.reason for stop in status.stops] == ["pipeline_definition_invalid"]
    assert log_lines(tmp_path) == lines


def test_an_unwritable_health_status_raises_os_error_after_the_stop_line(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    loader = PipelineLoader(dataclasses.replace(boundaries, health=_UnwritableHealth()))

    with pytest.raises(OSError, match="cannot be written"):
        loader.load()

    lines = log_lines(tmp_path)
    assert len(lines) == 1
    assert lines[0].startswith(
        f"{STAMP} stop repository pipeline_definition_invalid: agent home unavailable: "
    )


def test_the_agents_are_checked_only_when_the_text_is_valid(
    boundaries: Boundaries, human: HumanClone, checkout: GitCli, clock: ManualClock
) -> None:
    _push(human, checkout, "main", WITHOUT_CONTRACT)

    fault = _refused(PipelineLoader(boundaries))

    assert fault == "missing key: contract"
    assert boundaries.health.read().stops == [_stop(fault, clock)]
