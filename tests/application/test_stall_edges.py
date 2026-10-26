"""The stalls at their edges: no detail, a red check's files."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.journal import entry_text
from human_clone import HumanClone
from stage_run_support import (
    BRANCH,
    NOTES,
    PATH,
    open_story,
    run_stage,
)

Setup = Callable[[Boundaries, HumanClone, Path, FakeAgentRuntime], Boundaries]


def _merge_conflict(
    boundaries: Boundaries, human: HumanClone, agent_home: Path, _: FakeAgentRuntime
) -> Boundaries:
    open_story(boundaries, human, agent_home, main_files={NOTES: "base\n"})
    human.push_file(BRANCH, NOTES, "branch\n")
    human.push_file("main", NOTES, "main\n")
    boundaries.git.fetch()
    return boundaries


@pytest.mark.parametrize(
    ("setup", "note", "entry"),
    [
        pytest.param(
            _merge_conflict,
            "Stalled (attempt 1 of 2): merging the main branch conflicts and the merge was"
            " aborted. Retrying on the next tick.",
            "Stage tests stalled (attempt 1 of 2): merging the main branch conflicts and the"
            " merge was aborted",
            id="merge-conflict",
        ),
    ],
)
def test_a_stall_without_a_detail_says_only_its_reason(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    setup: Setup,
    note: str,
    entry: str,
) -> None:
    report = run_stage(setup(boundaries, human, agent_home, agent_runtime))

    [post] = hosting.factory_posts(report.pull_request)
    assert post.body.splitlines()[0] == note
    text = boundaries.git.show_file(report.commit, PATH)
    assert text is not None
    document = boundaries.work_item_reader.parse(text)
    assert document.state is not None
    assert entry_text(document, document.state.journal[-1].number) == entry
