"""The state of a work item, its claim and the document that pairs state and body."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.journal import JournalRecord
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState, initial_state

STARTED_AT = datetime(2026, 10, 13, 9, 30, tzinfo=UTC)


def _claim(stage: str = "tests") -> Claim:
    return Claim(instance="laptop", stage=stage, started_at=STARTED_AT, lease_duration=30)


def _records(numbers: list[int]) -> list[JournalRecord]:
    return [JournalRecord(number=number, speaker="factory", kind="result") for number in numbers]


def _claim_fields(stage: str = "tests", lease_duration: int = 30) -> dict[str, object]:
    return {
        "instance": "laptop",
        "stage": stage,
        "started_at": "2026-10-13T09:30:00+00:00",
        "lease_duration": lease_duration,
    }


def test_initial_state_starts_at_the_first_stage_with_nothing_set() -> None:
    state = initial_state("intake")

    assert state.stage == "intake"
    assert state.blocked is None
    assert state.pull_request is None
    assert state.handed_over is None
    assert state.claim is None
    assert state.round == 0
    assert state.attempts == 0
    assert state.crashes == 0
    assert state.comments_read == []
    assert state.journal == []
    assert list(WorkItemState.model_fields) == [
        "stage",
        "blocked",
        "round",
        "attempts",
        "crashes",
        "pull_request",
        "comments_read",
        "handed_over",
        "claim",
        "journal",
    ]


def test_only_stage_is_required_and_must_be_a_name() -> None:
    model: type[BaseModel] = WorkItemState

    assert WorkItemState(stage="tests") == initial_state("tests")
    with pytest.raises(ValidationError):
        model()
    with pytest.raises(ValidationError):
        WorkItemState(stage="Bad Stage")
    with pytest.raises(ValidationError):
        WorkItemState(stage="")
    with pytest.raises(ValidationError):
        initial_state("Bad Stage")


@pytest.mark.parametrize(
    ("blocked", "accepted"),
    [
        (None, True),
        ("question", True),
        ("attempts_cap", True),
        ("round_cap", True),
        ("crash_cap", True),
        ("send_back", True),
        ("asked", False),
        ("", False),
    ],
)
def test_blocked_is_one_of_the_five_reasons_or_none(blocked: str | None, accepted: bool) -> None:
    model: type[BaseModel] = WorkItemState
    if accepted:
        assert model(stage="tests", blocked=blocked).model_dump()["blocked"] == blocked
    else:
        with pytest.raises(ValidationError):
            model(stage="tests", blocked=blocked)


@pytest.mark.parametrize("field", ["round", "attempts", "crashes"])
@pytest.mark.parametrize(("value", "accepted"), [(0, True), (-1, False)])
def test_counters_are_not_negative(field: str, value: int, accepted: bool) -> None:
    model: type[BaseModel] = WorkItemState
    if accepted:
        assert model(stage="tests", **{field: value}).model_dump()[field] == value
    else:
        with pytest.raises(ValidationError):
            model(stage="tests", **{field: value})


@pytest.mark.parametrize(
    ("pull_request", "accepted"), [(1, True), (None, True), (0, False), (-1, False)]
)
def test_pull_request_is_positive_or_none(pull_request: int | None, accepted: bool) -> None:
    if accepted:
        assert WorkItemState(stage="tests", pull_request=pull_request).pull_request == pull_request
    else:
        with pytest.raises(ValidationError):
            WorkItemState(stage="tests", pull_request=pull_request)


@pytest.mark.parametrize(
    ("handed_over", "accepted"),
    [("approval", True), (None, True), ("Approval", False), ("", False)],
)
def test_handed_over_is_a_name_or_none(handed_over: str | None, accepted: bool) -> None:
    if accepted:
        assert WorkItemState(stage="tests", handed_over=handed_over).handed_over == handed_over
    else:
        with pytest.raises(ValidationError):
            WorkItemState(stage="tests", handed_over=handed_over)


@pytest.mark.parametrize(
    ("comments_read", "accepted"),
    [([], True), ([3], True), ([3, 5], True), ([5, 3], False), ([3, 3], False), ([0], False)],
)
def test_comments_read_are_ascending_positive_and_unique(
    comments_read: list[int], accepted: bool
) -> None:
    if accepted:
        assert WorkItemState(stage="tests", comments_read=comments_read).comments_read == (
            comments_read
        )
    else:
        with pytest.raises(ValidationError):
            WorkItemState(stage="tests", comments_read=comments_read)


def test_a_claim_must_be_for_the_state_s_stage() -> None:
    assert WorkItemState(stage="tests", claim=_claim("tests")).claim == _claim("tests")
    with pytest.raises(ValidationError):
        WorkItemState(stage="tests", claim=_claim("doing"))


@pytest.mark.parametrize(
    ("numbers", "accepted"),
    [
        ([], True),
        ([1, 2, 3], True),
        ([2], False),
        ([1, 3], False),
        ([1, 1], False),
        ([2, 1], False),
    ],
)
def test_journal_records_are_numbered_from_one_in_order(numbers: list[int], accepted: bool) -> None:
    if accepted:
        assert WorkItemState(stage="tests", journal=_records(numbers)).journal == _records(numbers)
    else:
        with pytest.raises(ValidationError):
            WorkItemState(stage="tests", journal=_records(numbers))


@pytest.mark.parametrize(
    ("fields", "location"),
    [
        ({"comments_read": [5, 3]}, ("comments_read",)),
        (
            {
                "journal": [
                    {"number": 1, "speaker": "factory", "kind": "result"},
                    {"number": 3, "speaker": "factory", "kind": "result"},
                ]
            },
            ("journal",),
        ),
        ({"claim": _claim_fields(stage="doing")}, ()),
        ({"claim": _claim_fields(lease_duration=0)}, ("claim", "lease_duration")),
    ],
)
def test_an_error_is_located_at_the_field_its_rule_validates(
    fields: dict[str, object], location: tuple[str, ...]
) -> None:
    with pytest.raises(ValidationError) as caught:
        WorkItemState.model_validate({"stage": "tests", **fields})

    assert caught.value.errors()[0]["loc"] == location


@pytest.mark.parametrize(("lease_duration", "accepted"), [(1, True), (0, False)])
def test_a_claim_s_lease_lasts_at_least_one_minute(lease_duration: int, accepted: bool) -> None:
    if accepted:
        claim = Claim(
            instance="laptop", stage="tests", started_at=STARTED_AT, lease_duration=lease_duration
        )
        assert claim.lease_duration == lease_duration
    else:
        with pytest.raises(ValidationError):
            Claim(
                instance="laptop",
                stage="tests",
                started_at=STARTED_AT,
                lease_duration=lease_duration,
            )


def test_a_claim_refuses_a_naive_start() -> None:
    with pytest.raises(ValidationError):
        Claim(
            instance="laptop",
            stage="tests",
            started_at=datetime(2026, 10, 13, 9, 30),  # noqa: DTZ001
            lease_duration=30,
        )


def test_a_claim_stores_its_start_in_utc() -> None:
    east = datetime(2026, 10, 13, 11, 30, tzinfo=timezone(timedelta(hours=2)))

    claim = Claim(instance="laptop", stage="tests", started_at=east, lease_duration=30)

    assert claim.started_at == STARTED_AT
    assert claim.started_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    ("instance", "stage"), [("Laptop", "tests"), ("", "tests"), ("laptop", "Bad Stage")]
)
def test_a_claim_s_instance_and_stage_are_names(instance: str, stage: str) -> None:
    with pytest.raises(ValidationError):
        Claim(instance=instance, stage=stage, started_at=STARTED_AT, lease_duration=30)


@pytest.mark.parametrize(
    ("model", "fields", "field"),
    [
        (WorkItemState, {"stage": "tests"}, "stage"),
        (
            Claim,
            {
                "instance": "laptop",
                "stage": "tests",
                "started_at": STARTED_AT,
                "lease_duration": 30,
            },
            "lease_duration",
        ),
        (JournalRecord, {"number": 1, "speaker": "human", "kind": "created"}, "kind"),
        (WorkItemDocument, {"state": None, "body": "x"}, "body"),
    ],
)
def test_work_item_models_are_frozen_and_refuse_an_unknown_field(
    model: type[BaseModel], fields: dict[str, object], field: str
) -> None:
    instance = model(**fields)

    with pytest.raises(ValidationError):
        model(**fields, unknown="x")
    with pytest.raises(ValidationError):
        setattr(instance, field, instance.model_dump()[field])


def test_a_document_needs_a_state_even_if_it_is_none() -> None:
    model: type[BaseModel] = WorkItemDocument
    document = WorkItemDocument(state=None, body="x")

    assert document.state is None
    assert document.ignored_keys == []
    with pytest.raises(ValidationError):
        model(body="x")
