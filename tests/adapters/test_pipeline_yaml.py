"""The pipeline definition read from YAML: its defaults, and every fault named."""

from collections.abc import Callable

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
from factory.domain.pipeline_definition import PipelineDefinition
from git_support import PIPELINE_YAML

MINIMAL = """\
contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
  tester: {write_paths: ['tests/*']}
stages:
  tests: {role: tester, next: [doing]}
  doing: {role: coder, next: [done]}
  done: {}
"""

CODER = "  coder: {write_paths: ['src/*']}"
DOING = "  doing: {role: coder, next: [done]}"


def _parse(text: str) -> PipelineDefinition:
    return RuamelPipelineDefinitionReader().parse(text)


def _fault(text: str) -> str:
    with pytest.raises(PipelineDefinitionInvalid) as caught:
        _parse(text)
    return caught.value.fault


def _replaced(text: str, old: str, new: str) -> str:
    assert old in text
    return text.replace(old, new)


def test_example_definition_is_read_in_its_order() -> None:
    definition = _parse(PIPELINE_YAML)

    assert definition.contract == "1.0"
    assert definition.attempts_cap == 2
    assert definition.crash_cap == 2
    assert definition.acceptance_stage == "acceptance"
    assert len(definition.stages) == 9
    assert list(definition.stages)[0] == "intake"
    assert list(definition.stages)[-1] == "done"
    assert len(definition.roles) == 7
    assert definition.stages["doing"].next == ["review", "tests"]
    assert definition.stages["tests"].checks == ["lint"]
    assert definition.stages["tests"].reports == ["test"]
    assert definition.stages["review"].round_cap == 3
    assert definition.stages["approval"].approval is True
    assert definition.roles["coder"].write_paths == ["src/*"]


def test_first_stage_is_the_first_stage_of_the_text() -> None:
    assert _parse(PIPELINE_YAML).first_stage() == "intake"


def test_role_of_a_stage_is_its_role_or_none() -> None:
    definition = _parse(PIPELINE_YAML)

    assert definition.role_of("doing") == definition.roles["coder"]
    assert definition.role_of("approval") is None
    assert definition.role_of("done") is None


def test_role_of_an_unknown_stage_raises_key_error() -> None:
    with pytest.raises(KeyError):
        _parse(PIPELINE_YAML).role_of("nowhere")


@pytest.mark.parametrize(("stage", "index"), [("intake", 0), ("tests", 1), ("done", 8)])
def test_position_is_the_index_in_the_stages(stage: str, index: int) -> None:
    assert _parse(PIPELINE_YAML).position(stage) == index


def test_left_out_keys_with_defaults_take_them() -> None:
    role = _parse(PIPELINE_YAML).roles["coder"]
    definition = _parse(MINIMAL)

    assert role.lease_duration == 60
    assert role.time_limit == 40
    assert definition.attempts_cap == 2
    assert definition.crash_cap == 2
    assert definition.acceptance_stage is None


def test_an_empty_stage_takes_every_default() -> None:
    stage = _parse(MINIMAL).stages["done"]

    assert stage.role is None
    assert stage.next == []
    assert stage.approval is False
    assert stage.checks == []
    assert stage.reports == []
    assert stage.round_cap is None


def test_left_out_project_commands_are_check_lint_and_test() -> None:
    commands = _parse(MINIMAL).project_commands

    assert sorted(commands) == ["check", "lint", "test"]
    assert all(command.time_limit == 10 for command in commands.values())


def test_given_project_commands_replace_the_default_set() -> None:
    commands = _parse(MINIMAL + "project_commands: {check: {time_limit: 3}}\n").project_commands

    assert list(commands) == ["check"]
    assert commands["check"].time_limit == 3


def test_an_empty_project_command_takes_the_default_time_limit() -> None:
    commands = _parse(MINIMAL + "project_commands: {lint: {}}\n").project_commands

    assert commands["lint"].time_limit == 10


def test_given_values_replace_the_defaults() -> None:
    text = _replaced(
        PIPELINE_YAML,
        '  coder: {write_paths: ["src/*"]}',
        '  coder: {write_paths: ["src/*"], lease_duration: 90, time_limit: 25}',
    )
    text = _replaced(text, "attempts_cap: 2", "attempts_cap: 5")
    text = _replaced(text, "crash_cap: 2", "crash_cap: 3")

    definition = _parse(text)

    assert definition.roles["coder"].lease_duration == 90
    assert definition.roles["coder"].time_limit == 25
    assert definition.attempts_cap == 5
    assert definition.crash_cap == 3


def test_a_text_without_contract_is_refused() -> None:
    assert _fault(_replaced(MINIMAL, "contract: '1.0'\n", "")) == "missing key: contract"


def test_a_text_without_stages_is_refused() -> None:
    text = MINIMAL.partition("stages:\n")[0]

    assert _fault(text) == "missing key: stages"


def test_a_text_without_roles_is_refused() -> None:
    text = _replaced(MINIMAL, "roles:\n" + CODER + "\n  tester: {write_paths: ['tests/*']}\n", "")

    assert _fault(text) == "missing key: roles"


def test_a_role_without_write_paths_is_refused() -> None:
    assert (
        _fault(_replaced(MINIMAL, CODER, "  coder: {}")) == "missing key: roles.coder.write_paths"
    )


@pytest.mark.parametrize(
    ("text", "fault"),
    [
        (MINIMAL + "lease_minutes: 60\n", "unknown key: lease_minutes"),
        (
            _replaced(MINIMAL, DOING, "  doing: {role: coder, next: [done], agent: coder}"),
            "unknown key: stages.doing.agent",
        ),
        (
            _replaced(MINIMAL, CODER, "  coder: {write_paths: ['src/*'], lanes: []}"),
            "unknown key: roles.coder.lanes",
        ),
    ],
    ids=["top-level", "stage", "role"],
)
def test_an_unknown_key_is_refused_by_its_path(text: str, fault: str) -> None:
    assert _fault(text) == fault


def _with_limit(path: str, value: int) -> str:
    if path == "roles.coder.lease_duration":
        new = f"  coder: {{write_paths: ['src/*'], lease_duration: {value}, time_limit: 1}}"
        return _replaced(MINIMAL, CODER, new)
    if path == "roles.coder.time_limit":
        new = f"  coder: {{write_paths: ['src/*'], time_limit: {value}}}"
        return _replaced(MINIMAL, CODER, new)
    if path == "stages.doing.round_cap":
        new = f"  doing: {{role: coder, next: [done], round_cap: {value}}}"
        return _replaced(MINIMAL, DOING, new)
    if path == "project_commands.check.time_limit":
        return MINIMAL + f"project_commands: {{check: {{time_limit: {value}}}}}\n"
    return MINIMAL + f"{path}: {value}\n"


LIMITS: dict[str, Callable[[PipelineDefinition], int | None]] = {
    "roles.coder.lease_duration": lambda definition: definition.roles["coder"].lease_duration,
    "roles.coder.time_limit": lambda definition: definition.roles["coder"].time_limit,
    "attempts_cap": lambda definition: definition.attempts_cap,
    "crash_cap": lambda definition: definition.crash_cap,
    "stages.doing.round_cap": lambda definition: definition.stages["doing"].round_cap,
    "project_commands.check.time_limit": (
        lambda definition: definition.project_commands["check"].time_limit
    ),
}


@pytest.mark.parametrize("path", list(LIMITS))
@pytest.mark.parametrize("value", [0, -1])
def test_a_limit_below_one_is_refused(path: str, value: int) -> None:
    assert _fault(_with_limit(path, value)).startswith(f"invalid {path}:")


@pytest.mark.parametrize("path", list(LIMITS))
def test_a_limit_of_one_is_accepted(path: str) -> None:
    assert LIMITS[path](_parse(_with_limit(path, 1))) == 1


@pytest.mark.parametrize(
    ("text", "name"),
    [
        (MINIMAL.replace("doing", "Doing"), "Doing"),
        (MINIMAL.replace("doing", "1st"), "1st"),
        (MINIMAL.replace("doing", "do_ing"), "do_ing"),
        (MINIMAL.replace("coder", "Coder"), "Coder"),
        (MINIMAL + "project_commands: {Check: {}}\n", "Check"),
    ],
    ids=[
        "stage-capital",
        "stage-digit-first",
        "stage-underscore",
        "role-capital",
        "command-capital",
    ],
)
def test_a_name_that_breaks_the_pattern_is_refused_naming_it(text: str, name: str) -> None:
    assert name in _fault(text)


@pytest.mark.parametrize("name", ["smoke-test", "a1"])
def test_a_well_formed_name_is_accepted_for_stage_role_and_command(name: str) -> None:
    stages = _parse(MINIMAL.replace("doing", name)).stages
    roles = _parse(MINIMAL.replace("coder", name)).roles
    commands = _parse(MINIMAL + f"project_commands: {{{name}: {{}}}}\n").project_commands

    assert name in stages
    assert name in roles
    assert name in commands


@pytest.mark.parametrize(
    ("text", "path"),
    [
        (_replaced(MINIMAL, DOING, "  doing: {role: Coder, next: [done]}"), "stages.doing.role"),
        (_replaced(MINIMAL, DOING, "  doing: {role: coder, next: [Done]}"), "stages.doing.next[0]"),
        (MINIMAL + "acceptance_stage: Acceptance\n", "acceptance_stage"),
    ],
    ids=["role", "next", "acceptance-stage"],
)
def test_a_name_value_that_breaks_the_pattern_is_refused(text: str, path: str) -> None:
    assert _fault(text).startswith(f"invalid {path}:")


@pytest.mark.parametrize(
    ("text", "path"),
    [
        (MINIMAL.partition("stages:\n")[0] + "stages: [tests, doing, done]\n", "stages"),
        (_replaced(MINIMAL, DOING, "  doing: {role: coder, next: review}"), "stages.doing.next"),
        (_replaced(MINIMAL, CODER, "  coder: {write_paths: 'src/*'}"), "roles.coder.write_paths"),
        (_replaced(MINIMAL, "contract: '1.0'", "contract: 1.0"), "contract"),
    ],
    ids=["stages-list", "next-string", "write-paths-string", "contract-number"],
)
def test_a_value_of_the_wrong_type_is_refused_by_its_path(text: str, path: str) -> None:
    assert _fault(text).startswith(f"invalid {path}:")


def test_a_text_that_is_not_yaml_is_refused() -> None:
    assert _fault(MINIMAL + "x: [\n").startswith("not valid YAML:")


def test_a_repeated_key_is_refused_naming_it() -> None:
    fault = _fault(MINIMAL + "  doing: {}\n")

    assert fault.startswith("not valid YAML:")
    assert "doing" in fault


def test_a_python_tag_is_refused_as_a_pipeline_definition_fault() -> None:
    with pytest.raises(PipelineDefinitionInvalid):
        _parse(MINIMAL + "x: !!python/object/apply:os.getcwd []\n")


@pytest.mark.parametrize("text", ["- a\n- b\n", "just text\n", ""], ids=["list", "string", "empty"])
def test_a_text_that_is_not_a_mapping_is_refused(text: str) -> None:
    assert _fault(text) == "the pipeline definition must be a mapping"


def test_several_faults_are_refused_once_in_rank_order() -> None:
    text = _replaced(MINIMAL, "contract: '1.0'\n", "") + "x: 1\n"

    assert _fault(text) == "unknown key: x; missing key: contract"
