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
    ("path", "home", "named"),
    [
        pytest.param("/usr/bin", "home", "factory-guard", id="path-without-factory-guard"),
        pytest.param(None, "home", "PATH", id="no-path"),
        pytest.param(GUARD_DIRECTORY, None, "HOME", id="no-home"),
        pytest.param(GUARD_DIRECTORY, "file", "HOME", id="home-not-a-directory"),
    ],
)
def test_a_fault_in_the_environment_fails_naming_it(
    tmp_path: Path, *, path: str | None, home: str | None, named: str
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
    assert named in item.detail
