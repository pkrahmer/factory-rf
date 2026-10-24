"""The image and its compose file: the token arrives as a mounted file, never as a setting."""

from pathlib import Path

import pytest
from ruamel.yaml import YAML

from dockerfile_support import DOCKERFILE, SECRET_WORDS, _declared_names, dockerfile_instructions

ROOT = Path(__file__).parent.parent
COMPOSE = ROOT / "image" / "compose.yml"
HELPER_COPY = "COPY image/git-credential-factory /usr/local/bin/git-credential-factory"
FILE_SETTING = "ENV FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token"


@pytest.fixture
def compose() -> dict[str, object]:
    """Return the compose file as data."""
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def test_the_dockerfile_installs_the_helper_and_sets_nothing_secret() -> None:
    instructions = dockerfile_instructions()
    user = instructions.index("USER factory")
    text = DOCKERFILE.read_text(encoding="utf-8")

    assert instructions.index(HELPER_COPY) < user
    assert instructions.index(FILE_SETTING) < user
    secret_names = [
        name
        for name in _declared_names(instructions)
        if any(word in name.upper() for word in SECRET_WORDS)
    ]
    assert secret_names == ["FACTORY_TOKEN_FILE"]
    assert ".git-credentials" not in text
    assert "credential.helper" not in text


def test_the_compose_file_has_no_secret_and_sets_nothing_secret(
    compose: dict[str, object],
) -> None:
    services = compose["services"]
    assert isinstance(services, dict)
    service = services["factory"]
    assert isinstance(service, dict)
    environment = service.get("environment", {})
    assert isinstance(environment, dict)

    assert "secrets" not in compose
    assert "secrets" not in service
    secret_names = [
        name for name in environment if any(word in name.upper() for word in SECRET_WORDS)
    ]
    assert secret_names == []
    assert "env_file" not in service
