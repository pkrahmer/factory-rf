"""The preflight item `opencode` and the models the installed agents use."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.application.preflight import installed_models, opencode_item
from factory.domain.settings import InstanceSettings
from git_support import AGENT_FILE, write_agent

PATH = "/opt/factory/bin:/usr/bin"
ENVIRONMENT = {"PATH": PATH, "HOME": "/home/agent"}
NOT_ON_PATH = f"opencode is not on the agent run's PATH {PATH}"
NO_PATH = "the agent run has no PATH"


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


def _find_on(found: bool) -> Callable[[str, str], str | None]:
    def find(name: str, path: str) -> str | None:
        return f"/usr/bin/{name}" if found and name == "opencode" and path else None

    return find


@pytest.mark.parametrize(
    ("environment", "found", "models", "detail"),
    [
        pytest.param(ENVIRONMENT, True, ["opus", "anthropic/claude-haiku-5-5"], None, id="ready"),
        pytest.param(ENVIRONMENT, False, ["opus"], NOT_ON_PATH, id="not-on-path"),
        pytest.param({"HOME": "/home/agent"}, True, ["opus"], NO_PATH, id="no-path"),
        pytest.param(ENVIRONMENT, True, ["opus", "sonnet"], _no_model("sonnet"), id="unmapped"),
        pytest.param(
            ENVIRONMENT,
            True,
            ["sonnet", "haiku", "sonnet"],
            f"{_no_model('haiku')}; {_no_model('sonnet')}",
            id="unmapped-sorted-once",
        ),
        pytest.param(
            ENVIRONMENT,
            False,
            ["sonnet"],
            f"{NOT_ON_PATH}; {_no_model('sonnet')}",
            id="path-and-model",
        ),
    ],
)
def test_the_opencode_item_names_a_missing_executable_and_each_unmapped_alias(
    environment: dict[str, str], *, found: bool, models: list[str], detail: str | None
) -> None:
    item = opencode_item(_settings(), environment, _find_on(found), models)

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
@pytest.mark.parametrize("found", [True, False], ids=["on-path", "not-on-path"])
def test_the_opencode_item_does_not_depend_on_the_api_login_file(
    tmp_path: Path, *, content: str | None, found: bool
) -> None:
    api_login_file = None if content is None else tmp_path / "api-login"
    if api_login_file is not None and content is not None and content != "missing":
        api_login_file.write_text(content, encoding="utf-8")
    models = ["opus", "sonnet"]

    item = opencode_item(
        _settings(api_login_file=api_login_file), ENVIRONMENT, _find_on(found), models
    )

    assert item == opencode_item(_settings(), ENVIRONMENT, _find_on(found), models)


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
