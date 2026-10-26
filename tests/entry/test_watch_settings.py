"""The watcher's command line reads the instance's settings from the environment."""

import io
from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.domain.errors import GitError
from factory.entry.watch import main
from stage_run_support import INSTANCE

HOSTED_URL = "https://github.com/owner/project.git"
REFUSAL = "factory-watch: settings invalid: "


@pytest.fixture
def valid_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set a valid environment, its token and image id files in `tmp_path`; return the token."""
    token = tmp_path / "hosting-token"
    token.write_text("example-value\n", encoding="utf-8")
    image = tmp_path / "image-id"
    image.write_text("build-7\n", encoding="utf-8")
    monkeypatch.setenv("FACTORY_REPOSITORY_URL", HOSTED_URL)
    monkeypatch.setenv("FACTORY_INSTANCE", INSTANCE)
    monkeypatch.setenv("FACTORY_TOKEN_FILE", str(token))
    monkeypatch.setenv("FACTORY_IMAGE_ID_FILE", str(image))
    monkeypatch.setenv("FACTORY_CLAUDE_HOME", str(tmp_path / "agent-home"))
    return token


@pytest.mark.parametrize("given_boundaries", [False, True], ids=["nothing-given", "boundaries"])
def test_an_environment_without_an_instance_is_refused_with_a_line(
    boundaries: Boundaries, monkeypatch: pytest.MonkeyPatch, *, given_boundaries: bool
) -> None:
    monkeypatch.setenv("FACTORY_REPOSITORY_URL", HOSTED_URL)
    monkeypatch.delenv("FACTORY_INSTANCE", raising=False)
    out, err = io.StringIO(), io.StringIO()

    status = main(
        [], boundaries=boundaries if given_boundaries else None, instance=None, out=out, err=err
    )

    assert status == 2
    prefix = f"{REFUSAL}FACTORY_INSTANCE: "
    assert err.getvalue().startswith(prefix)
    assert err.getvalue().endswith("\n")
    assert err.getvalue().count("\n") == 1
    assert err.getvalue()[len(prefix) :].strip() != ""
    assert out.getvalue() == ""


def test_a_missing_token_file_is_refused_with_a_line_naming_it(
    valid_environment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FACTORY_TOKEN_FILE", str(valid_environment.parent / "no-such-token"))
    out, err = io.StringIO(), io.StringIO()

    status = main([], out=out, err=err)

    assert status == 2
    assert err.getvalue().startswith(f"{REFUSAL}FACTORY_TOKEN_FILE: ")
    assert err.getvalue().endswith("\n")
    assert out.getvalue() == ""


@pytest.mark.usefixtures("valid_environment")
def test_a_valid_environment_gets_past_the_settings_to_the_fixed_checkout() -> None:
    if Path("/work/checkout/.git").exists():
        pytest.skip("the fixed checkout holds a clone on this machine")
    out, err = io.StringIO(), io.StringIO()

    with pytest.raises(GitError):
        main([], out=out, err=err)

    assert "settings invalid" not in err.getvalue()
