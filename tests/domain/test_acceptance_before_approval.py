"""An acceptance merged before its approval: the stages before it and the entry that says so."""

import pytest

from bill_support import completed_records
from factory.domain.acceptance import AcceptanceState, book_merge, is_before_approval
from factory.domain.bills import bill, cost_line
from factory.domain.journal import FACTORY, JournalRecord, entry_text
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument

BEFORE_APPROVAL = "done (pull request merged before approval); cost: "
JOURNAL = [JournalRecord(number=1, speaker=FACTORY, kind="started")]
BODY = "# Acceptance of Todo service\n\n## Journal\n\n1. factory: started.\n"


# The stages of the test remote's pipeline definition (`PIPELINE_YAML`), in its order.
FIXTURE = PipelineDefinition.model_validate(
    {
        "contract": "1.0",
        "acceptance_stage": "acceptance",
        "roles": {
            "intake": {"write_paths": ["{work_item}"]},
            "tester": {"write_paths": ["tests/*"]},
            "coder": {"write_paths": ["src/*"]},
            "reviewer": {"write_paths": ["{work_item}"]},
            "documenter": {"write_paths": ["README.md", "docs/*"]},
            "smoke-tester": {"write_paths": ["{work_item}"]},
            "acceptance-reviewer": {"write_paths": ["{work_item}", "{feature}/backlog/*"]},
        },
        "stages": {
            "intake": {"role": "intake", "next": ["tests"]},
            "tests": {"role": "tester", "next": ["doing"], "checks": ["lint"], "reports": ["test"]},
            "doing": {"role": "coder", "next": ["review", "tests"], "checks": ["check"]},
            "review": {"role": "reviewer", "next": ["docs", "doing"], "round_cap": 3},
            "docs": {"role": "documenter", "next": ["smoke-test", "doing"], "checks": ["check"]},
            "smoke-test": {"role": "smoke-tester", "next": ["approval", "doing"]},
            "acceptance": {"role": "acceptance-reviewer", "next": ["approval"]},
            "approval": {"approval": True, "next": ["done", "doing"]},
            "done": {},
        },
    }
)


def _without_approval() -> PipelineDefinition:
    return PipelineDefinition.model_validate(
        {
            "contract": "1.0",
            "acceptance_stage": "acceptance",
            "roles": {"acceptance-reviewer": {"write_paths": ["{work_item}"]}},
            "stages": {
                "acceptance": {"role": "acceptance-reviewer", "next": ["done"]},
                "done": {},
            },
        }
    )


@pytest.mark.parametrize(
    ("stage", "expected"),
    [("acceptance", True), ("approval", False), ("done", False)],
)
def test_only_a_stage_before_the_first_approval_is_before_approval(
    stage: str, *, expected: bool
) -> None:
    assert is_before_approval(FIXTURE, stage) is expected


@pytest.mark.parametrize(
    ("without_approval", "stage", "error"),
    [(False, "nowhere", KeyError), (True, "acceptance", ValueError)],
    ids=["unknown-stage", "no-approval-stage"],
)
def test_an_unknown_stage_or_a_definition_without_approval_is_refused(
    stage: str, error: type[Exception], *, without_approval: bool
) -> None:
    used = _without_approval() if without_approval else FIXTURE

    with pytest.raises(error):
        is_before_approval(used, stage)


def test_a_merge_before_approval_books_like_a_merge_with_an_entry_that_says_so() -> None:
    state = AcceptanceState(
        stage="acceptance", stories=["F0002-S0001"], blocked="question", journal=JOURNAL
    )
    document = WorkItemDocument(state=state, body=BODY)
    records = bill(completed_records("F0002-A0001", 2))

    booked = book_merge(document, records, before_approval=True)

    plain = book_merge(document, records)
    assert booked.state == plain.state
    assert booked.state is not None
    assert booked.state.journal == [
        *JOURNAL,
        JournalRecord(number=2, speaker=FACTORY, kind="done"),
    ]
    assert entry_text(booked, 2) == BEFORE_APPROVAL + cost_line(records)
