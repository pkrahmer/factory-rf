"""The production wiring of one instance: its settings and token turned into its boundaries."""

import json
import os
import shutil
from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import github
import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.clock import SystemClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.disk_space import ShutilDiskSpace
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.pygithub_hosting import PyGithubHostingService
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.project_agents import ProjectAgentDefinitions
from factory.application.project_commands import RecordingProjectCommands
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.errors import SettingsInvalid
from factory.domain.git import GitIdentity
from factory.domain.settings import InstanceSettings, read_settings
from factory.domain.stops import HealthStatus
from factory.entry.wiring import (
    build_boundaries,
    git_environment,
    git_options,
    read_hosting_token,
    repository_name,
)
from git_support import clone, install_agents, write_executable
from wiring_support import CREDENTIAL, with_dataset

GITHUB_URL = "https://github.com/owner/project.git"
LOCAL_URL = "/srv/project.git"
REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.25,
        "duration_ms": 1200,
        "usage": {"input_tokens": 10, "output_tokens": 5},
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
)


@pytest.fixture
def settings(tmp_path: Path) -> InstanceSettings:
    """Settings whose checkout, state directory and agent home lie in `tmp_path`; none exists."""
    root = tmp_path.resolve()
    return with_dataset(
        InstanceSettings(
            repository_url=LOCAL_URL,
            instance="factory-1",
            checkout=root / "checkout",
            state_directory=root / "state",
            agent_home=root / "agents-home",
        ),
        tmp_path,
    )


def _record_get_repo(monkeypatch: pytest.MonkeyPatch) -> list[tuple[object, ...]]:
    repositories: list[tuple[object, ...]] = []
    original: Callable[..., object] = github.Github.get_repo

    def recording(self: github.Github, *args: object, **kwargs: object) -> object:
        repositories.append((*args, *kwargs.values()))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(github.Github, "get_repo", recording)
    return repositories


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/owner/project.git", "owner/project"),
        ("https://github.com/owner/project", "owner/project"),
        ("https://github.com/owner/project/", "owner/project"),
        ("git@github.com:owner/project.git", "owner/project"),
        ("git@github.com:owner/project", "owner/project"),
        ("ssh://git@github.com/owner/project.git", "owner/project"),
        ("https://github.com/my.org/my_project-2.git", "my.org/my_project-2"),
        ("https://git.example.com/owner/project.git", "owner/project"),
    ],
)
def test_repository_name_is_read_from_the_url(url: str, expected: str) -> None:
    assert repository_name(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "/srv/project.git",
        "https://github.com/project.git",
        "https://github.com/a/b/c.git",
        "https://github.com/owner/pro*ject.git",
    ],
)
def test_a_url_without_owner_and_name_is_refused(url: str) -> None:
    with pytest.raises(SettingsInvalid) as raised:
        repository_name(url)

    assert raised.value.variable == "FACTORY_REPOSITORY_URL"


def test_the_hosting_token_is_the_file_content_without_surrounding_whitespace(
    tmp_path: Path,
) -> None:
    path = tmp_path / "token"
    path.write_text("example-value\n", encoding="utf-8")

    assert read_hosting_token(path) == "example-value"


@pytest.mark.parametrize("case", ["none", "missing", "directory", "whitespace"])
def test_a_hosting_token_that_cannot_be_read_is_refused(tmp_path: Path, case: str) -> None:
    path: Path | None = tmp_path / "token"
    if case == "none":
        path = None
    elif case == "directory":
        (tmp_path / "token").mkdir()
    elif case == "whitespace":
        (tmp_path / "token").write_text("  \n\t\n", encoding="utf-8")

    with pytest.raises(SettingsInvalid) as raised:
        read_hosting_token(path)

    assert raised.value.variable == "FACTORY_TOKEN_FILE"


@pytest.mark.parametrize(
    ("helper", "expected_helper"),
    [
        (None, "/usr/local/bin/git-credential-factory"),
        ("/opt/other-helper", "/opt/other-helper"),
    ],
)
def test_git_environment_gives_the_credential_helper_and_no_hooks(
    helper: str | None, expected_helper: str
) -> None:
    environment = git_environment() if helper is None else git_environment(helper)

    assert environment == {
        "GIT_CONFIG_COUNT": "3",
        "GIT_CONFIG_KEY_0": "credential.helper",
        "GIT_CONFIG_VALUE_0": expected_helper,
        "GIT_CONFIG_KEY_1": "core.hooksPath",
        "GIT_CONFIG_VALUE_1": "/dev/null",
        "GIT_CONFIG_KEY_2": "core.fsmonitor",
        "GIT_CONFIG_VALUE_2": "false",
    }


def test_git_options_carry_the_settings_identity_and_the_git_environment() -> None:
    settings = read_settings(
        {
            "FACTORY_REPOSITORY_URL": LOCAL_URL,
            "FACTORY_INSTANCE": "factory-1",
            "GIT_USER_NAME": "Ann",
        }
    )

    options = git_options(settings)

    assert options.identity == settings.git_identity
    assert options.identity.name == "Ann"
    assert options.environment == git_environment()


def test_build_boundaries_uses_the_given_hosting_checkout_and_settings(
    settings: InstanceSettings,
) -> None:
    fake = FakeHostingService()

    boundaries = build_boundaries(settings, CREDENTIAL, hosting=fake)

    assert boundaries.hosting is fake
    assert boundaries.checkout == settings.checkout
    assert boundaries.settings is settings


def test_build_boundaries_picks_the_concrete_adapters_and_writes_nothing(
    settings: InstanceSettings,
) -> None:
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    assert isinstance(boundaries.git, GitCli)
    assert isinstance(boundaries.agent_runtime, ClaudeCodeRuntime)
    assert isinstance(boundaries.project_commands, RecordingProjectCommands)
    assert isinstance(boundaries.work_item_reader, FrontmatterWorkItemReader)
    assert isinstance(boundaries.work_item_writer, FrontmatterWorkItemWriter)
    assert isinstance(boundaries.cost_reader, JsonLinesCostRecordReader)
    assert isinstance(boundaries.cost_writer, JsonLinesCostRecordWriter)
    assert isinstance(boundaries.pipeline_reader, RuamelPipelineDefinitionReader)
    assert isinstance(boundaries.agent_definitions, ProjectAgentDefinitions)
    assert isinstance(boundaries.clock, SystemClock)
    assert isinstance(boundaries.log, TimestampedFactoryLog)
    assert isinstance(boundaries.health, JsonHealthStatusFile)
    assert not settings.state_directory.exists()
    assert not settings.checkout.exists()


def test_the_built_boundaries_read_the_disk(settings: InstanceSettings) -> None:
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    assert isinstance(boundaries.disk, ShutilDiskSpace)


def test_the_built_git_runs_with_the_git_options_of_the_settings(
    tmp_path: Path, remote: Path, settings: InstanceSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = clone(remote, settings.checkout)
    seen = tmp_path / "git-environment.json"
    real_git = shutil.which("git")
    assert real_git is not None
    folder = tmp_path / "stand-in-bin"
    folder.mkdir()
    stand_in = write_executable(
        folder,
        "import json, os, sys\n"
        f"open({str(seen)!r}, 'w', encoding='utf-8').write(json.dumps(dict(os.environ)))\n"
        f"os.execv({real_git!r}, [{real_git!r}, *sys.argv[1:]])",
    )
    stand_in.rename(folder / "git")
    monkeypatch.setenv("PATH", f"{folder}{os.pathsep}{os.environ['PATH']}")
    (checkout / "note.md").write_text("A note.\n", encoding="utf-8")
    identity = GitIdentity(name="Ann", email="ann@example.invalid")
    boundaries = build_boundaries(
        settings.model_copy(update={"git_identity": identity}),
        CREDENTIAL,
        hosting=FakeHostingService(),
    )

    boundaries.git.commit("Add a note")

    environment = json.loads(seen.read_text(encoding="utf-8"))
    assert environment["GIT_AUTHOR_NAME"] == "Ann"
    assert environment["GIT_CONFIG_KEY_0"] == "credential.helper"
    assert environment["GIT_CONFIG_VALUE_0"] == "/usr/local/bin/git-credential-factory"
    assert environment["GIT_CONFIG_KEY_1"] == "core.hooksPath"
    assert environment["GIT_CONFIG_VALUE_1"] == "/dev/null"
    assert environment["GIT_CONFIG_KEY_2"] == "core.fsmonitor"
    assert environment["GIT_CONFIG_VALUE_2"] == "false"


def test_the_built_project_commands_run_in_the_checkout(settings: InstanceSettings) -> None:
    settings.checkout.mkdir()
    (settings.checkout / "Makefile").write_text("lint:\n\t@pwd\n", encoding="utf-8")
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    result = boundaries.project_commands.run("lint", time_limit=timedelta(seconds=30))

    assert result.last_line == str(settings.checkout)


def test_the_built_agent_definitions_are_read_from_the_agent_home(
    tmp_path: Path, remote: Path, monkeypatch: pytest.MonkeyPatch, settings: InstanceSettings
) -> None:
    GitCli(settings.checkout).clone(str(remote))
    home = tmp_path / "home"
    install_agents(home / ".claude", ["intruder"])
    monkeypatch.setenv("HOME", str(home))
    install_agents(settings.agent_home, ["coder", "tester"])
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    assert boundaries.agent_definitions.names() == ["coder", "tester"]


def test_the_built_log_and_health_file_lie_in_the_state_directory(
    settings: InstanceSettings,
) -> None:
    settings.state_directory.mkdir()
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    boundaries.log.line("x")
    boundaries.health.write(HealthStatus())

    log = (settings.state_directory / "factory.log").read_text(encoding="utf-8")
    assert log.splitlines()[-1].endswith(" x")
    assert (settings.state_directory / "health.json").exists()


def test_the_built_agent_runtime_keeps_its_run_files_under_runs(
    tmp_path: Path, settings: InstanceSettings
) -> None:
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=REPLY)])
    work = tmp_path / "work"
    work.mkdir()
    instructions = "Write the code."
    request = AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Read"],
            effort=None,
            budget_usd=Decimal("1"),
            instructions=instructions,
        ),
        prompt="Stage: doing",
        allowed_decisions=["doing", "question"],
        time_limit=timedelta(seconds=30),
        working_directory=work,
        environment={},
    )
    boundaries = build_boundaries(
        settings.model_copy(update={"claude_executable": str(executable)}),
        CREDENTIAL,
        hosting=FakeHostingService(),
    )

    boundaries.agent_runtime.run(request)

    calls = read_calls(tmp_path / "bin")
    assert len(calls) == 1
    parents = [Path(path).parent for path, text in calls[0].files.items() if text == instructions]
    assert parents == [settings.state_directory / "runs"]


def test_build_boundaries_refuses_a_url_without_owner_and_name(
    settings: InstanceSettings,
) -> None:
    with pytest.raises(SettingsInvalid) as raised:
        build_boundaries(settings, CREDENTIAL)

    assert raised.value.variable == "FACTORY_REPOSITORY_URL"
    assert not settings.state_directory.exists()


def test_build_boundaries_without_hosting_hands_pygithub_the_repository(
    monkeypatch: pytest.MonkeyPatch, settings: InstanceSettings
) -> None:
    repositories = _record_get_repo(monkeypatch)

    boundaries = build_boundaries(
        settings.model_copy(update={"repository_url": GITHUB_URL}), CREDENTIAL
    )

    assert isinstance(boundaries.hosting, PyGithubHostingService)
    assert repositories == [("owner/project",)]
