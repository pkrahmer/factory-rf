"""The stand-in login and the budget stop of a `claude -p` stand-in, for the runtime's tests."""

import json

LOGIN = "stand-in-login"


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
