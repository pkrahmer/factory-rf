"""The pins outside any image: the reader of floating references, the lockfile and the build."""

import importlib.metadata
import re
import tomllib
from pathlib import Path

import pytest

from dockerfile_support import floating_references

ROOT = Path(__file__).parent.parent
PYPROJECT = ROOT / "pyproject.toml"
LOCKFILE = ROOT / "uv.lock"
TEMPLATE = ROOT / "template"
PRODUCTION_DEPENDENCIES = ["pydantic", "PyGithub", "ruamel.yaml", "python-frontmatter"]


@pytest.mark.parametrize(
    "line",
    [
        "FROM python:3.12-slim-bookworm",
        "FROM python",
        "FROM python:latest",
        "ARG CLAUDE_CODE_VERSION=latest",
        "ARG CLAUDE_CODE_VERSION=2.1",
        "apt-get install -y git",
        "apt-get install -y git=*",
        "apt-get upgrade -y",
        "pip install uv",
        "pip install uv>=0.9",
        "npm install --global @anthropic-ai/claude-code",
        "npm install --global @anthropic-ai/claude-code@latest",
        "npm install --global @anthropic-ai/claude-code@2.1",
        "npx claude-code",
        "RUN curl -fsSL https://example.invalid/install.sh | bash",
        "RUN wget -qO- https://example.invalid/install.sh | sh",
        "uv tool install /opt/factory",
        "uv sync",
        "apt-get dist-upgrade -y",
        "npm i -g @anthropic-ai/claude-code",
        "pip install .",
        "ARG CLAUDE_CODE_VERSION=stable",
        "ARG CLAUDE_CODE_VERSION=",
        "RUN echo latest",
        "FROM python@sha256:" + "a" * 63,
        "FROM python@sha256:" + "a" * 65,
        "FROM python@sha256:" + "g" * 64,
        "ARG CLAUDE_CODE_VERSION=2.1.289.1",
        "npm install --global @anthropic-ai/claude-code@2.1.289.1",
    ],
)
def test_a_floating_item_is_reported(line: str) -> None:
    assert floating_references(line + "\n") != []


@pytest.mark.parametrize(
    "line",
    [
        "FROM python:3.12-slim-bookworm@sha256:" + "a" * 64,
        "ARG CLAUDE_CODE_VERSION=2.1.289",
        "apt-get install -y git=1:2.39.5-0+deb12u2",
        "pip install uv==0.9.2",
        "npm install --global @anthropic-ai/claude-code@2.1.289",
        "uv sync --frozen --no-dev",
        "uv sync --locked --no-dev",
        "RUN curl -fsSL https://example.invalid/file -o /opt/file",
        "# latest",
    ],
)
def test_a_pinned_item_is_not_reported(line: str) -> None:
    assert floating_references(line + "\n") == []


def _pins() -> dict[str, str]:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    pins = [requirement.partition("==") for requirement in project["dependencies"]]
    return {name: version for name, _, version in pins}


def _locked() -> dict[str, str]:
    lock = tomllib.loads(LOCKFILE.read_text(encoding="utf-8"))
    return {package["name"]: package["version"] for package in lock["package"]}


@pytest.mark.parametrize("name", PRODUCTION_DEPENDENCIES)
def test_installed_versions_equal_the_locked_and_pinned_ones(name: str) -> None:
    locked = _locked()[re.sub(r"[-_.]+", "-", name).lower()]

    assert importlib.metadata.version(name) == locked
    assert _pins()[name] == locked


def test_the_template_has_no_placeholder_files_and_no_tasks_directory() -> None:
    found = list(TEMPLATE.rglob(".gitkeep")) + [
        path for path in TEMPLATE.rglob("tasks") if path.is_dir()
    ]

    assert found == []


def test_the_build_backend_is_pinned() -> None:
    requires = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["build-system"]["requires"]

    assert requires != []
    assert all(re.match(r"^[A-Za-z0-9._-]+==\S+$", requirement) for requirement in requires)
