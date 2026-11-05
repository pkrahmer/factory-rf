"""The mutation report command and its rules are gone; the shared input reader stays."""

import pytest

from support.module_names import module_exists_anywhere


@pytest.mark.parametrize(
    ("name", "found"),
    [
        pytest.param("factory.entry.check_mutants", False, id="report-command"),
        pytest.param("factory.domain.mutants", False, id="report-rules"),
        pytest.param("factory.entry.inputs", True, id="input-reader"),
        pytest.param("factory.entry.check_duplicates", True, id="duplicates-command"),
    ],
)
def test_the_mutation_report_is_removed_and_the_input_reader_stays(name: str, found: bool) -> None:
    assert module_exists_anywhere(name) is found
