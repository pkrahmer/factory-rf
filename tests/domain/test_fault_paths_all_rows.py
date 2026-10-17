"""The fault-injection paths as data: all thirteen rows, the last seven after the first six."""

from factory.domain.fault_paths import FAULT_PATHS

FIRST_SIX = [
    (1, "intake asks: a behaviour without a criterion", "agent-run-tick"),
    (2, "intake asks for an edge case", "commit-push"),
    (3, "the tester finds a criterion against the interface", "post-record"),
    (4, "a review rework", "agent-run-dies"),
    (5, "a documenter finding", "tick-other"),
    (6, "a smoke test finding", "agent-run-dies"),
]
LAST_SEVEN = [
    (
        7,
        "the round cap",
        "post-record",
        "test_round_cap_question_killed_between_post_and_record_posts_once_and_waits",
    ),
    (
        8,
        "the attempts cap and its retry",
        "agent-run-dies",
        "test_attempts_cap_run_stalls_twice_asks_human_without_a_rerun_and_reruns_on_comment",
    ),
    (
        9,
        "`reject` after a stage change by hand",
        "commit-push",
        "test_reject_killed_before_push_reverts_once_and_leaves_main_clean",
    ),
    (
        10,
        "two work items in progress",
        "tick-other",
        "test_two_items_in_progress_tick_killed_after_claim_push_reruns_lower_id_and_other_waits",
    ),
    (
        11,
        "a close at the approval",
        "tick-other",
        "test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once",
    ),
    (
        12,
        "a feature acceptance refused, or merged",
        "container",
        "test_acceptance_container_lost_in_review_reruns_once_and_books_result",
    ),
    (
        13,
        "a test change the human approves",
        "agent-run-tick",
        "test_test_change_approved_tick_killed_during_tester_run_reruns_tests_without_round",
    ),
]


def test_the_paths_are_the_six_first_rows_then_the_seven_last_in_number_order() -> None:
    first = [(path.number, path.title, path.case) for path in FAULT_PATHS[:6]]
    last = [(path.number, path.title, path.case, path.test) for path in FAULT_PATHS[6:]]

    assert len(FAULT_PATHS) == 13
    assert first == FIRST_SIX
    assert last == LAST_SEVEN
