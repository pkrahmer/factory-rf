"""The stand-in login and the replies of a `claude -p` stand-in, shared by the runtime's tests."""

import json

LOGIN = "stand-in-login"


REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.1,
        "duration_ms": 100,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
)


BUDGET_STOP = json.dumps(
    {
        "type": "result",
        "subtype": "error_max_budget_usd",
        "is_error": True,
        "num_turns": 3,
        "total_cost_usd": 1.0,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
    }
)
