"""Each row of the stop table proved: the stop reaches its destination and nowhere twice."""

import ast
from pathlib import Path
from typing import get_args

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.hosting import PostKey, PullRequestComment
from factory.domain.identifiers import WorkItemId, branch_name
from factory.domain.journal import NewEntry, append_entry
from factory.domain.stop_table import STOP_TABLE, StopRow
from factory.domain.stops import RepositoryStop, RepositoryStopReason
from factory.domain.work_item import WorkItemDocument, initial_state
from proof_support import (
    FEATURE,
    FIRST_BACKLOG_STORY,
    QUESTION,
    STORY,
    World,
    completed,
    drive_to,
    head_state,
    posts,
    run_ticks,
    start_story,
)
from source_search import modules, string_literals

STAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
FIRST_IN_PROGRESS = FIRST_BACKLOG_STORY.replace("/backlog/", "/in-progress/")
HEALTH_ROWS = [row for row in STOP_TABLE if row.destination == "health_status"]
REJECTING_HOOK = '#!/bin/sh\ncase "$1" in\n  refs/heads/work-item/*) exit 1 ;;\nesac\nexit 0\n'


def _error_posts(world: World) -> list[PullRequestComment]:
    return [
        post
        for view in world.hosting.pull_requests()
        for post in world.hosting.factory_posts(view.number)
        if post.key is not None and post.key.kind == "error"
    ]


def _all_posts(world: World) -> list[PullRequestComment]:
    return [
        post
        for view in world.hosting.pull_requests()
        for post in world.hosting.factory_posts(view.number)
    ]


def _branch_key(world: World, work_item: WorkItemId) -> PostKey:
    git = world.boundaries.git
    git.fetch()
    commit = git.resolve(f"origin/{branch_name(work_item)}")
    assert commit is not None
    return PostKey(work_item=work_item, kind="error", n=commit[:12])


def _question_tick(world: World) -> WorkItemId:
    work_item = start_story(world)
    world.agent_runtime.queue(completed("question", QUESTION))
    run_ticks(world)
    return work_item


def test_every_test_of_the_table_is_a_function_of_this_module() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}

    assert {row.test for row in STOP_TABLE} <= functions


@pytest.mark.parametrize("row", HEALTH_ROWS, ids=[row.id for row in HEALTH_ROWS])
def test_repository_stop_reaches_the_health_status_and_the_factory_log(
    tmp_path: Path,
    boundaries: Boundaries,
    *,
    clock: ManualClock,
    hosting: FakeHostingService,
    row: StopRow,
) -> None:
    assert row.reason is not None
    scope = "machine" if row.reason in ("preflight_failed", "disk_low") else "repository"
    stop = RepositoryStop(scope=scope, reason=row.reason, detail="the fault", at=clock.now())

    StopService(boundaries).raise_stop(stop)

    status = boundaries.health.read()
    lines = (tmp_path / "state" / "factory.log").read_text(encoding="utf-8").splitlines()
    assert status.stops == [stop]
    assert not status.healthy
    assert len(lines) == 1
    assert lines[0].startswith(clock.now().strftime(STAMP_FORMAT))
    assert row.reason in lines[0]
    assert "the fault" in lines[0]
    assert hosting.pull_requests() == []


@pytest.mark.parametrize("reason", get_args(RepositoryStopReason))
def test_production_code_names_every_reason_of_a_repository_stop(reason: str) -> None:
    constants = {
        literal
        for name, tree in modules().items()
        if name.startswith(("factory.application", "factory.entry"))
        for literal in string_literals(tree)
    }

    assert reason in constants


def test_duplicate_is_a_counted_error_reported_once_on_the_pull_request(world: World) -> None:
    work_item = _question_tick(world)
    world.human.push_file(
        "main", f"{FEATURE}/in-progress/{work_item}-other.md", STORY.format(title="Other")
    )

    run_ticks(world, 2)
    after_second = _error_posts(world)
    run_ticks(world)
    after_third = posts(world, work_item, "error")
    key = _branch_key(world, work_item)
    run_ticks(world, 3)

    assert after_second == []
    assert [post.key for post in after_third] == [key]
    assert _error_posts(world) == after_third


def test_failed_pull_request_lookup_is_a_counted_error_reported_once(world: World) -> None:
    work_item = _question_tick(world)
    world.hosting.fail_next("get_pull_request", times=99)
    world.hosting.fail_next("find_open_pull_request", times=99)

    run_ticks(world, 2)
    after_second = _error_posts(world)
    run_ticks(world)
    after_third = posts(world, work_item, "error")
    key = _branch_key(world, work_item)
    run_ticks(world, 3)

    assert after_second == []
    assert [post.key for post in after_third] == [key]
    assert _error_posts(world) == after_third


def _push_recorded_question_without_pull_request(world: World, work_item: WorkItemId) -> None:
    state = initial_state("intake").model_copy(update={"blocked": "question"})
    document = WorkItemDocument(state=state, body=STORY.format(title="Example"))
    asked = append_entry(document, NewEntry(speaker="intake", kind="question", text=QUESTION))
    text = world.boundaries.work_item_writer.render(asked)
    world.human.push_file(branch_name(work_item), FIRST_IN_PROGRESS, text)


def test_ask_without_pull_request_is_reported_once_on_a_draft_pull_request_opened_first(
    world: World, work_item: WorkItemId
) -> None:
    _push_recorded_question_without_pull_request(world, work_item)

    run_ticks(world, 2)
    pull_requests_after_second = world.hosting.pull_requests()
    run_ticks(world)
    pull_requests_after_third = world.hosting.pull_requests()
    after_third = _all_posts(world)
    run_ticks(world, 3)

    assert pull_requests_after_second == []
    assert [(view.branch, view.draft) for view in pull_requests_after_third] == [
        (branch_name(work_item), True)
    ]
    assert len(posts(world, work_item, "error")) == 1
    assert [post.key.kind for post in after_third if post.key is not None] == ["error"]
    assert len(world.hosting.pull_requests()) == 1
    assert _all_posts(world) == after_third


def test_handler_that_fails_every_time_is_reported_once_after_the_error_cap(
    world: World,
) -> None:
    work_item = _question_tick(world)
    world.hosting.fail_next("post_comment", times=3)

    run_ticks(world, 2)
    after_second = _error_posts(world)
    run_ticks(world)
    after_third = posts(world, work_item, "error")
    questions = posts(world, work_item, "question")
    every_post = _all_posts(world)
    run_ticks(world, 3)

    assert after_second == []
    assert len(after_third) == 1
    assert questions == []
    assert _all_posts(world) == every_post


def test_hand_over_that_fails_every_time_is_reported_once_after_the_error_cap(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "smoke-test")
    world.hosting.fail_next("set_description", times=3)
    world.agent_runtime.queue(completed("approval", "Accepted."))
    run_ticks(world)

    run_ticks(world, 2)
    after_second = _error_posts(world)
    run_ticks(world)
    after_third = posts(world, work_item, "error")
    every_post = _all_posts(world)
    run_ticks(world, 3)

    assert after_second == []
    assert len(after_third) == 1
    assert _all_posts(world) == every_post


def test_rejected_push_is_a_counted_error_reported_once(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "tests")
    hook = world.remote / "hooks" / "update"
    hook.parent.mkdir(exist_ok=True)
    hook.write_text(REJECTING_HOOK, encoding="utf-8")
    hook.chmod(0o755)
    world.agent_runtime.queue(completed("doing", "Done."))
    requests_before = len(world.agent_runtime.requests())

    run_ticks(world, 2)
    after_second = _error_posts(world)
    run_ticks(world)
    after_third = posts(world, work_item, "error")
    every_post = _all_posts(world)
    run_ticks(world, 3)

    assert len(world.agent_runtime.requests()) == requests_before
    assert after_second == []
    assert len(after_third) == 1
    assert _all_posts(world) == every_post


def test_story_file_naming_a_later_stage_starts_at_intake_with_no_stop(world: World) -> None:
    front_matter = "---\nstage: doing\nround: 2\nattempts: 1\n---\n"
    world.human.push_file("main", FIRST_BACKLOG_STORY, front_matter + STORY.format(title="Example"))
    world.human.start(FIRST_BACKLOG_STORY)
    work_item: WorkItemId = Path(FIRST_BACKLOG_STORY).name[: len("F0001-S0001")]
    world.agent_runtime.queue(completed("question", QUESTION))

    run_ticks(world)

    state = head_state(world, work_item)
    assert (state.stage, state.round, state.attempts, state.crashes) == ("intake", 0, 0, 0)
    assert world.boundaries.health.read().healthy
    assert _error_posts(world) == []
