"""After the agent at its edges: an empty entry, and form findings counted on both sides."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.agent_runs import AgentRunResult
from factory.domain.work_item import WorkItemDocument, WorkItemState
from human_clone import HumanClone
from stage_run_support import CREATED, CREATED_LINE, PATH, STORY, open_story, run_stage

BLOCK = "```bash\ntrue\n```\n"
WITHOUT_EXPECT = STORY.replace("```\nExpect: nothing.\n", "```\n")
TWICE = WITHOUT_EXPECT.replace(BLOCK, BLOCK + "\n```bash\nfalse\n```\n")
THRICE = WITHOUT_EXPECT.replace(BLOCK, BLOCK + "\n```bash\nfalse\n```\n\n```bash\nfalse\n```\n")


@pytest.mark.parametrize("entry", ["", "tester:"], ids=["empty", "role-name-only"])
def test_an_empty_entry_stalls_as_no_result(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    entry: str,
) -> None:
    open_story(boundaries, human, agent_home)
    agent_runtime.queue(
        ScriptedRun(
            result=AgentRunResult(
                end_reason="completed",
                decision="doing",
                entry=entry,
                duration=timedelta(minutes=1),
            )
        )
    )

    report = run_stage(boundaries)

    assert report.stall is not None
    assert report.stall.reason == "no_result"
    [post] = hosting.factory_posts(report.pull_request)
    assert post.body.splitlines()[0] == (
        "Stalled (attempt 1 of 2): the agent gave no valid decision and entry:"
        " the entry is empty. Retrying on the next tick."
    )


@pytest.mark.parametrize(
    ("after", "stalled"),
    [(TWICE, False), (THRICE, True)],
    ids=["as-many-as-before", "one-more-than-before"],
)
def test_only_findings_beyond_the_count_before_the_run_are_new(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    after: str,
    stalled: bool,
) -> None:
    state = WorkItemState(stage="review", journal=[CREATED])
    open_story(boundaries, human, agent_home, state=state, body=TWICE, roles=("reviewer",))
    written = WorkItemDocument(state=state, body=after + CREATED_LINE)
    agent_runtime.queue(
        ScriptedRun(
            writes={PATH: boundaries.work_item_writer.render(written)},
            result=AgentRunResult(
                end_reason="completed",
                decision="docs",
                entry="reviewed.",
                duration=timedelta(minutes=1),
            ),
        )
    )

    report = run_stage(boundaries)

    if not stalled:
        assert report.stall is None
        assert report.rule == 1
        return
    assert report.stall is not None
    assert report.stall.reason == "form_invalid"
    last = hosting.factory_posts(report.pull_request)[-1]
    assert last.body.splitlines()[0] == (
        "Stalled (attempt 1 of 2): the work item's form broke during the stage: the code block"
        ' opened at line 27 is not followed by an "Expect:" line. Retrying on the next tick.'
    )
