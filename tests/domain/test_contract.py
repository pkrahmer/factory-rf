"""The records contract: its entries and the text of each entry's JSON Schema."""

import json

import pytest

from factory.domain.acceptance import AcceptanceState
from factory.domain.contract import (
    CONTRACT,
    ContractEntry,
    contract_schema,
    schema_file_name,
)
from factory.domain.cost_records import CostRecord
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.stops import StopRecord
from factory.domain.work_item import WorkItemState


def _entry(name: str) -> ContractEntry:
    return next(entry for entry in CONTRACT if entry.name == name)


def _schema(name: str) -> dict[str, object]:
    parsed: dict[str, object] = json.loads(contract_schema(_entry(name)))
    return parsed


def test_the_contract_holds_the_five_records_in_order() -> None:
    names = [entry.name for entry in CONTRACT]

    assert [(entry.name, entry.model, entry.mode) for entry in CONTRACT] == [
        ("work-item-state", WorkItemState, "serialization"),
        ("acceptance-state", AcceptanceState, "serialization"),
        ("cost-record", CostRecord, "serialization"),
        ("stop-record", StopRecord, "serialization"),
        ("pipeline-definition", PipelineDefinition, "validation"),
    ]
    assert len(set(names)) == len(names)
    assert schema_file_name(CONTRACT[0]) == "work-item-state.schema.json"


@pytest.mark.parametrize("entry", CONTRACT, ids=[entry.name for entry in CONTRACT])
def test_a_schema_starts_with_the_dialect_and_the_contract_version(
    entry: ContractEntry,
) -> None:
    text = contract_schema(entry)
    parsed: dict[str, object] = json.loads(text)
    keys = list(parsed)
    rest = {key: parsed[key] for key in keys[2:]}

    assert keys[:2] == ["$schema", "x-records-contract"]
    assert parsed["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert parsed["x-records-contract"] == "4.0"
    assert rest == entry.model.model_json_schema(mode=entry.mode)
    assert text.endswith("}\n")


def test_the_journal_record_carries_its_optional_causes() -> None:
    definitions = _schema("work-item-state")["$defs"]
    assert isinstance(definitions, dict)
    journal_record = definitions["JournalRecord"]
    properties = journal_record["properties"]
    required = journal_record.get("required", [])

    for name in ("blocked", "reason"):
        assert name in properties
        assert name not in required


def test_the_cost_record_carries_its_optional_denials() -> None:
    schema = _schema("cost-record")
    properties = schema["properties"]
    required = schema.get("required", [])
    assert isinstance(properties, dict)
    assert isinstance(required, list)

    for name in ("denials", "denied_paths"):
        assert name in properties
        assert name not in required


@pytest.mark.parametrize("field", ["event", "scope", "reason", "at"])
def test_the_stop_record_requires_its_fields(field: str) -> None:
    required = _schema("stop-record")["required"]
    assert isinstance(required, list)

    assert field in required
