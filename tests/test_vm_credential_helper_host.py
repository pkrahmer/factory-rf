"""Git's credential helper answers only for the host of the project's repository."""

from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from vm_support import EXAMPLE_VALUE, HELPER, SYSTEM_PATH

PROJECT_URL = "https://git.example.invalid/o/r.git"
PROJECT_HOST = "git.example.invalid"
ANSWER = ["username=x-access-token", f"password={EXAMPLE_VALUE}"]


def _helper(
    tmp_path: Path, token: Path, operation: str, url: str, request_lines: list[str]
) -> ProcessResult:
    """Run the helper with `sh`, `FACTORY_REPOSITORY_URL` set to `url` and the request on stdin."""
    request = tmp_path / "request"
    request.write_text("".join(f"{line}\n" for line in request_lines) + "\n", encoding="utf-8")
    return run_process(
        ProcessRequest(
            argv=["sh", "-c", f'sh "$1" {operation} < "$0"', str(request), str(HELPER)],
            cwd=tmp_path,
            env={
                "PATH": SYSTEM_PATH,
                "HOME": str(tmp_path),
                "FACTORY_TOKEN_FILE": str(token),
                "FACTORY_REPOSITORY_URL": url,
            },
        )
    )


def _assert_answer(result: ProcessResult, *, answered: bool) -> None:
    if answered:
        assert result.exit_status == 0
        assert result.stdout.splitlines() == ANSWER
    else:
        assert result.exit_status == 1
        assert result.stdout == ""


@pytest.mark.parametrize(
    ("request_lines", "answered"),
    [
        pytest.param(["protocol=https", "host=git.example.invalid"], True, id="same-host"),
        pytest.param(["protocol=https", "host=GIT.EXAMPLE.INVALID"], True, id="upper-case"),
        pytest.param(["protocol=https", "host=git.example.invalid:443"], True, id="with-port"),
        pytest.param(["protocol=https", "host=github.com"], False, id="other-host"),
        pytest.param(
            ["protocol=https", "host=git.example.invalid.evil.example"], False, id="longer-host"
        ),
        pytest.param(["protocol=https"], False, id="no-host-line"),
    ],
)
def test_get_answers_only_a_request_for_the_project_repository_s_host(
    tmp_path: Path, token: Path, request_lines: list[str], *, answered: bool
) -> None:
    result = _helper(tmp_path, token, "get", PROJECT_URL, request_lines)

    _assert_answer(result, answered=answered)


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("ssh://git@git.example.invalid:22/o/r.git", id="ssh-url"),
        pytest.param("git@git.example.invalid:o/r.git", id="scp-like"),
    ],
)
def test_the_ssh_url_forms_name_their_host(tmp_path: Path, token: Path, url: str) -> None:
    result = _helper(tmp_path, token, "get", url, ["protocol=https", f"host={PROJECT_HOST}"])

    _assert_answer(result, answered=True)


@pytest.mark.parametrize(
    ("url", "answered"),
    [
        pytest.param("https://GIT.EXAMPLE.INVALID/o/r.git", True, id="upper-case"),
        pytest.param("https://user@git.example.invalid:8443/o/r.git", True, id="user-and-port"),
        pytest.param("https://git.example.invalid:8443/o/r.git", True, id="port-only"),
        pytest.param("https://user@other.example.invalid/o/r.git", False, id="other-host"),
    ],
)
def test_the_url_s_case_user_and_port_do_not_change_its_host(
    tmp_path: Path, token: Path, url: str, *, answered: bool
) -> None:
    result = _helper(tmp_path, token, "get", url, ["protocol=https", f"host={PROJECT_HOST}"])

    _assert_answer(result, answered=answered)


@pytest.mark.parametrize("operation", ["store", "erase"])
def test_any_other_operation_prints_nothing_and_succeeds_with_the_url_set(
    tmp_path: Path, token: Path, operation: str
) -> None:
    result = _helper(
        tmp_path, token, operation, PROJECT_URL, ["protocol=https", f"host={PROJECT_HOST}"]
    )

    assert result.exit_status == 0
    assert result.stdout == ""
