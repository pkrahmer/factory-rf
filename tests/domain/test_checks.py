"""The generic check result: its status follows the exit status, and nothing else."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from factory.domain.checks import CheckResult, CheckStatus


def _result(
    status: CheckStatus = "passed", exit_status: int | None = 0, command: str = "check"
) -> CheckResult:
    return CheckResult(
        command=command,
        status=status,
        exit_status=exit_status,
        duration=timedelta(seconds=1),
        last_line="",
        output_tail="",
    )


@pytest.mark.parametrize(
    ("status", "exit_status", "passed"),
    [("passed", 0, True), ("failed", 2, False), ("time_limit", None, False)],
)
def test_status_matching_the_exit_status_is_accepted(
    status: CheckStatus, exit_status: int | None, passed: bool
) -> None:
    result = _result(status, exit_status)

    assert result.status == status
    assert result.exit_status == exit_status
    assert result.passed is passed


@pytest.mark.parametrize(
    ("status", "exit_status"),
    [("passed", 1), ("failed", 0), ("failed", None), ("time_limit", 0), ("time_limit", 124)],
)
def test_status_contradicting_the_exit_status_is_rejected(
    status: CheckStatus, exit_status: int | None
) -> None:
    with pytest.raises(ValidationError):
        _result(status, exit_status)


@pytest.mark.parametrize("command", ["check", "lint-all"])
def test_lowercase_command_names_are_accepted(command: str) -> None:
    assert _result(command=command).command == command


@pytest.mark.parametrize("command", ["Check", "1x", "a b", "", "-f"])
def test_other_command_names_are_rejected(command: str) -> None:
    with pytest.raises(ValidationError):
        _result(command=command)


def test_unknown_keys_and_assignment_are_rejected() -> None:
    result = _result()

    with pytest.raises(ValidationError):
        CheckResult(
            command="check",
            status="passed",
            exit_status=0,
            duration=timedelta(seconds=1),
            last_line="",
            output_tail="",
            layers=["domain"],  # type: ignore[call-arg]
        )
    with pytest.raises(ValidationError):
        result.status = "failed"  # type: ignore[misc]


def test_fields_are_exactly_the_generic_six() -> None:
    assert set(CheckResult.model_fields) == {
        "command",
        "status",
        "exit_status",
        "duration",
        "last_line",
        "output_tail",
    }
