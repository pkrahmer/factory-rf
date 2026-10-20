"""The preflight item `agent-environment`: the agent run finds its login in `HOME`."""

from pathlib import Path

import pytest

from factory.application.preflight import agent_environment_item


@pytest.mark.parametrize(
    ("path", "home", "detail"),
    [
        pytest.param("/usr/bin", "home", None, id="path-and-home"),
        pytest.param(None, "home", None, id="home-without-path"),
        pytest.param("/opt/factory/bin", "home", None, id="factory-path-and-home"),
        pytest.param("/usr/bin", None, "the agent run has no HOME", id="no-home"),
        pytest.param(
            "/usr/bin",
            "file",
            "the agent run's HOME {file} is no directory",
            id="home-not-a-directory",
        ),
    ],
)
def test_the_agent_environment_checks_the_home_only(
    tmp_path: Path, *, path: str | None, home: str | None, detail: str | None
) -> None:
    (tmp_path / "home").mkdir()
    (tmp_path / "file").write_text("not a directory\n", encoding="utf-8")
    environment: dict[str, str] = {}
    if path is not None:
        environment["PATH"] = path
    if home is not None:
        environment["HOME"] = str(tmp_path / home)

    item = agent_environment_item(environment, Path.is_dir)

    assert item.name == "agent-environment"
    if detail is None:
        assert item.passed
    else:
        assert not item.passed
        assert item.detail == detail.format(file=tmp_path / "file")
