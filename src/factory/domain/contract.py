"""The records contract: the records readers outside the factory may rely on, and their schemas."""

import json
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from factory.domain.acceptance import AcceptanceState
from factory.domain.cost_records import CostRecord
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.stops import StopRecord
from factory.domain.work_item import WorkItemState

RECORDS_CONTRACT = "4.0"
CONTRACT_KEY = "x-records-contract"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

SchemaMode = Literal["validation", "serialization"]

_SCHEMA_SUFFIX = ".schema.json"


# A dataclass, not a Pydantic model: it holds a class, not data.
@dataclass(frozen=True)
class ContractEntry:
    """One record of the contract: its file's name, the model that validates it and the mode."""

    name: str
    model: type[BaseModel]
    mode: SchemaMode


# The records the factory writes are described as they are on disk; the pipeline
# definition, which the human writes and the factory reads, as it is accepted.
CONTRACT: tuple[ContractEntry, ...] = (
    ContractEntry("work-item-state", WorkItemState, "serialization"),
    ContractEntry("acceptance-state", AcceptanceState, "serialization"),
    ContractEntry("cost-record", CostRecord, "serialization"),
    ContractEntry("stop-record", StopRecord, "serialization"),
    ContractEntry("pipeline-definition", PipelineDefinition, "validation"),
)


def schema_file_name(entry: ContractEntry) -> str:
    """`<name>.schema.json`."""
    return f"{entry.name}{_SCHEMA_SUFFIX}"


def contract_schema(entry: ContractEntry) -> str:
    """The schema's text: `$schema`, the contract key and version, then the model's schema."""
    schema = {
        "$schema": JSON_SCHEMA_DIALECT,
        CONTRACT_KEY: RECORDS_CONTRACT,
        **entry.model.model_json_schema(mode=entry.mode),
    }
    return json.dumps(schema, indent=2) + "\n"
