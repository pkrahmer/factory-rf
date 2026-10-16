"""The image and its compose file: the token arrives as a mounted secret, never as a setting."""

import re
from pathlib import Path

import pytest
from ruamel.yaml import YAML

ROOT = Path(__file__).parent.parent
DOCKERFILE = ROOT / "image" / "Dockerfile"
COMPOSE = ROOT / "image" / "compose.yml"
SECRET_WORDS = ("TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")
HELPER_COPY = "COPY image/git-credential-factory /usr/local/bin/git-credential-factory"
FILE_SETTING = "ENV FACTORY_TOKEN_FILE=/run/secrets/hosting-token"


def _instructions() -> list[str]:
    """Every instruction of the Dockerfile on one line, continuations joined, comments dropped."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    joined = re.sub(r"\\\n", " ", "\n".join(lines))
    return [" ".join(line.split()) for line in joined.splitlines() if line.strip()]


def _declared_names(instructions: list[str]) -> list[str]:
    """The names every `ENV` and `ARG` instruction declares."""
    names: list[str] = []
    for instruction in instructions:
        keyword, _, arguments = instruction.partition(" ")
        if keyword.upper() in {"ENV", "ARG"}:
            names.extend(word.partition("=")[0] for word in arguments.split() if "=" in word)
            if "=" not in arguments:
                names.append(arguments.split()[0])
    return names


@pytest.fixture
def compose() -> dict[str, object]:
    """Return the compose file as data."""
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def test_the_dockerfile_installs_the_helper_and_sets_nothing_secret() -> None:
    instructions = _instructions()
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


def test_the_compose_file_mounts_the_token_as_a_secret_and_sets_nothing_secret(
    compose: dict[str, object],
) -> None:
    services = compose["services"]
    assert isinstance(services, dict)
    service = services["factory"]
    assert isinstance(service, dict)
    environment = service.get("environment", {})
    assert isinstance(environment, dict)

    assert compose["secrets"] == {"hosting_token": {"file": "./secrets/hosting-token"}}
    assert service["secrets"] == [
        {
            "source": "hosting_token",
            "target": "hosting-token",
            "uid": "1000",
            "gid": "1002",
            "mode": 400,
        }
    ]
    secret_names = [
        name for name in environment if any(word in name.upper() for word in SECRET_WORDS)
    ]
    assert secret_names == []
    assert "env_file" not in service
