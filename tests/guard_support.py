"""The hook payload and the outside-the-checkout text of the guard's tests."""

import json


def hook_payload(file_path: str, tool: str = "Write") -> str:
    """Return the `PreToolUse` payload of a `tool` call that names `file_path`."""
    return json.dumps({"tool_name": tool, "tool_input": {"file_path": file_path}})


def outside(file_path: str) -> str:
    """Return the guard's refusal of `file_path` as a path outside the checkout."""
    return f"{file_path} is outside the checkout."
