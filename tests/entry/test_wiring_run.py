"""The wiring of one instance's run: its tick and the boundaries read from the environment."""

import tempfile
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.agent_runs import AgentRunResult
from factory.domain.errors import SettingsInvalid
from factory.domain.identifiers import branch_name
from factory.domain.settings import InstanceSettings, read_settings
from factory.entry.wiring import (
    agent_run_environment,
    boundaries_from_environment,
    build_tick,
    production_environment,
)
from git_support import PIPELINE_YAML, install_agents, remote_commit, run_git
from human_clone import HumanClone
from wiring_support import every_tool

INSTANCE = "factory-7"
WORK_ITEM = "F0001-S0001"
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
STORY = """\
# First story

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal
"""
PROBE = AgentRunResult(
    end_reason="completed", decision="question", entry="probe", duration=timedelta(seconds=5)
)
COMPLETED = AgentRunResult(
    end_reason="completed", decision="tests", entry="checked.", duration=timedelta(minutes=1)
)


@pytest.fixture
def settings(tmp_path: Path, remote: Path, agent_home: Path) -> InstanceSettings:
    """Return settings of `factory-7` whose checkout and state lie in `tmp_path`."""
    return InstanceSettings(
        repository_url=str(remote),
        instance=INSTANCE,
        checkout=tmp_path / "instance-checkout",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        claude_executable=str(tmp_path / "no-claude"),
    )


def test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance(
    boundaries: Boundaries,
    settings: InstanceSettings,
    *,
    remote: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    human.push_file("main", "Makefile", "lint:\n\ttrue\nsync:\n\t@:\n")
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    token_file = tmp_path / "hosting-token"
    token_file.write_text("example-value\n", encoding="utf-8")
    token_file.chmod(0o600)
    agent_runtime.queue(ScriptedRun(result=PROBE))
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    ready = settings.model_copy(update={"pinned_agent_version": "fake", "token_file": token_file})
    tick = build_tick(boundaries, ready, every_tool)

    outcome = tick.run()

    assert outcome.event is not None
    assert (outcome.event.kind, outcome.dispatch) == ("run", "handled")
    request = agent_runtime.requests()[-1]
    assert request.environment == agent_run_environment(ready, production_environment())
    assert build_tick(boundaries, ready, every_tool) is not build_tick(
        boundaries, ready, every_tool
    )
    branch = branch_name(WORK_ITEM)
    assert remote_commit(remote, branch) is not None
    # The completed stage released its claim at the tip; the claim commit comes first after main.
    claim_commit = run_git(remote, "rev-list", "--reverse", f"main..{branch}").split()[0]
    text = boundaries.git.show_file(claim_commit, PATH)
    assert text is not None
    state = boundaries.work_item_reader.parse(text).state
    assert state is not None
    assert state.claim is not None
    assert state.claim.instance == INSTANCE


def test_boundaries_from_environment_reads_the_settings_and_builds_their_boundaries(
    hosted_environment: dict[str, str], hosting: FakeHostingService
) -> None:
    settings, boundaries = boundaries_from_environment(hosted_environment, hosting=hosting)

    assert settings == read_settings(hosted_environment, read_file=Path.read_text).model_copy(
        update={"temporary_directory": Path(tempfile.gettempdir())}
    )
    assert boundaries.settings == settings


@pytest.mark.parametrize(
    ("changes", "with_hosting", "variable"),
    [
        pytest.param({"FACTORY_TOKEN_FILE": "missing"}, True, "FACTORY_TOKEN_FILE", id="token"),
        pytest.param({"FACTORY_INSTANCE": None}, True, "FACTORY_INSTANCE", id="instance"),
        pytest.param(
            {"FACTORY_REPOSITORY_URL": "/srv/project.git"},
            False,
            "FACTORY_REPOSITORY_URL",
            id="url-without-owner-and-name",
        ),
    ],
)
def test_boundaries_from_environment_refuses_an_invalid_environment(
    hosted_environment: dict[str, str],
    hosting: FakeHostingService,
    tmp_path: Path,
    *,
    changes: dict[str, str | None],
    with_hosting: bool,
    variable: str,
) -> None:
    changed = dict(hosted_environment)
    for name, value in changes.items():
        if value is None:
            del changed[name]
        else:
            changed[name] = str(tmp_path / value) if name == "FACTORY_TOKEN_FILE" else value

    with pytest.raises(SettingsInvalid) as raised:
        boundaries_from_environment(changed, hosting=hosting if with_hosting else None)

    assert raised.value.variable == variable
