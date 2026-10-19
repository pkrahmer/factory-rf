"""The committed schema of the pipeline definition carries a project command's `not_read`."""

import json
from pathlib import Path

import factory
from factory.domain.contract import RECORDS_CONTRACT

SCHEMA = Path(factory.__file__).parent / "contract" / "pipeline-definition.schema.json"


def test_the_committed_pipeline_schema_holds_an_optional_not_read() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    command = schema["$defs"]["ProjectCommandDefinition"]

    assert "not_read" in command["properties"]
    assert "not_read" not in command.get("required", [])
    assert schema["x-records-contract"] == RECORDS_CONTRACT
