"""The wiring hands the instance's provider limit to the Claude Code runtime."""

import json
from pathlib import Path

from adapters.claude_stand_in import claude_request
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.provider_limits import ProviderLimit
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from podman_support import PodmanPlan
from wiring_support import CREDENTIAL, dataset_podman, with_dataset

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
    root = tmp_path.resolve()
    settings = with_dataset(
        InstanceSettings(
            repository_url="/srv/project.git",
            instance="factory-1",
            checkout=root / "checkout",
            state_directory=root / "state",
            agent_home=root / "agents-home",
            provider_limit=ProviderLimit(status=429),
        ),
        tmp_path,
    )
    dataset_podman(tmp_path, PodmanPlan(stdout=ERROR_REPLY))
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    result = boundaries.agent_runtime.run(claude_request(tmp_path))

    assert result.end_reason == "provider_limit"
