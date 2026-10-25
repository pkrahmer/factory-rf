"""The preflight item `opencode` and the models the installed agents use."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.application.preflight import installed_models, opencode_item
from factory.domain.settings import InstanceSettings
from git_support import AGENT_FILE, write_agent


def _no_model(alias: str) -> str:
    return f"no model is set for {alias} in FACTORY_OPENCODE_MODELS"


def _settings(**fields: object) -> InstanceSettings:
    return InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "agent_runtime": "opencode",
            "opencode_models": {"opus": "anthropic/claude-opus-5-5"},
            **fields,
        }
    )


@pytest.mark.parametrize(
    ("models", "detail"),
    [
        pytest.param(["opus", "anthropic/claude-haiku-5-5"], None, id="ready"),
        pytest.param(["opus", "sonnet"], _no_model("sonnet"), id="unmapped"),
        pytest.param(
            ["sonnet", "haiku", "sonnet"],
            f"{_no_model('haiku')}; {_no_model('sonnet')}",
            id="unmapped-sorted-once",
        ),
    ],
)
def test_the_opencode_item_names_a_missing_executable_and_each_unmapped_alias(
    models: list[str], detail: str | None
) -> None:
    item = opencode_item(_settings(), models)

    assert item.name == "opencode"
    assert item.passed == (detail is None)
    assert item.detail == ("" if detail is None else detail)


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(None, id="unset"),
        pytest.param("missing", id="no-file"),
        pytest.param("", id="empty"),
        pytest.param("stand-in-api-login\n", id="key"),
    ],
)
def test_the_opencode_item_does_not_depend_on_the_api_login_file(
    tmp_path: Path, content: str | None
) -> None:
    api_login_file = None if content is None else tmp_path / "api-login"
    if api_login_file is not None and content is not None and content != "missing":
        api_login_file.write_text(content, encoding="utf-8")
    models = ["opus", "sonnet"]

    item = opencode_item(_settings(api_login_file=api_login_file), models)

    assert item == opencode_item(_settings(), models)


def _write_three_agents(home: Path) -> None:
    for role, model in (("tester", "sonnet"), ("coder", "sonnet"), ("intake", "opus")):
        write_agent(home, role, AGENT_FILE.replace("model: sonnet", f"model: {model}"))


def _write_an_unreadable_agent(home: Path) -> None:
    write_agent(home, "coder", AGENT_FILE)
    (home / "agents" / "intake.md").write_bytes(b"\xff\xfe")


@pytest.mark.parametrize(
    ("prepare", "models"),
    [
        pytest.param(_write_three_agents, ["sonnet", "opus"], id="each-once-in-name-order"),
        pytest.param(lambda _: None, [], id="no-agents-folder"),
        pytest.param(_write_an_unreadable_agent, [], id="unreadable-agent-file"),
    ],
)
def test_the_installed_models_are_each_agent_s_model_once_or_none_when_unreadable(
    boundaries: Boundaries,
    agent_home: Path,
    prepare: Callable[[Path], object],
    models: list[str],
) -> None:
    prepare(agent_home)

    assert installed_models(boundaries) == models
