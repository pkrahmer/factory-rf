"""The end of a stage records on its question the block the question opened."""

from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.domain.agent_runs import QUESTION
from factory.domain.work_item import WorkItemState
from human_clone import HumanClone
from stage_run_support import (
    CREATED,
    STORY,
    WITHOUT_SMOKE_TEST,
    completed,
    open_story,
    pushed_state,
    run_stage,
)


@pytest.mark.parametrize(
    ("stage", "rounds", "role", "body", "decision", "tail"),
    [
        pytest.param(
            "tests", 0, "tester", STORY, QUESTION, [("tester", "question", "question")], id="rule-2"
        ),
        pytest.param(
            "tests",
            0,
            "tester",
            WITHOUT_SMOKE_TEST,
            "doing",
            [("tester", "result", None), ("factory", "question", "question")],
            id="rule-1",
        ),
        pytest.param(
            "docs",
            3,
            "documenter",
            STORY,
            "doing",
            [("factory", "question", "round_cap")],
            id="rule-4",
        ),
        pytest.param(
            "tests", 0, "tester", STORY, "doing", [("tester", "result", None)], id="rule-6"
        ),
    ],
)
def test_a_stage_end_records_the_block_its_question_opened(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    stage: str,
    rounds: int,
    role: str,
    body: str,
    decision: str,
    tail: list[tuple[str, str, str | None]],
) -> None:
    state = WorkItemState(stage=stage, round=rounds, journal=[CREATED])
    open_story(boundaries, human, agent_home, state=state, body=body, roles=(role,))
    agent_runtime.queue(ScriptedRun(result=completed(decision)))

    run_stage(boundaries)

    journal = pushed_state(boundaries, remote).journal
    recorded = [(record.speaker, record.kind, record.blocked) for record in journal]
    assert recorded[-len(tail) :] == tail
