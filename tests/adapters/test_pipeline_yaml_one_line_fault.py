"""A text that is not valid YAML is refused with ruamel's problem and position on one line."""

import pytest
from ruamel.yaml.error import FileMark, MarkedYAMLError, YAMLError

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader, yaml_fault
from factory.domain.errors import PipelineDefinitionInvalid
from git_support import PIPELINE_YAML

REPEATED_KEY = PIPELINE_YAML + "  done: {}\n"
UNCLOSED_LIST = PIPELINE_YAML + "x: [\n"
MAPPING_IN_A_VALUE = PIPELINE_YAML.replace("crash_cap: 2", "crash_cap: 2: 3")
PYTHON_TAG = PIPELINE_YAML + "x: !!python/object/apply:os.getcwd []\n"
CONTROL_CHARACTER = PIPELINE_YAML + 'x: "\x07"\n'
BLOCK_SCALAR_REPEATED_KEY = "a: 1\na: |\n  x\n  y\n"

REPEATED_KEY_FAULT = (
    'not valid YAML: found duplicate key "done" with value "{}" (original value: "{}")'
    " (line 27, column 3)"
)


def _fault(text: str) -> str:
    with pytest.raises(PipelineDefinitionInvalid) as caught:
        RuamelPipelineDefinitionReader().parse(text)
    return caught.value.fault


@pytest.mark.parametrize(
    ("text", "fault"),
    [
        (REPEATED_KEY, REPEATED_KEY_FAULT),
        (UNCLOSED_LIST, "not valid YAML: did not find expected node content (line 28, column 1)"),
        (
            MAPPING_IN_A_VALUE,
            "not valid YAML: mapping values are not allowed in this context (line 3, column 13)",
        ),
        (
            CONTROL_CHARACTER,
            "not valid YAML: unacceptable character #x0007: control characters are not allowed",
        ),
        (
            BLOCK_SCALAR_REPEATED_KEY,
            'not valid YAML: found duplicate key "a" with value "x\\ny\\n" (original value: "1")'
            " (line 2, column 1)",
        ),
    ],
    ids=[
        "repeated-key",
        "unclosed-list",
        "mapping-in-a-value",
        "control-character",
        "block-scalar-repeated-key",
    ],
)
def test_a_yaml_error_is_refused_with_its_problem_and_position(text: str, fault: str) -> None:
    assert _fault(text) == fault


def test_a_python_tag_is_refused_with_its_problem_and_position() -> None:
    fault = _fault(PYTHON_TAG)

    assert fault.startswith("not valid YAML: could not determine a constructor for the tag")
    assert fault.endswith("(line 27, column 4)")


@pytest.mark.parametrize(
    "text",
    [
        REPEATED_KEY,
        UNCLOSED_LIST,
        MAPPING_IN_A_VALUE,
        PYTHON_TAG,
        CONTROL_CHARACTER,
        BLOCK_SCALAR_REPEATED_KEY,
    ],
    ids=[
        "repeated-key",
        "unclosed-list",
        "mapping-in-a-value",
        "python-tag",
        "control-character",
        "block-scalar-repeated-key",
    ],
)
def test_a_yaml_fault_holds_no_line_break(text: str) -> None:
    fault = _fault(text)

    assert "\n" not in fault
    assert "\r" not in fault


def test_a_repeated_key_fault_holds_no_hint_and_no_context() -> None:
    fault = _fault(REPEATED_KEY)

    assert "To suppress" not in fault
    assert "<unicode string>" not in fault


def test_the_example_definition_still_parses() -> None:
    RuamelPipelineDefinitionReader().parse(PIPELINE_YAML)


def test_a_yaml_text_that_is_not_a_mapping_is_still_refused_as_such() -> None:
    assert _fault("- a\n") == "the pipeline definition must be a mapping"


@pytest.mark.parametrize(
    ("error", "fault"),
    [
        (MarkedYAMLError(context="while x", problem="found y"), "not valid YAML: found y"),
        (
            MarkedYAMLError(context="while x", problem="", problem_mark=FileMark("<s>", 0, 4, 2)),
            "not valid YAML: while x",
        ),
        (YAMLError("plain\nsecond"), "not valid YAML: plain"),
    ],
    ids=["problem-without-mark", "empty-problem", "plain-error"],
)
def test_yaml_fault_falls_back_to_the_first_line_of_the_text(error: YAMLError, fault: str) -> None:
    assert yaml_fault(error) == fault
