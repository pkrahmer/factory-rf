"""The wiring hands the operator's extra names and CA bundle to every container of a stage."""

import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from container_extra_support import CA_NAMES, COMMIT, OTHER, PROXY, env_words, volume, write_bundle
from entry.test_wiring_login import REPLY
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.project_commands import RecordingProjectCommands
from factory.application.stage_environment import stage_environment_of
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from git_support import CHECKOUT, write_executable
from podman_support import IMAGE
from wiring_support import CREDENTIAL
from zfs_support import DATASET


def _recording(folder: Path, *, printed: str = "") -> Path:
    folder.mkdir(parents=True)
    calls = folder / "calls"
    return write_executable(
        folder,
        "import json, sys\n"
        f"with open({str(calls)!r}, 'a', encoding='utf-8') as file:\n"
        "    file.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        f"sys.stdout.write({printed!r})\n",
    )


def _calls(executable: Path) -> list[list[str]]:
    lines = (executable.parent / "calls").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def _request(tmp_path: Path) -> AgentRunRequest:
    work = tmp_path / "request-work"
    work.mkdir()
    return AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Read"],
            budget_usd=Decimal("1"),
            instructions="Write the code.",
        ),
        prompt="Stage: doing",
        allowed_decisions=["doing", "question"],
        time_limit=timedelta(seconds=30),
        working_directory=work,
        environment={"HOME": "/work/home", "LANG": "C.UTF-8", "PATH": "/usr/bin:/bin"},
    )


@pytest.mark.usefixtures("checkout")
@pytest.mark.parametrize("runtime", ["claude", "opencode"])
def test_every_container_of_a_stage_carries_both_settings_and_no_hosting_token(
    tmp_path: Path,
    agent_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime: str,
) -> None:
    monkeypatch.setenv("HTTPS_PROXY", PROXY)
    monkeypatch.setenv(OTHER, "x")
    zfs = _recording(tmp_path / "zfs-bin")
    podman = _recording(tmp_path / "podman-bin", printed=REPLY)
    bundle = write_bundle(tmp_path)
    workspace = tmp_path / "work"
    workspace.mkdir()
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=tmp_path / CHECKOUT,
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        dataset=DATASET,
        workspace=workspace,
        stage_image=IMAGE,
        zfs_executable=str(zfs),
        podman_executable=str(podman),
        agent_runtime=runtime,
        container_env=("HTTPS_PROXY",),
        ca_bundle=bundle,
        opencode_models={"sonnet": "anthropic/claude-sonnet"} if runtime == "opencode" else {},
    )
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())
    project_commands = boundaries.project_commands
    assert isinstance(project_commands, RecordingProjectCommands)

    stage_environment_of(boundaries).prepare(COMMIT, "main", sync_time_limit=timedelta(minutes=5))
    boundaries.agent_runtime.run(_request(tmp_path))
    project_commands.inner.run("check", time_limit=timedelta(minutes=1))

    calls = [words for words in _calls(podman) if words[:1] == ["run"]]
    assert len(calls) == 3
    for words in calls:
        environment = env_words(words)
        assert environment["HTTPS_PROXY"] == PROXY
        assert OTHER not in environment
        assert {name: environment[name] for name in CA_NAMES} == dict.fromkeys(
            CA_NAMES, str(bundle)
        )
        assert volume(bundle) in words
        assert not any(CREDENTIAL in word for word in words)
