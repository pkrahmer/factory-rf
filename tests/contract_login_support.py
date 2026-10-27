"""The committed contract values of the contract's login tests."""

import json
from pathlib import Path

SCHEMAS = Path(__file__).parent.parent / "src" / "factory" / "contract"


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
