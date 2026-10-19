"""The image installs opencode at a pinned version and the compose file lets the operator choose."""

import re
from pathlib import Path

from ruamel.yaml import YAML

from dockerfile_support import dockerfile_instructions

COMPOSE = Path(__file__).parent.parent / "image" / "compose.yml"
MODELS = (
    "opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,"
    "haiku=anthropic/claude-haiku-5-5"
)


def test_the_image_installs_opencode_at_its_pin_and_sets_its_version_and_models() -> None:
    instructions = dockerfile_instructions()
    pins = [line for line in instructions if line.startswith("ARG OPENCODE_VERSION=")]
    installs = [index for index, line in enumerate(instructions) if "npm install" in line]
    opencode = [
        index for index in installs if "opencode-ai@${OPENCODE_VERSION}" in instructions[index]
    ]
    claude = [index for index in installs if "@anthropic-ai/claude-code" in instructions[index]]
    user = instructions.index("USER factory")

    assert pins == ["ARG OPENCODE_VERSION=1.19.3"]
    assert re.fullmatch(r"ARG OPENCODE_VERSION=\d+\.\d+\.\d+", pins[0])
    assert len(opencode) == 1
    assert len(claude) == 1
    assert opencode[0] > claude[0]
    version = instructions.index("ENV FACTORY_OPENCODE_VERSION=${OPENCODE_VERSION}")
    models = instructions.index(f"ENV FACTORY_OPENCODE_MODELS={MODELS}")
    assert version < user
    assert models < user


def test_the_compose_service_passes_the_runtime_and_opencode_build_with_the_image_s_defaults() -> (
    None
):
    environment = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))["services"]["factory"][
        "environment"
    ]
    names = list(environment)
    after = names[names.index("FACTORY_INSTANCE") + 1 : names.index("FACTORY_INSTANCE") + 6]
    pin = next(
        line for line in dockerfile_instructions() if line.startswith("ARG OPENCODE_VERSION=")
    )
    image_models = next(
        line
        for line in dockerfile_instructions()
        if line.startswith("ENV FACTORY_OPENCODE_MODELS=")
    )

    assert after == [
        "FACTORY_AGENT_RUNTIME",
        "FACTORY_OPENCODE",
        "FACTORY_OPENCODE_VERSION",
        "FACTORY_OPENCODE_MODELS",
        "FACTORY_OPENCODE_FOLDERS",
    ]
    assert environment["FACTORY_AGENT_RUNTIME"] == "${FACTORY_AGENT_RUNTIME:-claude}"
    assert environment["FACTORY_OPENCODE"] == "${FACTORY_OPENCODE:-opencode}"
    assert environment["FACTORY_OPENCODE_VERSION"] == (
        f"${{FACTORY_OPENCODE_VERSION:-{pin.removeprefix('ARG OPENCODE_VERSION=')}}}"
    )
    assert environment["FACTORY_OPENCODE_MODELS"] == (
        f"${{FACTORY_OPENCODE_MODELS:-{image_models.removeprefix('ENV FACTORY_OPENCODE_MODELS=')}}}"
    )
    assert environment["FACTORY_OPENCODE_FOLDERS"] == "${FACTORY_OPENCODE_FOLDERS:-}"
