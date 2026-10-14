"""The rules of a send-back: whether a reason was given, where the story goes and its round cap."""

import pytest

from factory.domain.journal import JournalKind, JournalRecord
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.send_back import reason_given, send_back_cap, send_back_target
from factory.domain.work_item import WorkItemDocument, WorkItemState

ROLES = {
    "coder": {"write_paths": ["src/*"]},
    "smoke-tester": {"write_paths": ["x"]},
    "acceptance-reviewer": {"write_paths": ["y"]},
}
DOING: dict[str, object] = {"role": "coder", "next": ["smoke-test"]}
SMOKE_TEST: dict[str, object] = {
    "role": "smoke-tester",
    "next": ["approval", "doing"],
    "round_cap": 3,
}
ACCEPTANCE: dict[str, object] = {"role": "acceptance-reviewer", "next": ["approval"]}
APPROVAL: dict[str, object] = {"approval": True, "next": ["done", "doing"]}


def _definition(stages: dict[str, dict[str, object]]) -> PipelineDefinition:
    return PipelineDefinition.model_validate({"contract": "1.0", "roles": ROLES, "stages": stages})


def _fixture_definition() -> PipelineDefinition:
    return _definition({"doing": DOING, "smoke-test": SMOKE_TEST, "approval": APPROVAL, "done": {}})


def _document(*pairs: tuple[str, JournalKind]) -> WorkItemDocument:
    records = [
        JournalRecord(number=number, speaker=speaker, kind=kind)
        for number, (speaker, kind) in enumerate(pairs, 1)
    ]
    # No journal text: the records alone decide.
    return WorkItemDocument(state=WorkItemState(stage="approval", journal=records), body="# T\n")


@pytest.mark.parametrize(
    "document",
    [
        _document(
            ("human", "created"),
            ("smoke-tester", "result"),
            ("human", "comment"),
            ("human", "close"),
        ),
        _document(("human", "created"), ("human", "comment")),
    ],
    ids=["comment-after-the-latest-result", "comment-and-no-result"],
)
def test_a_comment_after_the_latest_result_or_without_any_result_is_a_reason(
    document: WorkItemDocument,
) -> None:
    assert reason_given(document)


@pytest.mark.parametrize(
    "document",
    [
        _document(
            ("human", "created"),
            ("smoke-tester", "result"),
            ("human", "comment"),
            ("smoke-tester", "result"),
            ("human", "close"),
        ),
        _document(("human", "created"), ("smoke-tester", "result"), ("human", "close")),
    ],
    ids=["every-comment-before-the-latest-result", "no-comment"],
)
def test_no_comment_after_the_latest_result_is_no_reason(document: WorkItemDocument) -> None:
    assert not reason_given(document)


def test_the_send_back_target_is_the_second_next_of_the_approval_or_none_without_one() -> None:
    single = _definition(
        {
            "doing": DOING,
            "smoke-test": SMOKE_TEST,
            "approval": {"approval": True, "next": ["done"]},
            "done": {},
        }
    )

    assert send_back_target(_fixture_definition(), "approval") == "doing"
    assert send_back_target(single, "approval") is None


@pytest.mark.parametrize(
    ("stages", "expected"),
    [
        ({"doing": DOING, "smoke-test": SMOKE_TEST, "approval": APPROVAL, "done": {}}, 3),
        (
            {
                "doing": DOING,
                "acceptance": ACCEPTANCE,
                "smoke-test": SMOKE_TEST,
                "approval": APPROVAL,
                "done": {},
            },
            3,
        ),
        (
            {
                "doing": {"role": "coder", "next": ["smoke-test"], "round_cap": 5},
                "smoke-test": {"role": "smoke-tester", "next": ["approval", "doing"]},
                "approval": APPROVAL,
                "done": {},
            },
            None,
        ),
    ],
    ids=["fixture", "uncapped-stage-first", "no-capped-stage-hands-over"],
)
def test_the_send_back_cap_is_the_round_cap_of_the_first_capped_stage_handing_over(
    stages: dict[str, dict[str, object]], expected: int | None
) -> None:
    assert send_back_cap(_definition(stages), "approval") == expected
