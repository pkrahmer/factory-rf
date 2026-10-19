"""The report of a mutation run: mutmut's result lines, the report, the names to run again."""

import re
from collections.abc import Sequence

import pytest

from factory.domain.mutants import (
    MutantResult,
    MutantStatus,
    mutation_report,
    parse_results,
    rerun_names,
)

STATUSES: tuple[MutantStatus, ...] = (
    "killed",
    "survived",
    "timeout",
    "suspicious",
    "no tests",
    "skipped",
    "segfault",
    "caught by type check",
    "check was interrupted by user",
    "not checked",
)
A = "factory.domain.a"
B = "factory.domain.b"
C = "factory.domain.c"
D = "factory.domain.d"


def _results(module: str, *statuses: MutantStatus) -> list[MutantResult]:
    return [
        MutantResult(name=f"{module}.x_f__mutmut_{number}", status=status)
        for number, status in enumerate(statuses, start=1)
    ]


def _names(results: Sequence[MutantResult], *numbers: int) -> list[str]:
    return [results[number].name for number in numbers]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(
            "    factory.domain.a.x_f__mutmut_1: killed\n\n"
            "    factory.domain.a.xǁCǁm__mutmut_2: not checked\n",
            [
                MutantResult(name="factory.domain.a.x_f__mutmut_1", status="killed"),
                MutantResult(name="factory.domain.a.xǁCǁm__mutmut_2", status="not checked"),
            ],
            id="two-lines-and-a-blank-one",
        ),
        pytest.param("", [], id="empty"),
        *(
            pytest.param(
                f"factory.domain.a.x_f__mutmut_1: {status}\n",
                [MutantResult(name="factory.domain.a.x_f__mutmut_1", status=status)],
                id=f"status-{status}",
            )
            for status in STATUSES
        ),
        *(
            pytest.param(f"{line}\n", f"not a result line of mutmut: {line!r}", id=case)
            for line, case in (
                ("factory.domain.a.x_f__mutmut_1 killed", "no-separator"),
                ("factory.domain.a.x_f__mutmut_1: dead", "unknown-status"),
                ("x_f__mutmut_1: killed", "no-dot"),
                ("factory..x_f__mutmut_1: killed", "empty-part"),
                ("factory.domain.a b.x_f__mutmut_1: killed", "whitespace-in-name"),
                ("factory.domain:a.x_f__mutmut_1: killed", "colon-in-name"),
                ("Warning: 3 files changed", "other-text"),
            )
        ),
    ],
)
def test_result_lines_are_read_in_their_order_and_other_lines_are_refused(
    text: str, expected: list[MutantResult] | str
) -> None:
    if isinstance(expected, str):
        with pytest.raises(ValueError, match=re.escape(expected)) as raised:
            parse_results(text)
        assert str(raised.value) == expected
    else:
        assert parse_results(text) == expected


@pytest.mark.parametrize(
    ("name", "module"),
    [
        ("factory.application.stage.xǁStageRunnerǁrun__mutmut_3", "factory.application.stage"),
        ("factory.entry.guard.x_main__mutmut_1", "factory.entry.guard"),
        ("a.b", "a"),
    ],
)
def test_the_module_of_a_mutant_is_its_name_without_the_last_part(name: str, module: str) -> None:
    assert MutantResult(name=name, status="killed").module == module


def test_the_report_lists_the_open_mutants_of_the_chosen_modules_and_counts_them() -> None:
    a = _results(
        A,
        "killed",
        "segfault",
        "survived",
        "timeout",
        "no tests",
        "suspicious",
        "skipped",
        "caught by type check",
        "check was interrupted by user",
    )
    b = _results(B, "survived")

    report = mutation_report([*a, *b], [A], stopped_after=None)

    assert report.lines == [
        f"{a[1].name}: segfault",
        f"{a[2].name}: survived",
        f"{a[3].name}: timeout",
        f"{a[5].name}: suspicious",
        "mutants: 1 killed, 1 survived, 1 timed out, 1 without tests, 0 not checked, "
        "5 other of 9 mutant(s) in 1 module(s)",
    ]
    assert report.partial is False


AB = "factory.domain.ab"


@pytest.mark.parametrize(
    ("results", "modules", "stopped_after", "partial", "last_line"),
    [
        pytest.param(
            [*_results(A, "killed"), *_results(B, "survived")],
            [A, B],
            None,
            False,
            r"mutants: \d.*",
            id="complete",
        ),
        pytest.param(
            [*_results(A, "killed"), *_results(B, "not checked")],
            [A, B],
            None,
            True,
            r"mutants: partial, .*\b1 not checked\b.*",
            id="not-checked",
        ),
        pytest.param(
            [*_results(A, "killed"), *_results(B, "killed")],
            [A, B],
            540,
            True,
            r".* \(stopped after 540 s\)",
            id="stopped",
        ),
        pytest.param(
            [*_results(A, "killed"), *_results(B, "killed")],
            [C],
            None,
            False,
            re.escape(
                "mutants: 0 killed, 0 survived, 0 timed out, 0 without tests, 0 not checked, "
                "0 other of 0 mutant(s) in 1 module(s)"
            ),
            id="no-result-of-the-module",
        ),
        pytest.param(
            [*_results(A, "killed"), *_results(B, "killed")],
            [A, A],
            None,
            False,
            r".* in 1 module\(s\)",
            id="module-given-twice",
        ),
        pytest.param(
            [
                *_results(A, "killed", "killed"),
                *_results(B, "not checked"),
                *_results(AB, "not checked"),
            ],
            [A],
            None,
            False,
            re.escape(
                "mutants: 2 killed, 0 survived, 0 timed out, 0 without tests, 0 not checked, "
                "0 other of 2 mutant(s) in 1 module(s)"
            ),
            id="other-modules-left-out",
        ),
    ],
)
def test_a_report_is_partial_while_a_mutant_is_not_checked_or_the_run_stopped(
    results: list[MutantResult],
    modules: list[str],
    stopped_after: int | None,
    partial: bool,
    last_line: str,
) -> None:
    report = mutation_report(results, modules, stopped_after=stopped_after)

    assert report.partial is partial
    assert re.fullmatch(last_line, report.lines[-1])


@pytest.mark.parametrize(
    ("stopped_after", "error"),
    [
        pytest.param(0, "stopped_after must be at least 1, not 0", id="zero"),
        pytest.param(1, None, id="one"),
    ],
)
def test_stopped_after_is_at_least_one_second(stopped_after: int, error: str | None) -> None:
    results = _results(A, "killed")

    if error is not None:
        with pytest.raises(ValueError, match=re.escape(error)) as raised:
            mutation_report(results, [A], stopped_after=stopped_after)
        assert str(raised.value) == error
    else:
        report = mutation_report(results, [A], stopped_after=stopped_after)
        assert report.partial is True
        assert report.lines[-1].endswith(" (stopped after 1 s)")


FIRST_A = _results(A, "killed", "survived", "not checked", "no tests", "caught by type check")
FIRST = [*FIRST_A, *_results(B, "survived")]
EVERY_STATUS = _results(A, *STATUSES)


@pytest.mark.parametrize(
    ("results", "modules", "expected"),
    [
        pytest.param(
            FIRST, [A, C], [*_names(FIRST_A, 1, 2, 3), f"{C}.*"], id="open-mutants-and-a-pattern"
        ),
        pytest.param(_results(A, "killed", "killed"), [A], [], id="every-mutant-killed"),
        pytest.param(FIRST, [A, C, C], [*_names(FIRST_A, 1, 2, 3), f"{C}.*"], id="pattern-once"),
        pytest.param(
            EVERY_STATUS,
            [A],
            [
                result.name
                for result in EVERY_STATUS
                if result.status not in ("killed", "caught by type check")
            ],
            id="every-status",
        ),
        pytest.param(
            FIRST,
            [D, A, C],
            [*_names(FIRST_A, 1, 2, 3), f"{D}.*", f"{C}.*"],
            id="patterns-in-the-given-order",
        ),
    ],
)
def test_the_names_to_run_again_are_the_unkilled_mutants_and_modules_without_one(
    results: list[MutantResult], modules: list[str], expected: list[str]
) -> None:
    assert rerun_names(results, modules) == expected
