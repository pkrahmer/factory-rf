"""The wiring of one instance's run: its tick and the boundaries read from the environment."""

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
from factory.entry.wiring import boundaries_from_environment, build_tick, production_environment
from git_support import PIPELINE_YAML, install_agents, remote_commit, run_git
from human_clone import HumanClone

INSTANCE = "factory-7"
WORK_ITEM = "F0001-S0001"
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
HOSTED_URL = "https://github.com/example/project.git"
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


@pytest.fixture
def environment(tmp_path: Path) -> dict[str, str]:
    """Return a valid environment whose token and image identity files lie in `tmp_path`."""
    token = tmp_path / "hosting-token"
    token.write_text("example-value\n", encoding="utf-8")
    image = tmp_path / "image-id"
    image.write_text("build-7\n", encoding="utf-8")
    return {
        "FACTORY_REPOSITORY_URL": HOSTED_URL,
        "FACTORY_INSTANCE": "factory-1",
        "FACTORY_IMAGE_ID_FILE": str(image),
        "FACTORY_TOKEN_FILE": str(token),
    }


def test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance(
    boundaries: Boundaries,
    settings: InstanceSettings,
    *,
    remote: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    tick = build_tick(boundaries, settings)

    outcome = tick.run()

    assert outcome.event is not None
    assert (outcome.event.kind, outcome.dispatch) == ("run", "handled")
    [request] = agent_runtime.requests()
    assert request.environment == production_environment()
    assert build_tick(boundaries, settings) is not build_tick(boundaries, settings)
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
    environment: dict[str, str], hosting: FakeHostingService
) -> None:
    settings, boundaries = boundaries_from_environment(environment, hosting=hosting)

    assert settings == read_settings(environment, read_file=Path.read_text)
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
    environment: dict[str, str],
    hosting: FakeHostingService,
    tmp_path: Path,
    *,
    changes: dict[str, str | None],
    with_hosting: bool,
    variable: str,
) -> None:
    changed = dict(environment)
    for name, value in changes.items():
        if value is None:
            del changed[name]
        else:
            changed[name] = str(tmp_path / value) if name == "FACTORY_TOKEN_FILE" else value

    with pytest.raises(SettingsInvalid) as raised:
        boundaries_from_environment(changed, hosting=hosting if with_hosting else None)

    assert raised.value.variable == variable
