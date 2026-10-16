"""The `claude -p` runtime hands the agent only the request's environment and its switches."""

import json
import os
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from factory.adapters.claude_runtime import SWITCHES, ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, scrub_environment
from factory.domain.hosting import PostKey
from git_support import CHECKOUT, commit_all, run_git, write_files

BRANCH = "work-item/F0001-S0001"
GIVEN = {"HOME": "/home/factory", "LANG": "C.UTF-8"}
REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.1,
        "duration_ms": 100,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
)


def _request(tmp_path: Path, environment: dict[str, str]) -> AgentRunRequest:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
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
        environment=environment,
    )


def _runtime(tmp_path: Path) -> ClaudeCodeRuntime:
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=REPLY)])
    return ClaudeCodeRuntime(str(executable), tmp_path / "state")


def test_the_agent_gets_the_request_environment_and_the_switches_and_no_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GH_TOKEN", "example-value")

    _runtime(tmp_path).run(_request(tmp_path, GIVEN))

    [call] = read_calls(tmp_path / "bin")
    seen = {name: value for name, value in call.environment.items() if name != "LC_CTYPE"}
    assert seen == {**GIVEN, **SWITCHES}


def test_the_factory_still_pushes_and_posts_after_an_agent_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
) -> None:
    monkeypatch.setenv("GH_TOKEN", "example-value")
    before = dict(os.environ)
    directory = tmp_path / CHECKOUT
    run_git(directory, "checkout", "-q", "-B", BRANCH, "origin/main")
    write_files(directory, {"new.txt": "new\n"})
    commit_all(directory, "work")
    pull = hosting.create_pull_request(BRANCH, "First story", "Text.", draft=True)

    _runtime(tmp_path).run(_request(tmp_path, scrub_environment(before)))
    pushed = checkout.push(BRANCH)
    posted = hosting.post_comment(
        pull.number, "Done.", PostKey(work_item="F0001-S0001", kind="question", n="1")
    )

    assert (pushed, posted) == ("pushed", "posted")
    assert dict(os.environ) == before
