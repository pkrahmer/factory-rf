"""The duplicates report: findings keyed without line numbers, compared with a baseline."""

import json
import re

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.duplicates import (
    DuplicateFinding,
    DuplicateReport,
    compare,
    dead_code_findings,
    read_baseline,
    report_lines,
    similar_code_findings,
)

STOPS_AND_GIT = (
    "Similar lines in 2 files\n"
    "==factory.domain.stops:[49:53]\n"
    "==factory.domain.git:[73:77]\n"
    '    @field_validator("at")\n'
    "    @classmethod"
)
STOPS_AND_GIT_KEY = 'similar-code factory.domain.git, factory.domain.stops: @field_validator("at")'
HELPER_LINE = "src/factory/x.py:12: unused function 'helper' (60% confidence)"
HELPER_KEY = "dead-code src/factory/x.py: unused function 'helper'"


def _pylint(*messages: str) -> str:
    return json.dumps([{"symbol": "duplicate-code", "message": message} for message in messages])


def _finding(key: str) -> DuplicateFinding:
    return DuplicateFinding(key=key, where=f"{key}.py:1", message=f"about {key}")


def test_a_duplicate_code_message_gives_its_key_where_and_first_line() -> None:
    findings = similar_code_findings(_pylint(STOPS_AND_GIT))

    assert findings == [
        DuplicateFinding(
            key=STOPS_AND_GIT_KEY,
            where="factory.domain.stops:[49:53], factory.domain.git:[73:77]",
            message="Similar lines in 2 files",
        )
    ]


@pytest.mark.parametrize(
    ("message", "same_key"),
    [
        (STOPS_AND_GIT.replace("[49:53]", "[149:153]").replace("[73:77]", "[7:11]"), True),
        (STOPS_AND_GIT.replace("[73:77]\n", "[73:77]\n\n"), True),
        (STOPS_AND_GIT.replace('@field_validator("at")', '@field_validator("until")'), False),
    ],
    ids=["other-line-numbers", "blank-line-before-code", "other-first-code-line"],
)
def test_the_key_ignores_line_numbers_and_blank_lines_but_not_the_code(
    message: str, same_key: bool
) -> None:
    [finding] = similar_code_findings(_pylint(message))

    assert (finding.key == STOPS_AND_GIT_KEY) is same_key


@pytest.mark.parametrize(
    ("pylint_json", "keys"),
    [
        (
            _pylint("Similar lines in 2 files\n==factory.a:[1:5]\n==factory.a:[9:13]\n    x = 1"),
            ["similar-code factory.a: x = 1"],
        ),
        (json.dumps([{"symbol": "unused-import", "message": "Unused import os"}]), []),
        ("[]", []),
    ],
    ids=["one-module-twice", "other-symbol", "empty-array"],
)
def test_modules_are_unique_in_the_key_and_other_symbols_give_nothing(
    pylint_json: str, keys: list[str]
) -> None:
    assert [finding.key for finding in similar_code_findings(pylint_json)] == keys


@pytest.mark.parametrize(
    "pylint_json",
    [
        "not json",
        "{}",
        "[1]",
        '[{"symbol": "duplicate-code"}]',
        '[{"symbol": "duplicate-code", "message": 5}]',
    ],
    ids=["not-json", "not-an-array", "element-not-an-object", "no-message", "message-not-a-string"],
)
def test_an_unreadable_pylint_text_is_refused(pylint_json: str) -> None:
    with pytest.raises(ValueError):
        similar_code_findings(pylint_json)


@pytest.mark.parametrize(
    ("message", "valid"),
    [
        ("Similar lines in 2 files\n    x = 1", False),
        ("Similar lines in 2 files\n==factory.a:[1:5]\n==factory.b:[9:13]\n", False),
        ("Similar lines in 2 files\n==factory.a\n    x = 1", False),
        ("Similar lines in 2 files\n==factory.a:[1:5]\n==factory.b:[9:13]\n    x = 1", True),
    ],
    ids=["no-module-line", "no-code-line", "malformed-module-line", "valid"],
)
def test_a_duplicate_code_message_out_of_form_is_refused_by_name(message: str, valid: bool) -> None:
    if valid:
        assert len(similar_code_findings(_pylint(message))) == 1
        return
    with pytest.raises(ValueError, match="Similar lines in 2 files"):
        similar_code_findings(_pylint(message))


@pytest.mark.parametrize(
    ("vulture_text", "keys"),
    [
        (HELPER_LINE + "\n", [HELPER_KEY]),
        (HELPER_LINE.replace(")", ", 3 lines)") + "\n", [HELPER_KEY]),
        (HELPER_LINE.replace(")", ", 1 line)") + "\n", [HELPER_KEY]),
        ("\n", []),
    ],
    ids=["plain", "three-lines", "one-line", "blank"],
)
def test_a_vulture_line_gives_its_key_without_the_line_number(
    vulture_text: str, keys: list[str]
) -> None:
    findings = dead_code_findings(vulture_text)

    assert [finding.key for finding in findings] == keys
    if vulture_text == HELPER_LINE + "\n":
        assert findings[0].where == "src/factory/x.py:12"
        assert findings[0].message == "unused function 'helper' (60% confidence)"


@pytest.mark.parametrize(
    ("vulture_text", "line_number"),
    [
        (HELPER_LINE + "\noops\n", 2),
        ("src/x.py: unused function 'f' (60% confidence)\n", 1),
        (HELPER_LINE + "\n" + HELPER_LINE + "\n  " + HELPER_LINE + "\n", 3),
    ],
    ids=["second-line-oops", "no-line-number", "leading-spaces"],
)
def test_a_vulture_line_out_of_form_is_refused_by_its_line_number(
    vulture_text: str, line_number: int
) -> None:
    with pytest.raises(ValueError) as refused:
        dead_code_findings(vulture_text)

    assert re.search(rf"\b{line_number}\b", str(refused.value))


def test_the_baseline_skips_blank_and_comment_lines_and_strips_keys() -> None:
    text = "# comment\n\n  similar-code a, b: x  \n  # indented comment\ndead-code p: m\n"

    assert read_baseline(text) == ["similar-code a, b: x", "dead-code p: m"]


@pytest.mark.parametrize(
    ("baseline", "new_keys", "known", "gone"),
    [
        (["e", "b", "c"], ["a", "d"], 2, ["e", "c"]),
        ([], ["a", "d", "b", "b"], 0, []),
    ],
    ids=["baseline", "empty-baseline"],
)
def test_compare_splits_findings_into_new_known_and_gone(
    baseline: list[str], new_keys: list[str], known: int, gone: list[str]
) -> None:
    findings = [_finding(key) for key in ["a", "d", "b", "b"]]

    report = compare(findings, baseline)

    assert report == DuplicateReport(
        new=[_finding(key) for key in new_keys], known=known, gone=gone
    )


@pytest.mark.parametrize(
    ("report", "lines"),
    [
        (
            DuplicateReport(new=[_finding("a"), _finding("d")], known=2, gone=["e", "c"]),
            [
                "new a at a.py:1: about a",
                "new d at d.py:1: about d",
                "gone e",
                "gone c",
                "duplicates: 2 new, 2 known, 2 gone",
            ],
        ),
        (DuplicateReport(new=[], known=3, gone=[]), ["duplicates: 0 new, 3 known, 0 gone"]),
    ],
    ids=["new-and-gone", "nothing-new-or-gone"],
)
def test_report_lines_list_new_then_gone_then_the_closing_line(
    report: DuplicateReport, lines: list[str]
) -> None:
    assert report_lines(report) == lines


@pytest.mark.parametrize(("known", "accepted"), [(-1, False), (0, True)], ids=["-1", "0"])
def test_the_known_count_is_not_negative(known: int, accepted: bool) -> None:
    model: type[BaseModel] = DuplicateReport
    if accepted:
        model(new=[], known=known, gone=[])
        return
    with pytest.raises(ValidationError):
        model(new=[], known=known, gone=[])
