"""The job start script's environment: its `PATH`, its private token copy and its proxy names."""

from pathlib import Path

import pytest

from tmp_path_support import file_mode
from vm_support import SYSTEM_PATH, JobRun, StandInCall, run_job_start

PROXY_NAMES = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy")
GIVEN_CONTENT = "TOKENMARK\n"
OLD_CONTENT = "an old token\n"


def _token_in_folder(tmp_path: Path, mode: int) -> Path:
    token = tmp_path / "given" / "hosting-token"
    token.parent.mkdir()
    token.write_text(GIVEN_CONTENT, encoding="utf-8")
    token.parent.chmod(mode)
    return token


def _builds(run: JobRun) -> list[StandInCall]:
    return [call for call in run.named("podman") if "build" in call.argv]


def _token_lines(run: JobRun) -> list[str]:
    return [
        line
        for line in (run.result.stdout + run.result.stderr).splitlines()
        if "token-file" in line
    ]


@pytest.fixture
def plain_run(tmp_path: Path) -> JobRun:
    """A run with every required input and nothing more."""
    return run_job_start(tmp_path)


def test_factory_run_starts_with_the_tools_folder_first_on_the_path(
    tmp_path: Path, plain_run: JobRun
) -> None:
    started = plain_run.named("factory-run")

    assert plain_run.result.exit_status == 0, plain_run.result.stderr
    assert len(started) == 1
    assert started[0].env["PATH"].split(":") == [
        str(plain_run.root / "tools" / "bin"),
        str(tmp_path / "stand-ins"),
        *SYSTEM_PATH.split(":"),
    ]


def test_the_image_build_starts_with_the_tools_folder_first_on_the_path(
    tmp_path: Path, plain_run: JobRun
) -> None:
    builds = _builds(plain_run)

    assert plain_run.result.exit_status == 0, plain_run.result.stderr
    assert len(builds) == 1
    assert builds[0].env["PATH"].split(":") == [
        str(plain_run.root / "tools" / "bin"),
        str(tmp_path / "stand-ins"),
        *SYSTEM_PATH.split(":"),
    ]


@pytest.mark.parametrize(
    ("mode", "copied"),
    [
        pytest.param(0o755, True, id="0755"),
        pytest.param(0o750, True, id="0750"),
        pytest.param(0o705, True, id="0705"),
        pytest.param(0o700, False, id="0700"),
    ],
)
def test_a_token_is_copied_into_a_private_folder_only_when_its_folder_is_not_private(
    tmp_path: Path, mode: int, *, copied: bool
) -> None:
    token = _token_in_folder(tmp_path, mode)
    original_mode = file_mode(token)
    run = run_job_start(tmp_path, {"FACTORY_TOKEN_FILE": str(token)})
    secrets = run.root / "secrets"
    copy = secrets / "hosting-token"
    started = run.named("factory-run")

    assert run.result.exit_status == 0, run.result.stderr
    assert len(started) == 1
    assert token.read_text(encoding="utf-8") == GIVEN_CONTENT
    assert file_mode(token) == original_mode
    if copied:
        assert started[0].env["FACTORY_TOKEN_FILE"] == str(copy)
        assert file_mode(secrets) == 0o700
        assert file_mode(copy) == 0o600
        assert copy.read_bytes() == token.read_bytes()
        assert f"job-start: token-file: copied to {secrets}" in run.result.stdout.splitlines()
    else:
        assert started[0].env["FACTORY_TOKEN_FILE"] == str(token)
        assert not secrets.exists()
        assert _token_lines(run) == []


def test_the_token_s_text_is_never_printed_when_it_is_copied(tmp_path: Path) -> None:
    token = _token_in_folder(tmp_path, 0o755)
    run = run_job_start(tmp_path, {"FACTORY_TOKEN_FILE": str(token)})

    assert run.result.exit_status == 0, run.result.stderr
    assert "TOKENMARK" not in run.result.stdout
    assert "TOKENMARK" not in run.result.stderr


def test_a_failing_copy_stops_the_script_before_factory_run(tmp_path: Path) -> None:
    token = _token_in_folder(tmp_path, 0o755)
    (tmp_path / "root").mkdir()
    (tmp_path / "root" / "secrets").write_text("in the way\n", encoding="utf-8")
    run = run_job_start(tmp_path, {"FACTORY_TOKEN_FILE": str(token)})

    assert run.result.exit_status == 1
    assert "job-start: token-file: failed" in run.result.stderr.splitlines()
    assert run.named("factory-run") == []


def test_a_missing_token_file_stops_the_script_as_before(tmp_path: Path) -> None:
    run = run_job_start(tmp_path, {"FACTORY_TOKEN_FILE": str(tmp_path / "no-such-token")})

    assert run.result.exit_status == 2
    assert "job-start: FACTORY_TOKEN_FILE is not a file" in run.result.stderr.splitlines()
    assert run.named("factory-run") == []


@pytest.mark.parametrize(
    ("inputs", "expected"),
    [
        pytest.param({"https_proxy": "P"}, ("P", "P", "P", "P"), id="lower-only"),
        pytest.param({"HTTPS_PROXY": "P"}, ("P", "P", "P", "P"), id="upper-only"),
        pytest.param(
            {"https_proxy": "P", "http_proxy": "Q"}, ("P", "P", "P", "Q"), id="own-lower-http"
        ),
        pytest.param(
            {"https_proxy": "P", "HTTP_PROXY": "Q"}, ("P", "P", "Q", "P"), id="own-upper-http"
        ),
        pytest.param(
            {"HTTPS_PROXY": "", "https_proxy": "P"}, ("P", "P", "P", "P"), id="empty-upper"
        ),
        pytest.param({"HTTPS_PROXY": "A", "https_proxy": "B"}, ("A", "A", "A", "A"), id="both"),
        pytest.param(
            {"https_proxy": "P", "http_proxy": ""}, ("P", "P", "P", "P"), id="empty-lower-http"
        ),
    ],
)
def test_a_given_proxy_reaches_the_image_build_under_all_four_names(
    tmp_path: Path, inputs: dict[str, str | None], expected: tuple[str, str, str, str]
) -> None:
    run = run_job_start(tmp_path, inputs)
    builds = _builds(run)

    assert run.result.exit_status == 0, run.result.stderr
    assert len(builds) == 1
    assert tuple(builds[0].env.get(name) for name in PROXY_NAMES) == expected


def test_without_a_proxy_no_stand_in_sees_one_and_apt_is_not_configured(
    plain_run: JobRun,
) -> None:
    seen = [
        (call.name, name) for call in plain_run.calls for name in PROXY_NAMES if name in call.env
    ]

    assert plain_run.result.exit_status == 0, plain_run.result.stderr
    assert plain_run.calls != []
    assert seen == []
    assert not (plain_run.prefix / "etc" / "apt" / "apt.conf.d" / "99proxy").exists()


def test_a_second_run_makes_an_existing_secrets_folder_private_and_replaces_the_old_token(
    tmp_path: Path,
) -> None:
    token = _token_in_folder(tmp_path, 0o755)
    secrets = tmp_path / "root" / "secrets"
    secrets.mkdir(parents=True)
    (secrets / "hosting-token").write_text(OLD_CONTENT, encoding="utf-8")
    (secrets / "hosting-token").chmod(0o644)
    secrets.chmod(0o755)
    run = run_job_start(tmp_path, {"FACTORY_TOKEN_FILE": str(token)})

    assert run.result.exit_status == 0, run.result.stderr
    assert file_mode(secrets) == 0o700
    assert file_mode(secrets / "hosting-token") == 0o600
    assert (secrets / "hosting-token").read_text(encoding="utf-8") == GIVEN_CONTENT
