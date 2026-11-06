"""The runnable examples of a document: the `console` blocks, what is skipped, the matching."""

import pytest

from factory.shared.domain.documents import Command, Example, Skipped, examples, matches

FENCE = "```"


def test_a_console_block_gives_its_fixture_commands_and_expected_output_in_order() -> None:
    text = "\n".join(
        [
            "# A guide",
            "",
            f"{FENCE}console",
            "$ echo hi",
            "hi",
            "$ printf 'a\\nb\\n'",
            "a",
            "b",
            FENCE,
            "",
            f"{FENCE}console fixture=instance",
            "$ true",
            FENCE,
            "",
            f"{FENCE}console fixture=checkout",
            "$ pytest tests/shared/test_one.py",
            "1 passed",
            FENCE,
            "",
        ]
    )

    found = examples(text)

    assert found.runnable == [
        Example(
            line=3,
            fixture="checkout",
            commands=[
                Command(line=4, command="echo hi", expected=["hi"]),
                Command(line=6, command="printf 'a\\nb\\n'", expected=["a", "b"]),
            ],
        ),
        Example(
            line=11, fixture="instance", commands=[Command(line=12, command="true", expected=[])]
        ),
        Example(
            line=15,
            fixture="checkout",
            commands=[
                Command(line=16, command="pytest tests/shared/test_one.py", expected=["1 passed"])
            ],
        ),
    ]
    assert found.skipped == []


@pytest.mark.parametrize(
    ("info", "command", "kind"),
    [
        pytest.param("console vm", "factory status", "vm", id="vm"),
        pytest.param("console github", "factory tick", "github", id="github"),
        pytest.param("console model", "factory run", "model", id="model"),
        pytest.param("console", "make check", "suite", id="make-check"),
        pytest.param("console", "make test", "suite", id="make-test"),
        pytest.param("console", "pytest", "suite", id="pytest-without-a-file"),
    ],
)
def test_a_marked_block_or_one_that_runs_the_suite_is_skipped_with_its_kind(
    info: str, command: str, kind: str
) -> None:
    text = "\n".join(["# A guide", "", f"{FENCE}{info}", f"$ {command}", "ok", FENCE, ""])

    found = examples(text)

    assert found.runnable == []
    assert found.skipped == [Skipped(line=3, kind=kind)]


@pytest.mark.parametrize(
    ("expected", "actual", "result"),
    [
        pytest.param(["hi", "there"], ["hi", "there"], True, id="equal-lines"),
        pytest.param(["hi"], ["ho"], False, id="different-line"),
        pytest.param(["first", "...", "last"], ["first", "last"], True, id="dots-for-no-lines"),
        pytest.param(
            ["first", "...", "last"], ["first", "a", "last"], True, id="dots-for-one-line"
        ),
        pytest.param(
            ["first", "...", "last"], ["first", "a", "b", "c", "last"], True, id="dots-for-lines"
        ),
        pytest.param(["started at <time>"], ["started at 07:31:52"], True, id="placeholder"),
        pytest.param(["<id> done"], ["a1b2 done"], True, id="placeholder-at-start"),
        pytest.param(
            ["started at <time>"], ["ended at 07:31:52"], False, id="placeholder-other-text"
        ),
        pytest.param(["one", "two"], ["one"], False, id="missing-line"),
        pytest.param(["one"], ["one", "two"], False, id="extra-line"),
        pytest.param([], [], True, id="no-lines"),
        pytest.param([], ["printed"], False, id="extra-line-after-none"),
    ],
)
def test_matches_accepts_equal_lines_and_the_placeholders_and_refuses_missing_or_extra_lines(
    expected: list[str], actual: list[str], result: bool
) -> None:
    assert matches(expected, actual) is result
