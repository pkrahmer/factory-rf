"""The rules across the keys of the pipeline definition refuse a text when it is read."""

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from git_support import PIPELINE_YAML, pipeline_outcome

CONTRACT = 'contract: "1.0"'
CODER = '  coder: {write_paths: ["src/*"]}'
TESTER = '  tester: {write_paths: ["tests/*"]}'
DOCUMENTER = '  documenter: {write_paths: ["README.md", "docs/*"]}'
TESTS_STAGE = "  tests: {role: tester, next: [doing], checks: [lint], reports: [test]}"
DOING_STAGE = "  doing: {role: coder, next: [review, tests], checks: [check]}"
REVIEW_STAGE = "  review: {role: reviewer, next: [docs, doing], round_cap: 3}"
APPROVAL_STAGE = "  approval: {approval: true, next: [done, doing]}"
DONE_STAGE = "  done: {}"
ROLES = "roles:\n"


def _changed(text: str, *replacements: tuple[str, str]) -> str:
    for old, new in replacements:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


def _coder(time_limit: int) -> tuple[str, str]:
    return CODER, f'  coder: {{time_limit: {time_limit}, write_paths: ["src/*"]}}'


def _tester(time_limit: int) -> tuple[str, str]:
    return TESTER, f'  tester: {{time_limit: {time_limit}, write_paths: ["tests/*"]}}'


def _doing_next(names: str) -> tuple[str, str]:
    return DOING_STAGE, DOING_STAGE.replace("[review, tests]", names)


def test_the_test_pipeline_definition_passes_every_rule() -> None:
    RuamelPipelineDefinitionReader().parse(PIPELINE_YAML)


@pytest.mark.parametrize(
    ("contract", "major"), [("2.0", "2"), ("0.9", "0"), ("10.0", "10"), ("02.0", "02")]
)
def test_a_contract_major_other_than_one_is_refused(contract: str, major: str) -> None:
    text = _changed(PIPELINE_YAML, (CONTRACT, f'contract: "{contract}"'))

    assert pipeline_outcome(text) == (
        f"contract major {major} is not supported (this factory reads major 1)"
    )


@pytest.mark.parametrize("contract", ["1.0", "1.7", "1.10", "01.0"])
def test_a_contract_of_major_one_is_accepted_for_any_minor(contract: str) -> None:
    text = _changed(PIPELINE_YAML, (CONTRACT, f'contract: "{contract}"'))

    assert pipeline_outcome(text) is None


@pytest.mark.parametrize("contract", ["1", "1.0.0", "v1.0", "1.x"])
def test_a_contract_without_major_and_minor_is_refused(contract: str) -> None:
    text = _changed(PIPELINE_YAML, (CONTRACT, f'contract: "{contract}"'))

    assert pipeline_outcome(text) == f"contract must look like <major>.<minor>, got '{contract}'"


def test_a_definition_without_a_done_stage_is_refused() -> None:
    text = PIPELINE_YAML.replace("done", "finished")

    assert pipeline_outcome(text) == "stages must hold a stage named done"


@pytest.mark.parametrize("done", ["  done: {role: coder}", "  done: {next: [doing]}"])
def test_a_done_stage_with_a_role_or_a_next_is_refused(done: str) -> None:
    text = _changed(PIPELINE_YAML, (DONE_STAGE, done))

    assert pipeline_outcome(text) == "stage done must have no role and no next"


def test_a_next_naming_an_unknown_stage_is_refused() -> None:
    text = _changed(PIPELINE_YAML, _doing_next("[review, ship]"))

    assert pipeline_outcome(text) == "stage doing: next names unknown stage ship"


def test_every_unknown_next_is_a_fault_of_its_own_in_the_order_of_the_text() -> None:
    text = _changed(
        PIPELINE_YAML,
        (TESTS_STAGE, TESTS_STAGE.replace("[doing]", "[doing, nowhere]")),
        _doing_next("[ship, review, harbour]"),
    )

    assert pipeline_outcome(text) == (
        "stage tests: next names unknown stage nowhere; "
        "stage doing: next names unknown stage ship; "
        "stage doing: next names unknown stage harbour"
    )


def test_a_stage_with_an_undefined_role_is_refused() -> None:
    text = _changed(PIPELINE_YAML, (REVIEW_STAGE, REVIEW_STAGE.replace("reviewer", "ghost")))

    assert pipeline_outcome(text) == "stage review: role ghost is not defined in roles"


@pytest.mark.parametrize(
    ("write_paths", "fault"),
    [("[]", "role documenter: write_paths is empty"), ('["docs/*"]', None)],
)
def test_a_role_needs_at_least_one_write_path(write_paths: str, fault: str | None) -> None:
    text = _changed(PIPELINE_YAML, (DOCUMENTER, f"  documenter: {{write_paths: {write_paths}}}"))

    assert pipeline_outcome(text) == fault


def test_an_approval_stage_with_a_role_is_refused() -> None:
    text = _changed(
        PIPELINE_YAML, (APPROVAL_STAGE, APPROVAL_STAGE.replace("true,", "true, role: coder,"))
    )

    assert pipeline_outcome(text) == "stage approval: an approval stage has no role"


def test_the_role_checks_report_undefined_roles_then_empty_paths_then_approval_roles() -> None:
    text = _changed(
        PIPELINE_YAML,
        (DONE_STAGE, "  x: {role: ghost, next: [done]}\n" + DONE_STAGE),
        (DOCUMENTER, "  documenter: {write_paths: []}"),
        (APPROVAL_STAGE, APPROVAL_STAGE.replace("true,", "true, role: coder,")),
    )

    assert pipeline_outcome(text) == (
        "stage x: role ghost is not defined in roles; "
        "role documenter: write_paths is empty; "
        "stage approval: an approval stage has no role"
    )


@pytest.mark.parametrize("name", ["human", "factory", "question"])
def test_a_reserved_stage_name_is_refused(name: str) -> None:
    text = _changed(
        PIPELINE_YAML, (DONE_STAGE, f"  {name}: {{role: coder, next: [done]}}\n{DONE_STAGE}")
    )

    assert pipeline_outcome(text) == f"stage name {name} is reserved"


@pytest.mark.parametrize("name", ["human", "factory", "question"])
def test_a_reserved_role_name_is_refused(name: str) -> None:
    text = _changed(PIPELINE_YAML, (ROLES, f'{ROLES}  {name}: {{write_paths: ["x/*"]}}\n'))

    assert pipeline_outcome(text) == f"role name {name} is reserved"


@pytest.mark.parametrize(
    ("old", "new", "fault"),
    [
        (
            DOING_STAGE,
            DOING_STAGE.replace("checks: [check]", "checks: [ghost]"),
            "stage doing: check ghost is not a project command",
        ),
        (
            TESTS_STAGE,
            TESTS_STAGE.replace("reports: [test]", "reports: [ghost]"),
            "stage tests: report ghost is not a project command",
        ),
    ],
)
def test_checks_and_reports_must_name_project_commands(old: str, new: str, fault: str) -> None:
    text = _changed(PIPELINE_YAML, (old, new))

    assert pipeline_outcome(text) == fault


@pytest.mark.parametrize(
    ("time_limit", "fault"),
    [(50, None), (51, "role coder at stage doing: 61 min exceed lease_duration 60 min")],
)
def test_a_role_time_limit_and_its_stage_checks_must_fit_the_lease(
    time_limit: int, fault: str | None
) -> None:
    text = _changed(PIPELINE_YAML, _coder(time_limit))

    assert pipeline_outcome(text) == fault


@pytest.mark.parametrize(
    ("time_limit", "fault"),
    [(45, None), (46, "role tester at stage tests: 61 min exceed lease_duration 60 min")],
)
def test_the_time_limits_of_checks_and_reports_both_count(
    time_limit: int, fault: str | None
) -> None:
    text = _changed(PIPELINE_YAML, _tester(time_limit))

    assert pipeline_outcome(text) == fault


def test_each_role_is_measured_against_its_own_lease() -> None:
    text = _changed(
        PIPELINE_YAML,
        (CODER, '  coder: {lease_duration: 90, time_limit: 70, write_paths: ["src/*"]}'),
        _tester(70),
    )

    assert pipeline_outcome(text) == (
        "role tester at stage tests: 85 min exceed lease_duration 60 min"
    )


def test_a_role_used_by_two_stages_is_measured_at_each_stage() -> None:
    text = _changed(
        PIPELINE_YAML,
        (DONE_STAGE, "  extra: {role: coder, next: [done]}\n" + DONE_STAGE),
        _coder(55),
    )

    assert pipeline_outcome(text) == (
        "role coder at stage doing: 65 min exceed lease_duration 60 min"
    )


def test_a_command_listed_twice_counts_twice() -> None:
    text = _changed(
        PIPELINE_YAML,
        (DOING_STAGE, DOING_STAGE.replace("checks: [check]", "checks: [check, check]")),
        _coder(41),
    )

    assert pipeline_outcome(text) == (
        "role coder at stage doing: 61 min exceed lease_duration 60 min"
    )


@pytest.mark.parametrize(
    ("replacements", "fault"),
    [
        (
            [
                (DOING_STAGE, DOING_STAGE.replace("checks: [check]", "checks: [ghost]")),
                _coder(60),
            ],
            "stage doing: check ghost is not a project command",
        ),
        (
            [(APPROVAL_STAGE, APPROVAL_STAGE.replace("}", ", checks: [check]}"))],
            None,
        ),
    ],
)
def test_unknown_commands_and_stages_without_a_role_add_no_minutes(
    replacements: list[tuple[str, str]], fault: str | None
) -> None:
    text = _changed(PIPELINE_YAML, *replacements)

    assert pipeline_outcome(text) == fault


@pytest.mark.parametrize(
    ("stage", "fault"),
    [
        ("nowhere", "acceptance_stage nowhere is not a stage with a role"),
        ("approval", "acceptance_stage approval is not a stage with a role"),
        ("acceptance", None),
    ],
)
def test_the_acceptance_stage_must_be_a_stage_with_a_role(stage: str, fault: str | None) -> None:
    text = _changed(PIPELINE_YAML, ("acceptance_stage: acceptance", f"acceptance_stage: {stage}"))

    assert pipeline_outcome(text) == fault


def test_faults_of_two_rules_are_reported_together_in_the_order_of_the_rules() -> None:
    text = _changed(PIPELINE_YAML, _doing_next("[review, ship]"), _coder(51))

    assert pipeline_outcome(text) == (
        "stage doing: next names unknown stage ship; "
        "role coder at stage doing: 61 min exceed lease_duration 60 min"
    )


def test_the_rules_run_only_when_every_field_is_valid() -> None:
    text = _changed(
        PIPELINE_YAML,
        (CODER, '  coder: {lease_duration: 0, write_paths: ["src/*"]}'),
        _doing_next("[review, ship]"),
    )

    fault = pipeline_outcome(text)

    assert fault is not None
    assert fault.startswith("invalid roles.coder.lease_duration:")
    assert "ship" not in fault
