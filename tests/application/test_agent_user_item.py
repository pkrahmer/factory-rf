"""The preflight item `agent-user`: no agent may run as the factory's user beside a token file."""

from pathlib import Path

import pytest

from factory.application.preflight import agent_user_item
from factory.domain.settings import InstanceSettings

TOKEN_FILE = Path("/run/secrets/hosting-token")
MISSING_DETAIL = (
    "FACTORY_AGENT_USER is not set: every agent would run as the factory's user, "
    "who can read the token file"
)


@pytest.mark.parametrize(
    ("agent_user", "token_file", "exists", "passed", "detail"),
    [
        (None, TOKEN_FILE, True, False, MISSING_DETAIL),
        ("agent", TOKEN_FILE, True, True, ""),
        ("agent", TOKEN_FILE, False, True, ""),
        ("agent", None, False, True, ""),
        (None, None, False, True, ""),
        (None, None, True, True, ""),
        (None, TOKEN_FILE, False, True, ""),
    ],
    ids=[
        "no-agent-user-token-file-exists",
        "agent-user-token-file-exists",
        "agent-user-token-file-missing",
        "agent-user-no-token-file",
        "no-agent-user-no-token-file",
        "no-agent-user-no-token-file-exists-says-yes",
        "no-agent-user-token-file-missing",
    ],
)
def test_the_item_fails_only_without_an_agent_user_beside_an_existing_token_file(
    *, agent_user: str | None, token_file: Path | None, exists: bool, passed: bool, detail: str
) -> None:
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        token_file=token_file,
        agent_user=agent_user,
    )
    asked: list[Path] = []

    def answer(path: Path) -> bool:
        asked.append(path)
        return exists

    item = agent_user_item(settings, answer)

    assert item.name == "agent-user"
    assert item.passed is passed
    assert item.detail == detail
    assert all(path == TOKEN_FILE for path in asked)
