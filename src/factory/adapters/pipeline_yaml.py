"""The pipeline definition read from its YAML file with ruamel.yaml."""

from typing import override

from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

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
            raise PipelineDefinitionInvalid(f"not valid YAML: {error}") from error
        if not isinstance(loaded, dict):
            raise PipelineDefinitionInvalid("the pipeline definition must be a mapping")
        try:
            return PipelineDefinition.model_validate(loaded)
        except ValidationError as error:
            faults = all_faults(error, "pipeline definition")
            raise PipelineDefinitionInvalid(_FAULT_SEPARATOR.join(faults)) from error
