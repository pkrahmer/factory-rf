"""Git's credential helper of the image: the token from its file, or nothing at all."""

import os
import shutil
from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.entry.wiring import git_environment
from vm_support import EXAMPLE_VALUE, HELPER, SYSTEM_PATH

GIT_REQUEST = "protocol=https\nhost=github.com\n\n"


def _feed(tmp_path: Path, command: str, environment: dict[str, str]) -> ProcessResult:
    """Run `command` with `sh`, the git request on its standard input."""
    request = tmp_path / "request"
    request.write_text(GIT_REQUEST, encoding="utf-8")
    return run_process(
        ProcessRequest(
            argv=["sh", "-c", f'{command} < "$0"', str(request)],
            cwd=tmp_path,
            env=environment,
        )
    )


def _helper(tmp_path: Path, operation: str, token_file: Path | None) -> ProcessResult:
    environment = {"PATH": SYSTEM_PATH, "HOME": str(tmp_path)}
    if token_file is not None:
        environment["FACTORY_TOKEN_FILE"] = str(token_file)
    return _feed(tmp_path, f"sh '{HELPER}' {operation}", environment)


def test_get_prints_the_user_name_and_the_token_from_the_file(tmp_path: Path, token: Path) -> None:
    result = _helper(tmp_path, "get", token)

    assert result.exit_status == 0
    assert result.stdout.splitlines() == ["username=x-access-token", f"password={EXAMPLE_VALUE}"]


@pytest.mark.parametrize(
    "fault",
    [
        pytest.param(
            "unreadable",
            marks=pytest.mark.skipif(os.geteuid() == 0, reason="root reads any file"),
        ),
        "missing",
        "unset",
    ],
)
def test_get_without_a_readable_token_file_prints_nothing_and_fails(
    tmp_path: Path, token: Path, fault: str
) -> None:
    token.chmod(0o000)
    token_file = {"unreadable": token, "missing": tmp_path / "absent", "unset": None}[fault]

    result = _helper(tmp_path, "get", token_file)

    assert result.exit_status == 1
    assert result.stdout == ""


@pytest.mark.parametrize("operation", ["store", "erase", "foo"])
def test_any_other_operation_prints_nothing_and_succeeds(
    tmp_path: Path, token: Path, operation: str
) -> None:
    result = _helper(tmp_path, operation, token)

    assert result.exit_status == 0
    assert result.stdout == ""
    assert EXAMPLE_VALUE not in result.stderr


@pytest.mark.parametrize("present", [True, False], ids=["token-file", "no-token-file"])
def test_git_credential_fill_gets_the_token_through_the_factorys_git_environment(
    tmp_path: Path, token: Path, *, present: bool
) -> None:
    helper = tmp_path / "git-credential-factory"
    shutil.copyfile(HELPER, helper)
    helper.chmod(0o755)
    inherited = {
        name: value
        for name, value in os.environ.items()
        if name not in {"GIT_ASKPASS", "SSH_ASKPASS"}
    }
    environment = {
        **inherited,
        **git_environment(str(helper)),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "FACTORY_TOKEN_FILE": str(token if present else tmp_path / "absent"),
    }

    result = _feed(tmp_path, "git credential fill", environment)

    if present:
        assert result.exit_status == 0
        assert f"password={EXAMPLE_VALUE}" in result.stdout.splitlines()
    else:
        assert result.exit_status != 0
        assert "password=" not in result.stdout
