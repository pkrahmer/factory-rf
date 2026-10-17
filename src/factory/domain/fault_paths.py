"""The fault-injection paths as data: each path, the case it arms and the test that walks it."""

from pydantic import BaseModel, ConfigDict


class FaultPath(BaseModel):
    """One behaviour path walked with one kill or stall, and the test function that walks it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    number: int
    title: str
    case: str
    test: str


# The case names the kill point the path's test arms; the path's own crash charge may
# differ from the case's.
FAULT_PATHS: tuple[FaultPath, ...] = (
    FaultPath(
        number=1,
        title="intake asks: a behaviour without a criterion",
        case="agent-run-tick",
        test="test_intake_question_tick_killed_during_intake_run_reruns_free_and_asks_once",
    ),
    FaultPath(
        number=2,
        title="intake asks for an edge case",
        case="commit-push",
        test="test_intake_edge_case_question_killed_between_commit_and_push_"
        "reruns_intake_and_posts_once",
    ),
    FaultPath(
        number=3,
        title="the tester finds a criterion against the interface",
        case="post-record",
        test="test_tester_question_killed_between_post_and_record_posts_once",
    ),
    FaultPath(
        number=4,
        title="a review rework",
        case="agent-run-dies",
        test="test_review_rework_after_reviewer_run_dies_charges_one_attempt_then_one_round",
    ),
    FaultPath(
        number=5,
        title="a documenter finding",
        case="tick-other",
        test="test_docs_finding_tick_killed_after_move_back_push_"
        "counts_round_once_and_next_stage_starts",
    ),
    FaultPath(
        number=6,
        title="a smoke test finding",
        case="agent-run-dies",
        test="test_smoke_test_finding_after_run_reaches_time_limit_"
        "charges_one_attempt_then_moves_back",
    ),
)
