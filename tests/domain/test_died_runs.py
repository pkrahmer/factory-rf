"""The factory log's line for a run that died names the run and quotes its text."""

from factory.domain.died_runs import died_line


def test_the_died_line_names_the_run_its_work_item_and_stage_and_quotes_the_text() -> None:
    line = died_line("a" * 32, "F0001-S0001", "docs", "You've hit your limit · resets 12am")

    assert line == (
        f"run {'a' * 32} of F0001-S0001 (docs) died: You've hit your limit · resets 12am"
    )
