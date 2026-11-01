"""The job start script installs the code checkout's credential helper for the factory's git."""

from pathlib import Path

import pytest

from vm_support import JOB_CODE_REF, JOB_CODE_URL, MISSING_REF, JobRun, run_job_start

HELPER = "git-credential-factory"


def _helper_target(run: JobRun) -> str:
    return str(run.prefix / "usr" / "local" / "bin" / HELPER)


def _index(run: JobRun, found: object) -> int:
    return next(index for index, call in enumerate(run.calls) if call is found)


def test_the_code_step_installs_the_checkout_s_helper_between_the_checkout_and_uv(
    tmp_path: Path,
) -> None:
    run = run_job_start(tmp_path)
    target = _helper_target(run)
    helper_calls = [call for call in run.named("install") if target in call.argv]
    checkout = next(
        call
        for call in run.named("git")
        if "checkout" in call.argv and "--detach" in call.argv and JOB_CODE_REF in call.argv
    )
    first_uv = run.named("uv")[0]

    assert run.result.exit_status == 0, run.result.stderr
    assert [call.argv for call in helper_calls] == [
        ["-m", "0755", str(run.root / "factory" / "vm" / HELPER), target]
    ]
    assert _index(run, checkout) < _index(run, helper_calls[0]) < _index(run, first_uv)


@pytest.mark.parametrize(
    ("missing_ref", "failing_helper", "message"),
    [
        pytest.param(
            True, False, f"job-start: code: no ref {MISSING_REF} in {JOB_CODE_URL}", id="no-ref"
        ),
        pytest.param(False, True, "job-start: code: failed", id="helper-install-fails"),
    ],
)
def test_the_code_step_stops_the_script_on_a_missing_ref_or_a_failed_helper_install(
    tmp_path: Path, *, missing_ref: bool, failing_helper: bool, message: str
) -> None:
    target = tmp_path / "prefix" / "usr" / "local" / "bin" / HELPER
    run = run_job_start(
        tmp_path,
        {"FACTORY_CODE_REF": MISSING_REF} if missing_ref else None,
        failing_install_target=target if failing_helper else None,
    )

    assert run.result.exit_status == 1
    assert message in run.result.stderr.splitlines()
    assert run.named("podman") == []
    assert run.named("factory-run") == []
    if missing_ref:
        assert [call for call in run.named("install") if str(target) in call.argv] == []


def test_only_runc_and_the_helper_are_installed_under_usr_local_bin(tmp_path: Path) -> None:
    run = run_job_start(tmp_path)
    folder = run.prefix / "usr" / "local" / "bin"
    targets = {
        Path(word).name
        for call in run.named("install")
        for word in call.argv
        if Path(word).parent == folder
    }

    assert run.result.exit_status == 0, run.result.stderr
    assert targets == {"runc", HELPER}
