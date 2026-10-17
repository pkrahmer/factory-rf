"""The preflight item `agent-environment`: the agent run finds `factory-guard` and its home."""

from pathlib import Path

import pytest

from factory.application.preflight import agent_environment_item

GUARD_DIRECTORY = "/opt/factory/bin"
COMMANDS = {GUARD_DIRECTORY: {"factory-guard"}, "/usr/bin": {"env", "sudo"}}


def _find(name: str, path: str) -> str | None:
    for directory in path.split(":"):
        if name in COMMANDS.get(directory, set()):
            return f"{directory}/{name}"
    return None


def test_a_path_holding_factory_guard_and_an_existing_home_pass(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    environment = {"PATH": f"/usr/bin:{GUARD_DIRECTORY}", "HOME": str(home)}

    item = agent_environment_item(environment, _find, Path.is_dir)

    assert item.name == "agent-environment"
    assert item.passed


@pytest.mark.parametrize(
    ("path", "home", "detail"),
    [
        pytest.param(
            "/usr/bin",
            "home",
            "factory-guard is not on the agent run's PATH /usr/bin",
            id="path-without-factory-guard",
        ),
        pytest.param(None, "home", "the agent run has no PATH", id="no-path"),
        pytest.param(GUARD_DIRECTORY, None, "the agent run has no HOME", id="no-home"),
        pytest.param(
            GUARD_DIRECTORY,
            "file",
            "the agent run's HOME {file} is no directory",
            id="home-not-a-directory",
        ),
        pytest.param(
            None,
            None,
            "the agent run has no PATH; the agent run has no HOME",
            id="neither-path-nor-home",
        ),
    ],
)
def test_a_fault_in_the_environment_fails_with_its_detail(
    tmp_path: Path, *, path: str | None, home: str | None, detail: str
) -> None:
    (tmp_path / "home").mkdir()
    (tmp_path / "file").write_text("not a directory\n", encoding="utf-8")
    environment: dict[str, str] = {}
    if path is not None:
        environment["PATH"] = path
    if home is not None:
        environment["HOME"] = str(tmp_path / home)

    item = agent_environment_item(environment, _find, Path.is_dir)

    assert item.name == "agent-environment"
    assert not item.passed
    assert item.detail == detail.format(file=tmp_path / "file")
