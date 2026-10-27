"""The committed contract values of the contract's login tests."""

import json

from contract_support import SCHEMAS


def committed(name: str) -> dict[str, object]:
    """The parsed committed schema file `name`."""
    parsed: dict[str, object] = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    return parsed


def values(schema: object) -> set[object]:
    """The values a schema allows: its enum, its const, or None for null, through its anyOf."""
    assert isinstance(schema, dict)
    if "anyOf" in schema:
        return {value for option in schema["anyOf"] for value in values(option)}
    if "enum" in schema:
        return set(schema["enum"])
    if "const" in schema:
        return {schema["const"]}
    assert schema.get("type") == "null"
    return {None}
