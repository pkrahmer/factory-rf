"""The records contract at version 1.1: the cost record's optional login."""

import json
from pathlib import Path

from factory.domain.contract import CONTRACT, RECORDS_CONTRACT, schema_file_name

SCHEMAS = Path(__file__).parent.parent.parent / "src" / "factory" / "contract"


def _committed(name: str) -> dict[str, object]:
    parsed: dict[str, object] = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    return parsed


def _values(schema: object) -> set[object]:
    assert isinstance(schema, dict)
    if "anyOf" in schema:
        return {value for option in schema["anyOf"] for value in _values(option)}
    if "enum" in schema:
        return set(schema["enum"])
    if "const" in schema:
        return {schema["const"]}
    assert schema.get("type") == "null"
    return {None}


def test_the_committed_cost_record_schema_lists_the_optional_login_at_version_1_1() -> None:
    schema = _committed("cost-record.schema.json")
    properties = schema["properties"]
    required = schema.get("required", [])
    assert isinstance(properties, dict)
    assert isinstance(required, list)

    assert RECORDS_CONTRACT == "1.1"
    assert "login" in properties
    assert "login" not in required
    assert _values(properties["login"]) == {"api_key", "subscription", "none", None}
    assert [_committed(schema_file_name(entry))["x-records-contract"] for entry in CONTRACT] == [
        "1.1"
    ] * 5
