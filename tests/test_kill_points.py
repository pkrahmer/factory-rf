"""The recovery proof: each kill-point case recovers, and repeated failures reach their caps."""

from collections.abc import Callable

import pytest

from factory.domain.hosting import FACTORY_MARKER, PostKey, render_post
from factory.domain.identifiers import branch_name
from factory.domain.kill_point_cases import KILL_POINT_CASES
from factory.domain.kill_points import InjectedKill, KillPoint
from proof_support import (
    KILL_TO_RERUN,
    MARKER,
    SCENARIOS,
    CaseResult,
    World,
    case_by_id,
    completed,
    died,
    head_state,
    posts,
    pull_request_of,
    repeated_posts,
    restart,
    run_case,
    run_ticks,
    start_story,
    violations,
)

QUESTION = "Which format does the title take?"
ALL = [case.id for case in KILL_POINT_CASES]
CRASHES = [case.id for case in KILL_POINT_CASES if case.result_class == "crash"]
CHARGING = [case.id for case in KILL_POINT_CASES if case.charges_crash]
STALLS = [case.id for case in KILL_POINT_CASES if case.result_class == "stall"]


@pytest.fixture(scope="module")
def result(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> CaseResult:
    case_id: str = request.param
    case = case_by_id(case_id)
    return run_case(case, tmp_path_factory.mktemp(case.id))


def _over(ids: list[str]) -> pytest.MarkDecorator:
    pairs = [(case_id, case_id) for case_id in ids]
    return pytest.mark.parametrize(("result", "case_id"), pairs, indirect=["result"], ids=ids)


def _checked(condition: str) -> Callable[[CaseResult, str], list[str]]:
    def check(result: CaseResult, case_id: str) -> list[str]:
        return violations(result, case_by_id(case_id), (condition,))

    return check


def test_every_case_has_a_scenario_and_no_other_id_has_one() -> None:
    assert set(SCENARIOS) == {case.id for case in KILL_POINT_CASES}
    assert len(SCENARIOS) == len(KILL_POINT_CASES)


@_over(CRASHES)
def test_the_armed_kill_point_ends_the_tick_that_reaches_it(
    result: CaseResult, case_id: str
) -> None:
    case = case_by_id(case_id)

    assert result.killed_point == case.kill_point


@_over(CRASHES)
def test_the_restarted_factory_reruns_a_charged_stage_at_its_first_tick(
    result: CaseResult, case_id: str
) -> None:

    assert _checked("resumes-at-first-tick")(result, case_id) == []


@_over(CHARGING)
def test_the_rerun_starts_five_seconds_after_the_kill(
    result: CaseResult, case_id: str, record_property: Callable[[str, object], None]
) -> None:
    assert case_by_id(case_id).charges_crash
    seconds = _rerun_seconds(result)
    record_property("kill_to_rerun_seconds", seconds)

    assert seconds == KILL_TO_RERUN.total_seconds() == 5.0


def _rerun_seconds(result: CaseResult) -> float:
    git = result.world.boundaries.git
    git.fetch()
    branch = f"origin/{branch_name(result.work_item)}"
    reader = result.world.boundaries.work_item_reader
    assert result.killed_at is not None
    for info in git.log(branch):
        for path in git.list_files(info.commit, "factory/features/F0001-example/in-progress"):
            if not path.endswith(".md"):
                continue
            text = git.show_file(info.commit, path)
            state = reader.parse(text).state if text is not None else None
            if state is not None and state.claim is not None:
                return (state.claim.started_at - result.killed_at).total_seconds()
    raise AssertionError("no commit of the branch carries a claim")


@_over(ALL)
def test_the_question_is_posted_once_and_no_post_is_repeated(
    result: CaseResult, case_id: str
) -> None:

    assert _checked("no-repeated-post")(result, case_id) == []


@_over(ALL)
def test_the_interrupted_step_is_journalled_once(result: CaseResult, case_id: str) -> None:

    assert _checked("no-repeated-step")(result, case_id) == []


@_over(ALL)
def test_no_write_of_the_interrupted_run_reaches_the_remote(
    result: CaseResult, case_id: str
) -> None:

    assert _checked("no-interrupted-write-in-history")(result, case_id) == []


@_over(CRASHES)
def test_the_stage_start_of_the_kill_is_kept(result: CaseResult, case_id: str) -> None:

    assert _checked("stage-start-kept")(result, case_id) == []


@_over(CRASHES)
def test_only_the_cost_record_of_the_finished_run_is_kept(result: CaseResult, case_id: str) -> None:

    assert _checked("no-discarded-cost-record")(result, case_id) == []


@_over(CRASHES)
def test_a_crash_charges_a_crash_only_while_a_stage_was_in_flight(
    result: CaseResult, case_id: str
) -> None:
    state = head_state(result.world, result.work_item)

    assert state.attempts == 0
    assert state.crashes == (1 if case_id in CHARGING else 0)
    assert _checked("counters")(result, case_id) == []


def test_the_proof_helpers_find_a_leaked_marker_and_a_repeated_post(world: World) -> None:
    work_item = start_story(world)
    world.agent_runtime.queue(completed("question", QUESTION))
    run_ticks(world)
    result = CaseResult(world, work_item, None, None, None)
    world.human.push_file("proof-leak", "src/leak.py", f"{MARKER} = True\n")
    number = pull_request_of(world, work_item).number
    key = PostKey(work_item=work_item, kind="correction", n="a")
    body = render_post("Repeated.", key)
    assert FACTORY_MARKER in body
    world.hosting.add_human_comment(number, body)
    world.hosting.add_human_comment(number, body)

    found = violations(result, KILL_POINT_CASES[0], ("no-interrupted-write-in-history",))

    assert found == ["no-interrupted-write-in-history"]
    assert key.comment() in repeated_posts(world)


def test_tick_killed_during_agent_run_twice_reaches_crash_cap_and_asks_human(
    world: World,
) -> None:
    work_item = start_story(world)
    world.kill_points.arm(KillPoint.AGENT_RUN)
    world.agent_runtime.queue(completed("question", QUESTION, kill=True))
    with pytest.raises(InjectedKill):
        run_ticks(world)
    world.clock.advance(KILL_TO_RERUN)
    second = restart(world)
    world.kill_points.arm(KillPoint.AGENT_RUN)
    second.agent_runtime.queue(completed("question", QUESTION, kill=True))
    with pytest.raises(InjectedKill):
        run_ticks(second)
    assert len(second.agent_runtime.requests()) == 1
    assert posts(second, work_item, "crash_cap") == []

    world.clock.advance(KILL_TO_RERUN)
    third = restart(second)
    run_ticks(third)

    assert third.agent_runtime.requests() == []
    assert len(posts(third, work_item, "crash_cap")) == 1
    state = head_state(third, work_item)
    assert state.blocked == "crash_cap"
    assert state.crashes == 2
    every_post = len(posts(third, work_item))
    run_ticks(third, 2)
    assert third.agent_runtime.requests() == []
    assert len(posts(third, work_item)) == every_post


@_over(STALLS)
def test_a_died_run_charges_one_attempt_and_keeps_the_stage(
    result: CaseResult, case_id: str
) -> None:

    assert _checked("attempt-charged")(result, case_id) == []


@_over(STALLS)
def test_a_died_run_loses_its_writes_outside_the_write_paths(
    result: CaseResult, case_id: str
) -> None:

    assert _checked("outside-writes-undone")(result, case_id) == []


@_over(STALLS)
def test_a_died_run_loses_its_edits_of_state_and_journal(result: CaseResult, case_id: str) -> None:

    assert _checked("state-restored")(result, case_id) == []


@_over(STALLS)
def test_a_died_run_keeps_its_writes_inside_the_write_paths(
    result: CaseResult, case_id: str
) -> None:

    assert _checked("inside-writes-kept")(result, case_id) == []


@_over(STALLS)
def test_a_died_run_keeps_its_cost_record_with_unknown_usage(
    result: CaseResult, case_id: str
) -> None:

    assert _checked("cost-record-kept")(result, case_id) == []


def test_two_died_runs_reach_the_attempts_cap_and_ask_the_human(world: World) -> None:
    work_item = start_story(world)
    world.agent_runtime.queue(died())
    world.agent_runtime.queue(died())

    run_ticks(world)
    assert head_state(world, work_item).attempts == 1
    assert posts(world, work_item, "attempts_cap") == []
    run_ticks(world)
    assert head_state(world, work_item).attempts == 2
    assert posts(world, work_item, "attempts_cap") == []
    run_ticks(world)

    assert head_state(world, work_item).blocked == "attempts_cap"
    assert len(posts(world, work_item, "attempts_cap")) == 1
    assert len(world.agent_runtime.requests()) == 2
    every_post = len(posts(world, work_item))
    run_ticks(world, 2)
    assert len(world.agent_runtime.requests()) == 2
    assert len(posts(world, work_item)) == every_post
