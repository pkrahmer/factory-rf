"""The records contract at version 1.1: the cost record's optional login."""

from contract_login_support import _committed, _values


def test_the_committed_cost_record_schema_lists_the_optional_login() -> None:
    schema = _committed("cost-record.schema.json")
    properties = schema["properties"]
    required = schema.get("required", [])
    assert isinstance(properties, dict)
    assert isinstance(required, list)

    assert "login" in properties
    assert "login" not in required
    assert _values(properties["login"]) == {"api_key", "subscription", "none", None}
