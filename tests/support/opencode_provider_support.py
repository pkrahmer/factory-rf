"""A complete opencode provider file and the configuration it gives, shared by its tests."""

import json
from pathlib import Path

KEY_ENV = "PROXY_KEY"
PROVIDER: dict[str, object] = {
    "id": "corp",
    "base_url": "https://example.invalid/v1",
    "api_key_env": KEY_ENV,
    "models": {
        "m": {
            "name": "M",
            "context": 1000,
            "output": 100,
            "input_cost": 3.0,
            "output_cost": 15.0,
        }
    },
    "small_model": "corp/m",
}
CONFIGURATION: dict[str, object] = {
    "provider": {
        "corp": {
            "npm": "@ai-sdk/openai-compatible",
            "options": {"baseURL": "https://example.invalid/v1", "apiKey": "{env:PROXY_KEY}"},
            "models": {
                "m": {
                    "name": "M",
                    "limit": {"context": 1000, "output": 100},
                    "cost": {"input": 3.0, "output": 15.0},
                }
            },
        }
    },
    "small_model": "corp/m",
}


def write_provider(folder: Path, text: str | None = None) -> Path:
    """Write `text`, the complete provider file when `None`, as `provider.json` in `folder`."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "provider.json"
    path.write_text(json.dumps(PROVIDER) if text is None else text, encoding="utf-8")
    return path
