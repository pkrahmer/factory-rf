"""The records contract at version 1.2: the end reason and the stall reason `provider_limit`."""

from domain.test_contract_login import _committed, _values
from factory.domain.contract import CONTRACT, RECORDS_CONTRACT, schema_file_name


def _reason_values(schema_name: str) -> set[object]:
    schema = _committed(schema_name)
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    record = definitions["JournalRecord"]
    assert isinstance(record, dict)
    return _values(record["properties"]["reason"])


def test_the_committed_schemas_list_provider_limit_at_version_1_2() -> None:
    cost_properties = _committed("cost-record.schema.json")["properties"]
    assert isinstance(cost_properties, dict)

    assert RECORDS_CONTRACT == "4.0"
    assert "provider_limit" in _values(cost_properties["end_reason"])
    assert "provider_limit" in _reason_values("work-item-state.schema.json")
    assert "provider_limit" in _reason_values("acceptance-state.schema.json")
    assert [_committed(schema_file_name(entry))["x-records-contract"] for entry in CONTRACT] == [
        "4.0"
    ] * 5
