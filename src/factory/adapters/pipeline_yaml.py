"""The pipeline definition read from its YAML file with ruamel.yaml."""

from typing import override

from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import MarkedYAMLError, YAMLError

from factory.adapters.validation_faults import all_faults
from factory.application.files import PipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
from factory.domain.pipeline_definition import PipelineDefinition

_FAULT_SEPARATOR = "; "


class RuamelPipelineDefinitionReader(PipelineDefinitionReader):
    """Reads the pipeline definition with ruamel.yaml's safe loader and validates it."""

    def __init__(self) -> None:
        """Prepare a safe loader, which builds plain data and refuses a repeated key."""
        self._loader = YAML(typ="safe")

    @override
    def parse(self, text: str) -> PipelineDefinition:
        """The definition of a text, its left-out keys at their defaults and all faults named."""
        try:
            loaded: object = self._loader.load(text)
        except YAMLError as error:
            raise PipelineDefinitionInvalid(yaml_fault(error)) from error
        if not isinstance(loaded, dict):
            raise PipelineDefinitionInvalid("the pipeline definition must be a mapping")
        try:
            return PipelineDefinition.model_validate(loaded)
        except ValidationError as error:
            raise PipelineDefinitionInvalid(_fault_of(error)) from error


def yaml_fault(error: YAMLError) -> str:
    """The one-line fault of ruamel.yaml's `error`: its problem and 1-based position."""
    # The context lines and ruamel's hint to suppress the duplicate-key check stay out:
    # the fault is one line of the factory log, and the factory wants that check.
    if isinstance(error, MarkedYAMLError) and error.problem:
        mark = error.problem_mark
        if mark is None:
            return f"not valid YAML: {error.problem}"
        return f"not valid YAML: {error.problem} (line {mark.line + 1}, column {mark.column + 1})"
    return f"not valid YAML: {_first_line(str(error))}"


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def _fault_of(error: ValidationError) -> str:
    details = error.errors()
    # The rules across keys run only once every field is valid, so their error comes alone.
    if len(details) == 1 and not details[0]["loc"] and "error" in details[0].get("ctx", {}):
        return str(details[0]["ctx"]["error"])
    return _FAULT_SEPARATOR.join(all_faults(error, "pipeline definition"))
