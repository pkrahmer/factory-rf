"""A story walks a second route to a second approval, in the fake world, beside today's route."""

from pathlib import Path
from typing import Final

import pytest

from factory.hosting.domain.hand_over import HAND_OVER_CLOSING
from factory.hosting.domain.post_texts import send_back_entry_text
from factory.pipeline.domain.pipeline_definition import PipelineDefinition
from factory.shared.domain.identifiers import WorkItemId, branch_name
from factory.work.domain.acceptance import is_before_approval
from factory.work.domain.journal import entry_text
from factory.work.domain.work_item import WorkItemDocument, WorkItemState
from support.git_support import remote_commit
from support.proof_support import (
    FEATURE,
    PASSING_TEST,
    SOURCE,
    World,
    completed,
    head_state,
    posts,
    pull_request_of,
    start_story,
    work_item_file,
)

TWO_ROUTES: Final[str] = """\
contract: "1.0"
attempts_cap: 2
crash_cap: 2
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 8}
  lint: {time_limit: 5}
  test: {time_limit: 10}
  duplicates: {time_limit: 2}
  documents: {time_limit: 2}
  secrets: {time_limit: 3}
  sync: {time_limit: 5}
roles:
  intake: {write_paths: ["{work_item}"], time_limit: 40, lease_duration: 60}
  tester: {write_paths: ["tests/*"], time_limit: 40, lease_duration: 60}
  coder: {write_paths: ["src/*"], time_limit: 40, lease_duration: 60}
  reviewer: {write_paths: ["{work_item}"], time_limit: 40, lease_duration: 60}
  documenter: {write_paths: ["README.md", "docs/*"], time_limit: 40, lease_duration: 60}
  smoke-tester: {write_paths: ["{work_item}"], time_limit: 40, lease_duration: 60}
  acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"], time_limit: 40, lease_duration: 60}
stages:
  intake: {role: intake, next: [tests, docs-only]}
  tests: {role: tester, next: [doing], checks: [lint]}
  doing: {role: coder, next: [review, tests], checks: [check], reports: [duplicates]}
  review: {role: reviewer, next: [docs, doing], round_cap: 2}
  docs: {role: documenter, next: [smoke-test, doing], checks: [check, secrets, documents], round_cap: 2}
  smoke-test: {role: smoke-tester, next: [approval, doing, docs], round_cap: 2}
  docs-only: {role: documenter, next: [docs-review, tests], checks: [check, secrets, documents]}
  docs-review: {role: reviewer, next: [docs-approval, docs-only], round_cap: 2}
  docs-approval: {approval: true, next: [done, docs-only]}
  acceptance: {role: acceptance-reviewer, next: [approval]}
  approval: {approval: true, next: [done, doing]}
  done: {}
"""  # noqa: E501
MAKEFILE: Final[str] = "".join(
    f"{target}:\n\t@:\n"
    for target in ("sync", "check", "lint", "test", "duplicates", "documents", "secrets")
)
WRITES: Final[dict[str, dict[str, str]]] = {
    "tests": {"tests/test_example.py": PASSING_TEST},
    "doing": {"src/example.py": SOURCE},
}
DOCS_ROUTE: Final[tuple[str, ...]] = ("docs-only", "docs-review", "docs-approval")
CODE_ROUTE: Final[tuple[str, ...]] = ("doing", "review", "docs", "smoke-test", "approval")
CLOSE_REASON = "The second paragraph is wrong."


@pytest.fixture
def two_routes(world: World) -> World:
    """The world with the two-route definition and a Makefile of every target on `main`."""
    world.human.push_files("main", {"factory/pipeline.yml": TWO_ROUTES, "Makefile": MAKEFILE})
    return world


@pytest.fixture
def story(two_routes: World) -> WorkItemId:
    """A story started in the two-route world."""
    return start_story(two_routes)


def _step(world: World, work_item: WorkItemId, decision: str, stage: str) -> WorkItemState:
    """One tick in which the agent of `stage` ends with `decision`; the state after it."""
    run = completed(decision, f"{stage}: {decision}.", writes=WRITES.get(stage))
    world.agent_runtime.queue(run)
    world.tick.run()
    return head_state(world, work_item)


def _hand_over(world: World, work_item: WorkItemId) -> WorkItemState:
    world.tick.run()
    return head_state(world, work_item)


def _labels(world: World, work_item: WorkItemId) -> list[str]:
    return world.hosting.labels(pull_request_of(world, work_item).number)


def _walk_docs_route(world: World, work_item: WorkItemId) -> WorkItemState:
    _step(world, work_item, "docs-only", "intake")
    _step(world, work_item, "docs-review", "docs-only")
    _step(world, work_item, "docs-approval", "docs-review")
    return _hand_over(world, work_item)


def _walk_code_route(world: World, work_item: WorkItemId, first: str) -> list[str]:
    """From `first`, every stage's forward decision to `approval`; the stages reached."""
    reached: list[str] = []
    stage = first
    for following in CODE_ROUTE:
        reached.append(_step(world, work_item, following, stage).stage)
        stage = following
    return reached


def _document(world: World, work_item: WorkItemId) -> WorkItemDocument:
    git = world.boundaries.git
    text = git.show_file(f"origin/{branch_name(work_item)}", work_item_file(world, work_item))
    assert text is not None
    return world.boundaries.work_item_reader.parse(text)


def _close_with_reason(world: World, work_item: WorkItemId) -> WorkItemState:
    number = pull_request_of(world, work_item).number
    world.hosting.add_human_comment(number, CLOSE_REASON)
    world.hosting.close_by_human(number)
    world.tick.run()
    return head_state(world, work_item)


def test_an_intake_decision_docs_only_walks_the_docs_route_to_a_hand_over_at_docs_approval(
    two_routes: World, story: WorkItemId
) -> None:
    reached: list[str] = []
    labelled: list[bool] = []
    for stage, decision in (
        ("intake", "docs-only"),
        ("docs-only", "docs-review"),
        ("docs-review", "docs-approval"),
    ):
        state = _step(two_routes, story, decision, stage)
        reached.append(state.stage)
        labelled.append(f"stage:{decision}" in _labels(two_routes, story))
    handed = _hand_over(two_routes, story)
    view = pull_request_of(two_routes, story)

    assert reached == list(DOCS_ROUTE)
    assert labelled == [True, True, True]
    results = [record.stage for record in handed.journal if record.kind == "result"]
    assert results == ["intake", "docs-only", "docs-review"]
    assert handed.stage == "docs-approval"
    assert handed.handed_over == "docs-approval"
    assert not view.draft
    assert two_routes.hosting.description(view.number).endswith(HAND_OVER_CLOSING + "\n")


def test_a_merge_at_docs_approval_archives_the_story_to_done(
    two_routes: World, story: WorkItemId
) -> None:
    _walk_docs_route(two_routes, story)
    two_routes.human.merge(branch_name(story), "merge")
    main = remote_commit(two_routes.remote, "main")
    assert main is not None
    two_routes.hosting.merge_by_human(pull_request_of(two_routes, story).number, main)
    for _ in range(3):
        two_routes.tick.run()

    git = two_routes.boundaries.git
    git.fetch()
    done = [Path(path).name for path in git.list_files("origin/main", f"{FEATURE}/done")]
    in_progress = [
        Path(path).name for path in git.list_files("origin/main", f"{FEATURE}/in-progress")
    ]
    assert any(name.startswith(story) and name.endswith(".md") for name in done)
    assert not any(name.startswith(story) for name in in_progress)


def test_a_close_at_docs_approval_sends_the_story_back_to_docs_only(
    two_routes: World, story: WorkItemId
) -> None:
    _walk_docs_route(two_routes, story)

    sent_back = _close_with_reason(two_routes, story)
    document = _document(two_routes, story)
    [send_back] = [record for record in sent_back.journal if record.kind == "send_back"]

    assert sent_back.stage == "docs-only"
    assert sent_back.round == 1
    assert entry_text(document, send_back.number) == send_back_entry_text("docs-only", 1)


@pytest.mark.parametrize(
    ("send_backs", "stage", "round_number", "blocked"),
    [
        pytest.param(1, "docs-only", 1, None, id="first"),
        pytest.param(2, "docs-only", 2, None, id="second-at-the-cap"),
        pytest.param(3, "docs-review", 3, "round_cap", id="third-past-the-cap"),
    ],
)
def test_a_send_back_at_docs_review_counts_a_round_and_the_third_asks_the_human(
    two_routes: World,
    story: WorkItemId,
    *,
    send_backs: int,
    stage: str,
    round_number: int,
    blocked: str | None,
) -> None:
    _step(two_routes, story, "docs-only", "intake")
    _step(two_routes, story, "docs-review", "docs-only")
    state = head_state(two_routes, story)
    for sent in range(1, send_backs + 1):
        state = _step(two_routes, story, "docs-only", "docs-review")
        if sent < send_backs:
            state = _step(two_routes, story, "docs-review", "docs-only")
    if blocked is not None:
        two_routes.tick.run()

    assert (state.stage, state.round, state.blocked) == (stage, round_number, blocked)
    assert len(posts(two_routes, story, "round_cap")) == (1 if blocked else 0)


def test_a_documenter_decision_tests_takes_the_code_route_whose_close_sends_back_to_doing(
    two_routes: World, story: WorkItemId
) -> None:
    _step(two_routes, story, "docs-only", "intake")
    moved = _step(two_routes, story, "tests", "docs-only")
    reached = _walk_code_route(two_routes, story, "tests")
    handed = _hand_over(two_routes, story)
    sent_back = _close_with_reason(two_routes, story)

    assert (moved.stage, moved.round) == ("tests", 0)
    assert reached == list(CODE_ROUTE)
    assert handed.handed_over == "approval"
    assert sent_back.stage == "doing"
    assert sent_back.journal[-1].kind == "send_back"


def test_an_intake_decision_tests_still_takes_todays_route_to_approval(
    two_routes: World, story: WorkItemId
) -> None:
    moved = _step(two_routes, story, "tests", "intake")
    reached = _walk_code_route(two_routes, story, "tests")
    handed = _hand_over(two_routes, story)

    assert moved.stage == "tests"
    assert reached == list(CODE_ROUTE)
    assert handed.stage == "approval"
    assert handed.handed_over == "approval"
    assert not pull_request_of(two_routes, story).draft


@pytest.mark.parametrize(
    ("stage", "before"),
    [
        ("docs-only", True),
        ("docs-review", True),
        ("docs-approval", False),
        ("acceptance", False),
        ("approval", False),
    ],
)
def test_only_the_docs_routes_working_stages_lie_before_the_approval(
    two_routes: World, stage: str, before: bool
) -> None:
    definition: PipelineDefinition = two_routes.boundaries.pipeline_reader.parse(TWO_ROUTES)

    assert is_before_approval(definition, stage) is before
