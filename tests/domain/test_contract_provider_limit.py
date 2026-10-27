"""The records contract names `provider_limit` as an end reason and as a stall reason."""

from contract_login_support import _committed, _values


def _reason_values(schema_name: str) -> set[object]:
    schema = _committed(schema_name)
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    record = definitions["JournalRecord"]
    assert isinstance(record, dict)
    return _values(record["properties"]["reason"])


def test_the_committed_schemas_list_provider_limit() -> None:
    cost_properties = _committed("cost-record.schema.json")["properties"]
    assert isinstance(cost_properties, dict)

    assert "provider_limit" in _values(cost_properties["end_reason"])
    assert "provider_limit" in _reason_values("work-item-state.schema.json")
    assert "provider_limit" in _reason_values("acceptance-state.schema.json")
