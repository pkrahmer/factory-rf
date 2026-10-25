"""The paths a project command does not read: their default, their order and their load rule."""

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from git_support import PIPELINE_YAML, pipeline_outcome

CHECK_LINE = "  check: {time_limit: 10}\n"
LINT_LINE = "  lint: {time_limit: 5}\n"


def _with_check(not_read: str) -> str:
    return PIPELINE_YAML.replace(CHECK_LINE, f"  check: {{time_limit: 10, not_read: {not_read}}}\n")


def _fault(command: str, pattern: str) -> str:
    return (
        f"project command {command}: not_read {pattern} must be a path pattern inside the checkout"
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(PIPELINE_YAML, [], id="absent"),
        pytest.param(_with_check('["README.md", "docs/*"]'), ["README.md", "docs/*"], id="two"),
    ],
)
def test_not_read_loads_in_order_and_defaults_to_nothing(text: str, expected: list[str]) -> None:
    commands = RuamelPipelineDefinitionReader().parse(text).project_commands

    assert commands["check"].not_read == expected
    assert commands["lint"].not_read == []
    assert commands["test"].not_read == []


ACCEPTED = [
    "docs/*",
    "*.md",
    ".github/*",
    "factory/features/*",
    "docs/~old/*",
    "docs/a..b/*",
    "docs..x/*",
]
REFUSED = ["/etc/*", "~/notes/*", "../docs/*", "docs/../src/*", "{work_item}", "docs/{x", "docs/x}"]


@pytest.mark.parametrize(
    ("text", "fault"),
    [
        *(pytest.param(_with_check(f'["{p}"]'), None, id=f"accepts-{p}") for p in ACCEPTED),
        *(pytest.param(_with_check(f'["{p}"]'), _fault("check", p), id=p) for p in REFUSED),
        pytest.param(
            _with_check('["/a/*"]').replace(
                LINT_LINE, '  lint: {time_limit: 5, not_read: ["/a/*"]}\n'
            ),
            f"{_fault('check', '/a/*')}; {_fault('lint', '/a/*')}",
            id="two-commands",
        ),
        pytest.param(
            _with_check('["/b/*", "/a/*"]'),
            f"{_fault('check', '/b/*')}; {_fault('check', '/a/*')}",
            id="two-patterns",
        ),
    ],
)
def test_a_not_read_pattern_outside_the_checkout_is_refused(text: str, fault: str | None) -> None:
    assert pipeline_outcome(text) == fault


@pytest.mark.parametrize(
    "value",
    [
        pytest.param('"docs/*"', id="string"),
        pytest.param("[1]", id="number"),
        pytest.param('[""]', id="empty"),
        pytest.param('[" "]', id="blank"),
    ],
)
def test_a_not_read_that_is_not_a_list_of_patterns_is_refused(value: str) -> None:
    fault = pipeline_outcome(_with_check(value))

    assert fault is not None
    assert "not_read" in fault
