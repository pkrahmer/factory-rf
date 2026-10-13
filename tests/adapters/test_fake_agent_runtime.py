"""The fake agent runtime: scripted runs applied to the working directory."""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.agent_runtime import AgentRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, AgentRunResult
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints


def _request(working_directory: Path, prompt: str = "Stage: tests") -> AgentRunRequest:
    agent = AgentDefinition(
        name="tester", model="sonnet", tools=["Read"], budget_usd=Decimal("2"), instructions="."
    )
    return AgentRunRequest(
        agent=agent,
        prompt=prompt,
        allowed_decisions=["doing", "question"],
        time_limit=timedelta(minutes=40),
        working_directory=working_directory,
    )


def _result(entry: str = "Done.") -> AgentRunResult:
    return AgentRunResult(
        end_reason="completed", decision="doing", entry=entry, duration=timedelta(seconds=5)
    )


def test_runs_return_queued_results_in_order_and_record_requests(
    agent_runtime: FakeAgentRuntime, tmp_path: Path
) -> None:
    first, second = _result("first"), _result("second")
    agent_runtime.queue(ScriptedRun(result=first))
    agent_runtime.queue(ScriptedRun(result=second))
    request_one, request_two = _request(tmp_path, "one"), _request(tmp_path, "two")

    assert agent_runtime.run(request_one) == first
    assert agent_runtime.run(request_two) == second
    assert agent_runtime.requests() == [request_one, request_two]


def test_writes_create_and_replace_files_and_deletes_remove_them(
    agent_runtime: FakeAgentRuntime, tmp_path: Path
) -> None:
    (tmp_path / "old.txt").write_text("old\n", encoding="utf-8")
    written = tmp_path / "tests" / "test_a.py"
    agent_runtime.queue(
        ScriptedRun(writes={"tests/test_a.py": "x = 1\n"}, deletes=["old.txt"], result=_result())
    )
    agent_runtime.queue(
        ScriptedRun(writes={"tests/test_a.py": "x = 2\n"}, deletes=["old.txt"], result=_result())
    )

    agent_runtime.run(_request(tmp_path))
    assert written.read_text(encoding="utf-8") == "x = 1\n"
    assert not (tmp_path / "old.txt").exists()

    agent_runtime.run(_request(tmp_path))
    assert written.read_text(encoding="utf-8") == "x = 2\n"


@pytest.mark.parametrize(
    ("bad_write", "bad_delete"),
    [
        ("../escape.txt", None),
        ("{outside}/escape.txt", None),
        (None, "../x"),
        (None, "{outside}/x"),
    ],
)
def test_paths_outside_the_working_directory_raise_before_any_change(
    agent_runtime: FakeAgentRuntime, tmp_path: Path, bad_write: str | None, bad_delete: str | None
) -> None:
    working = tmp_path / "work"
    working.mkdir()
    (working / "keep.txt").write_text("keep\n", encoding="utf-8")
    (tmp_path / "x").write_text("outside\n", encoding="utf-8")
    writes = {"good.txt": "good\n"}
    deletes = ["keep.txt"]
    if bad_write is not None:
        writes[bad_write.format(outside=tmp_path)] = "bad\n"
    if bad_delete is not None:
        deletes.append(bad_delete.format(outside=tmp_path))
    agent_runtime.queue(ScriptedRun(writes=writes, deletes=deletes, result=_result()))

    with pytest.raises(AgentRuntimeError):
        agent_runtime.run(_request(working))

    assert not (working / "good.txt").exists()
    assert (working / "keep.txt").read_text(encoding="utf-8") == "keep\n"
    assert not (tmp_path / "escape.txt").exists()
    assert (tmp_path / "x").read_text(encoding="utf-8") == "outside\n"


def test_run_with_nothing_queued_raises_and_records_the_request(
    agent_runtime: FakeAgentRuntime, tmp_path: Path
) -> None:
    request = _request(tmp_path)

    with pytest.raises(AgentRuntimeError):
        agent_runtime.run(request)
    assert agent_runtime.requests() == [request]


def test_armed_agent_run_kills_after_the_writes(
    agent_runtime: FakeAgentRuntime, kill_points: KillPoints, tmp_path: Path
) -> None:
    kill_points.arm(KillPoint.AGENT_RUN)
    agent_runtime.queue(ScriptedRun(writes={"a.txt": "a\n"}, result=_result(), kill=True))

    with pytest.raises(InjectedKill):
        agent_runtime.run(_request(tmp_path))
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "a\n"


def test_agent_run_point_is_reached_only_when_the_run_asks_for_it(tmp_path: Path) -> None:
    unarmed = KillPoints()
    killing = FakeAgentRuntime(unarmed)
    killing.queue(ScriptedRun(result=_result(), kill=True))
    assert killing.run(_request(tmp_path)) == _result()
    assert unarmed.reached(KillPoint.AGENT_RUN) == 1

    armed = KillPoints()
    armed.arm(KillPoint.AGENT_RUN)
    sparing = FakeAgentRuntime(armed)
    sparing.queue(ScriptedRun(result=_result(), kill=False))
    assert sparing.run(_request(tmp_path)) == _result()
    assert armed.reached(KillPoint.AGENT_RUN) == 0


def test_runtime_without_kill_points_ignores_kill(tmp_path: Path) -> None:
    runtime = FakeAgentRuntime()
    runtime.queue(ScriptedRun(writes={"a.txt": "a\n"}, result=_result(), kill=True))

    assert runtime.run(_request(tmp_path)) == _result()
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "a\n"


def test_version_is_the_one_given_at_construction() -> None:
    assert FakeAgentRuntime().version() == "fake"
    assert FakeAgentRuntime(version="2.1.289").version() == "2.1.289"


def test_fake_fits_the_agent_runtime_protocol_without_inheriting() -> None:
    runtime: AgentRuntime = FakeAgentRuntime()

    assert AgentRuntime not in type(runtime).__mro__
    assert runtime.version() == "fake"


def test_scripted_run_forbids_unknown_keys_and_is_frozen() -> None:
    run = ScriptedRun(result=_result())

    assert ScriptedRun(**dict(run)) == run
    with pytest.raises(ValidationError):
        ScriptedRun(**dict(run), unknown=1)
    with pytest.raises(ValidationError):
        setattr(run, "kill", True)  # noqa: B010
