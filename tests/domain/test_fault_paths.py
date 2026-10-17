"""The fault-injection paths as data: the rows, their cases and the closed model."""

from factory.domain.fault_paths import FAULT_PATHS
from factory.domain.kill_point_cases import KILL_POINT_CASES


def test_the_first_six_paths_are_the_six_rows_in_number_order() -> None:
    rows = [(path.number, path.title, path.case, path.test) for path in FAULT_PATHS[:6]]

    assert rows == [
        (
            1,
            "intake asks: a behaviour without a criterion",
            "agent-run-tick",
            "test_intake_question_tick_killed_during_intake_run_reruns_free_and_asks_once",
        ),
        (
            2,
            "intake asks for an edge case",
            "commit-push",
            "test_intake_edge_case_question_killed_between_commit_and_push_"
            "reruns_intake_and_posts_once",
        ),
        (
            3,
            "the tester finds a criterion against the interface",
            "post-record",
            "test_tester_question_killed_between_post_and_record_posts_once",
        ),
        (
            4,
            "a review rework",
            "agent-run-dies",
            "test_review_rework_after_reviewer_run_dies_charges_one_attempt_then_one_round",
        ),
        (
            5,
            "a documenter finding",
            "tick-other",
            "test_docs_finding_tick_killed_after_move_back_push_"
            "counts_round_once_and_next_stage_starts",
        ),
        (
            6,
            "a smoke test finding",
            "agent-run-dies",
            "test_smoke_test_finding_after_run_reaches_time_limit_"
            "charges_one_attempt_then_moves_back",
        ),
    ]


def test_every_path_arms_the_kill_point_of_a_known_case() -> None:
    ids = {case.id for case in KILL_POINT_CASES}

    assert [path.case for path in FAULT_PATHS if path.case not in ids] == []
