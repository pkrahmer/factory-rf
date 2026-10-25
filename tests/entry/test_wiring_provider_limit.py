"""The wiring hands the instance's provider limit to the Claude Code runtime."""

import json
from pathlib import Path

from adapters.claude_stand_in import Step, claude_request, write_stand_in
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.provider_limits import ProviderLimit
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from wiring_support import CREDENTIAL

ERROR_REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": True,
        "num_turns": 1,
        "total_cost_usd": 0.01,
        "result": "API Error: 429 spend limit reached",
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
    }
)


def test_the_built_runtime_recognizes_the_configured_limit_status(tmp_path: Path) -> None:
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=ERROR_REPLY)])
    root = tmp_path.resolve()
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
        claude_executable=str(executable),
        provider_limit=ProviderLimit(status=429),
    )
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    result = boundaries.agent_runtime.run(claude_request(tmp_path))

    assert result.end_reason == "provider_limit"
