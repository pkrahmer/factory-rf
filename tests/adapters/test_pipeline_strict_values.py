"""The pipeline definition takes a value only in its own YAML type, and no blank write path."""

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from git_support import PIPELINE_YAML, pipeline_outcome

CODER = '  coder: {write_paths: ["src/*"]}'
TESTS_STAGE = "  tests: {role: tester, next: [doing], checks: [lint], reports: [test]}"
DOING_STAGE = "  doing: {role: coder, next: [review, tests], checks: [check]}"
REVIEW_STAGE = "  review: {role: reviewer, next: [docs, doing], round_cap: 3}"
APPROVAL_STAGE = "  approval: {approval: true, next: [done, doing]}"

# Each integer limit: its key path, the line that sets it, and that line with the value as `{}`.
INTEGER_LIMITS = {
    "roles.coder.lease_duration": (
        CODER,
        '  coder: {{lease_duration: {}, write_paths: ["src/*"]}}',
    ),
    "roles.coder.time_limit": (CODER, '  coder: {{time_limit: {}, write_paths: ["src/*"]}}'),
    "attempts_cap": ("attempts_cap: 2", "attempts_cap: {}"),
    "crash_cap": ("crash_cap: 2", "crash_cap: {}"),
    "stages.review.round_cap": (
        REVIEW_STAGE,
        "  review: {{role: reviewer, next: [docs, doing], round_cap: {}}}",
    ),
    "project_commands.lint.time_limit": ("  lint: {time_limit: 5}", "  lint: {{time_limit: {}}}"),
}
ACCEPTED_INTEGERS = {
    "roles.coder.lease_duration": "50",
    "roles.coder.time_limit": "30",
    "attempts_cap": "30",
    "crash_cap": "30",
    "stages.review.round_cap": "30",
    "project_commands.lint.time_limit": "10",
}


def _changed(text: str, *replacements: tuple[str, str]) -> str:
    for old, new in replacements:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


def _limit(path: str, value: str) -> tuple[str, str]:
    old, template = INTEGER_LIMITS[path]
    return old, template.format(value)


def test_the_test_pipeline_definition_still_parses() -> None:
    RuamelPipelineDefinitionReader().parse(PIPELINE_YAML)


@pytest.mark.parametrize("value", ["true", "'30'", "30.0"])
@pytest.mark.parametrize("path", list(INTEGER_LIMITS))
def test_an_integer_limit_not_written_as_an_integer_is_refused(path: str, value: str) -> None:
    fault = pipeline_outcome(_changed(PIPELINE_YAML, _limit(path, value)))

    assert fault is not None
    assert fault.startswith(f"invalid {path}:")


@pytest.mark.parametrize("path", list(INTEGER_LIMITS))
def test_an_integer_limit_written_as_an_integer_is_accepted(path: str) -> None:
    text = _changed(PIPELINE_YAML, _limit(path, ACCEPTED_INTEGERS[path]))

    assert pipeline_outcome(text) is None


@pytest.mark.parametrize("value", ["'yes'", "'off'", "1", "0"])
def test_an_approval_not_written_as_a_boolean_is_refused(value: str) -> None:
    text = _changed(
        PIPELINE_YAML, (APPROVAL_STAGE, f"  approval: {{approval: {value}, next: [done, doing]}}")
    )

    fault = pipeline_outcome(text)

    assert fault is not None
    assert fault.startswith("invalid stages.approval.approval:")


def test_an_approval_written_as_true_is_accepted() -> None:
    assert APPROVAL_STAGE in PIPELINE_YAML
    assert pipeline_outcome(PIPELINE_YAML) is None


def test_an_approval_written_as_false_is_accepted() -> None:
    text = _changed(
        PIPELINE_YAML,
        (DOING_STAGE, DOING_STAGE.replace("{role: coder,", "{role: coder, approval: false,")),
    )

    assert pipeline_outcome(text) is None


@pytest.mark.parametrize("write_path", ["''", "'  '"])
def test_a_blank_write_path_is_refused_at_its_position(write_path: str) -> None:
    text = _changed(PIPELINE_YAML, (CODER, f"  coder: {{write_paths: [{write_path}]}}"))

    fault = pipeline_outcome(text)

    assert fault is not None
    assert fault.startswith("invalid roles.coder.write_paths[0]:")


@pytest.mark.parametrize("write_path", ["'src/*'", "'{work_item}'"])
def test_a_write_path_with_text_is_accepted(write_path: str) -> None:
    text = _changed(PIPELINE_YAML, (CODER, f"  coder: {{write_paths: [{write_path}]}}"))

    assert pipeline_outcome(text) is None


@pytest.mark.parametrize(
    ("old", "new", "path"),
    [
        (
            DOING_STAGE,
            DOING_STAGE.replace("checks: [check]", "checks: [1]"),
            "stages.doing.checks[0]",
        ),
        (
            TESTS_STAGE,
            TESTS_STAGE.replace("reports: [test]", "reports: [1]"),
            "stages.tests.reports[0]",
        ),
    ],
)
def test_a_number_in_a_text_list_is_refused(old: str, new: str, path: str) -> None:
    fault = pipeline_outcome(_changed(PIPELINE_YAML, (old, new)))

    assert fault is not None
    assert fault.startswith(f"invalid {path}:")


def test_a_strict_value_fault_comes_alone_before_a_fault_of_the_rules() -> None:
    text = _changed(
        PIPELINE_YAML,
        _limit("roles.coder.time_limit", "true"),
        (DOING_STAGE, DOING_STAGE.replace("[review, tests]", "[review, ship]")),
    )

    fault = pipeline_outcome(text)

    assert fault is not None
    assert fault.startswith("invalid roles.coder.time_limit:")
    assert "ship" not in fault
