"""The operator's job script: the job's call to `gcloud` built from the site's values."""

import base64
import gzip
import json
import os
import re
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.process import ProcessResult
from factory.domain.opencode_provider import read_provider
from git_support import commit_all, run_git, write_executable
from operator_support import ROOT, operator_environment, run_script

JOB = "factory-job"
HOSTING_MOUNT = "/secrets/hosting-token"
MODEL_MOUNT = "/secrets-llm/client-secret"
HOSTING_NAME = "hosting-sm"
MODEL_NAME = "model-sm"
MOUNTS = f"{HOSTING_MOUNT}={HOSTING_NAME}:latest,{MODEL_MOUNT}={MODEL_NAME}:latest"
TAG = "t1"
INSTANCE = "inst-x"
JOB_ROOT = f"/srv/factory/{INSTANCE}"
IMPERSONATE = "deployer@p1.iam.gserviceaccount.com"
NO_PROXY = "localhost,.internal,10.0.0.0/8"
SITE: dict[str, str] = {
    "SITE_PROJECT": "p1",
    "SITE_REGION": "europe-west3",
    "SITE_RUN_AS": "runner@p1.iam.gserviceaccount.com",
    "SITE_CONNECTOR": "conn-1",
    "SITE_PROXY": "http://proxy.example.invalid:3128",
    "SITE_NO_PROXY": NO_PROXY,
    "SITE_JOB": JOB,
    "SITE_INSTANCE": INSTANCE,
    "SITE_REPOSITORY_URL": "https://git.example.invalid/org/work.git",
    "SITE_CODE_URL": "https://git.example.invalid/org/factory.git",
    "SITE_CODE_REF": TAG,
    "SITE_HOSTING_SECRET": HOSTING_NAME,
    "SITE_MODEL_SECRET": MODEL_NAME,
    "SITE_MODEL_BASE_URL": "https://llm.example.invalid/v1",
    "SITE_MODEL": "big-model",
    "SITE_LOGIN_URL": "https://login.example.invalid/token",
    "SITE_LOGIN_SCOPE": "api://llm/.default",
    "SITE_LOGIN_CLIENT_ID": "client-1",
}
BARE = {key: SITE[key] for key in ("SITE_PROJECT", "SITE_REGION", "SITE_JOB")}
WRAPPER = re.compile(r"--args=-c,echo ([A-Za-z0-9+/=]+) \| base64 -d \| gzip -d \| sh")
LONG_BASE64 = re.compile(r"[A-Za-z0-9+/=]{101,}")
START = "exec sh /tmp/job-start.sh"
START_SCRIPT = START.removeprefix("exec sh ")
# What must never reach the job: a token command and secrets in the environment.
MARKED_SITE = {"SITE_TOKEN_CMD": "printf 'TOKEN%s' MARK"}
MARKS = ("TOKENMARK", "SECRETMARK")
MARKED_ENV = dict(zip(("GITHUB_TOKEN", "ANTHROPIC_API_KEY"), MARKS, strict=True))

# A stand-in for gcloud: it records its arguments; `describe` exits with STAND_IN_DESCRIBE
# (1, not found, by default) after writing STAND_IN_DESCRIBE_TEXT to standard error,
# `executions list` prints STAND_IN_EXECUTIONS, `execute` prints STAND_IN_EXECUTION;
# the verb STAND_IN_FAIL fails with STAND_IN_FAIL_STATUS and a text.
GCLOUD_STAND_IN = r"""
import json, os, sys

arguments = sys.argv[1:]
with open(os.environ["STAND_IN_RECORD"], "a", encoding="utf-8") as record:
    record.write(json.dumps(arguments) + "\n")
words = [word for word in arguments if not word.startswith("-")]
verb = "executions list" if words[2:4] == ["executions", "list"] else words[2]
if verb == os.environ.get("STAND_IN_FAIL"):
    sys.stderr.write("ERROR: (gcloud) FAILTEXT\n")
    sys.exit(int(os.environ.get("STAND_IN_FAIL_STATUS", "1")))
if verb == "describe":
    sys.stderr.write(os.environ.get("STAND_IN_DESCRIBE_TEXT", ""))
    sys.exit(int(os.environ.get("STAND_IN_DESCRIBE", "1")))
if verb == "executions list":
    sys.stdout.write(os.environ.get("STAND_IN_EXECUTIONS", ""))
if verb == "execute":
    sys.stdout.write(os.environ.get("STAND_IN_EXECUTION", "") + "\n")
"""

RunJob = Callable[..., ProcessResult]


def env_list(values: dict[str, str], idle: str = "60") -> str:
    """The `--set-env-vars` value the Interface gives for the site `values`."""
    proxy, no_proxy, model = values["SITE_PROXY"], values["SITE_NO_PROXY"], values["SITE_MODEL"]
    root = f"/srv/factory/{values['SITE_INSTANCE']}"
    entries = [
        f"FACTORY_INSTANCE={values['SITE_INSTANCE']}",
        f"FACTORY_REPOSITORY_URL={values['SITE_REPOSITORY_URL']}",
        f"FACTORY_CODE_URL={values['SITE_CODE_URL']}",
        f"FACTORY_CODE_REF={values['SITE_CODE_REF']}",
        f"FACTORY_TOKEN_FILE={HOSTING_MOUNT}",
        f"HTTPS_PROXY={proxy}",
        f"https_proxy={proxy}",
        f"HTTP_PROXY={proxy}",
        f"http_proxy={proxy}",
        f"NO_PROXY={no_proxy}",
        f"no_proxy={no_proxy}",
        "FACTORY_CONTAINER_ENV=HTTPS_PROXY,https_proxy,HTTP_PROXY,http_proxy,NO_PROXY,no_proxy",
        f"FACTORY_OPENCODE_PROVIDER_FILE={root}/provider.json",
        f"FACTORY_OPENCODE_MODELS=opus=site/{model},sonnet=site/{model},haiku=site/{model}",
        f"FACTORY_API_LOGIN_FILE={root}/api-login",
        f"FACTORY_TOKEN_URL={values['SITE_LOGIN_URL']}",
        f"FACTORY_TOKEN_SCOPE={values['SITE_LOGIN_SCOPE']}",
        f"FACTORY_TOKEN_CLIENT_ID={values['SITE_LOGIN_CLIENT_ID']}",
        f"FACTORY_TOKEN_CLIENT_SECRET_FILE={MODEL_MOUNT}",
        f"FACTORY_IDLE_SHUTDOWN_MINUTES={idle}",
    ]
    return "^@^" + "@".join(entries)


def job_flags(cpu: str = "8", memory: str = "32Gi", timeout: str = "14400") -> set[str]:
    """The flags of the `create` or `update` call besides the env list and the wrapper."""
    return {
        f"--project={SITE['SITE_PROJECT']}",
        f"--region={SITE['SITE_REGION']}",
        "--image=docker.io/library/debian:trixie-slim",
        "--execution-environment=gen2",
        f"--cpu={cpu}",
        f"--memory={memory}",
        f"--task-timeout={timeout}",
        "--max-retries=0",
        f"--vpc-connector={SITE['SITE_CONNECTOR']}",
        "--vpc-egress=all-traffic",
        f"--service-account={SITE['SITE_RUN_AS']}",
        f"--set-secrets={MOUNTS}",
        "--command=sh",
    }


def words(call: list[str]) -> list[str]:
    """The words of a call that are no flag, in order."""
    return [word for word in call if not word.startswith("-")]


def flag(call: list[str], name: str) -> str:
    """The value of the one flag `--name=` of `call`."""
    values = [word.removeprefix(f"--{name}=") for word in call if word.startswith(f"--{name}=")]
    assert len(values) == 1, call
    return values[0]


def wrapper_of(call: list[str]) -> str:
    """The script the call's `--args` carries, decoded and un-gzipped."""
    arguments = [word for word in call if word.startswith("--args=")]
    assert len(arguments) == 1, call
    match = WRAPPER.fullmatch(arguments[0])
    assert match is not None, arguments[0]
    return gzip.decompress(base64.b64decode(match.group(1))).decode("utf-8")


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """A git repository with `operator/` and `vm/` committed and tagged `t1`."""
    folder = tmp_path / "repo"
    folder.mkdir()
    run_git(folder, "init", "-q")
    for name in ("operator", "vm"):
        shutil.copytree(ROOT / name, folder / name)
    commit_all(folder, "the operator's scripts")
    run_git(folder, "tag", TAG)
    return folder


@pytest.fixture
def records(tmp_path: Path) -> Path:
    """The file the `gcloud` stand-in records its calls in."""
    return tmp_path / "gcloud.jsonl"


@pytest.fixture
def run_job(tmp_path: Path, repository: Path, records: Path) -> RunJob:
    """Run `job.sh` of `repository` with `words`, a site file of `values` and extra variables.

    The names in `unset` are left out of the environment.
    """
    bin_folder = tmp_path / "bin"
    bin_folder.mkdir()
    write_executable(bin_folder, GCLOUD_STAND_IN, name="gcloud")
    site_folder = tmp_path / "site"
    site_folder.mkdir()
    site_file = site_folder / "site.env"

    def run(
        job_words: list[str], values: dict[str, str], *, unset: tuple[str, ...] = (), **extra: str
    ) -> ProcessResult:
        site_file.write_text(
            "".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8"
        )
        env = operator_environment(
            tmp_path,
            PATH=os.pathsep.join([str(bin_folder), os.environ["PATH"]]),
            FACTORY_SITE=str(site_file),
            XDG_STATE_HOME=str(tmp_path / "state"),
            GIT_CONFIG_NOSYSTEM="1",
            STAND_IN_RECORD=str(records),
            **extra,
        )
        for name in unset:
            del env[name]
        return run_script(
            [str(repository / "operator" / "job" / "job.sh"), *job_words], tmp_path, env
        )

    return run


def calls(records: Path) -> list[list[str]]:
    """The argument lists the `gcloud` stand-in recorded, oldest first."""
    if not records.exists():
        return []
    return [json.loads(line) for line in records.read_text(encoding="utf-8").splitlines()]


def site_path(tmp_path: Path) -> Path:
    """The site file's path the `run_job` fixture writes."""
    return tmp_path / "site" / "site.env"


@pytest.mark.parametrize(
    ("verb", "describe"),
    [pytest.param("create", "1", id="create"), pytest.param("update", "0", id="update")],
)
def test_create_and_update_build_the_job_call_from_the_site(
    run_job: RunJob, records: Path, verb: str, describe: str
) -> None:
    result = run_job([verb], SITE, STAND_IN_DESCRIBE=describe)
    assert result.exit_status == 0, result.stderr
    recorded = calls(records)
    assert [words(call)[:3] for call in recorded] == [
        ["run", "jobs", "describe"],
        ["run", "jobs", verb],
    ]
    assert words(recorded[0])[3] == JOB
    call = recorded[1]
    assert words(call) == ["run", "jobs", verb, JOB]
    others = {
        word
        for word in call
        if word.startswith("--") and not word.startswith(("--set-env-vars=", "--args="))
    }
    assert others == job_flags()
    assert flag(call, "set-env-vars") == env_list(SITE)
    wrapper_of(call)


@pytest.mark.parametrize(
    ("job_words", "impersonate"),
    [
        pytest.param(["create"], True, id="create-impersonating"),
        pytest.param(["create"], False, id="create-not-impersonating"),
        pytest.param(["delete", "--yes"], True, id="delete-impersonating"),
        pytest.param(["delete", "--yes"], False, id="delete-not-impersonating"),
        pytest.param(["execute"], True, id="execute-impersonating"),
        pytest.param(["execute"], False, id="execute-not-impersonating"),
    ],
)
def test_every_call_carries_the_project_the_region_and_the_impersonation(
    run_job: RunJob, records: Path, job_words: list[str], *, impersonate: bool
) -> None:
    values = {**SITE, "SITE_IMPERSONATE": IMPERSONATE} if impersonate else SITE
    result = run_job(job_words, values, STAND_IN_EXECUTION="exec-1")
    assert result.exit_status == 0, result.stderr
    recorded = calls(records)
    assert recorded
    for call in recorded:
        assert f"--project={SITE['SITE_PROJECT']}" in call
        assert f"--region={SITE['SITE_REGION']}" in call
        carried = [word for word in call if word.startswith("--impersonate-service-account")]
        assert carried == ([f"--impersonate-service-account={IMPERSONATE}"] if impersonate else [])


@pytest.mark.parametrize(
    ("job_words", "values", "refused"),
    [
        pytest.param(["create"], SITE, True, id="create"),
        pytest.param(["update"], SITE, True, id="update"),
        pytest.param(["execute"], BARE, False, id="execute"),
        pytest.param(["delete", "--yes"], BARE, False, id="delete"),
    ],
)
def test_missing_site_keys_are_named_in_one_line(
    tmp_path: Path,
    run_job: RunJob,
    records: Path,
    job_words: list[str],
    values: dict[str, str],
    *,
    refused: bool,
) -> None:
    missing = {
        key: value for key, value in values.items() if key not in ("SITE_REGION", "SITE_CODE_REF")
    }
    result = run_job(
        job_words, missing if refused else values, STAND_IN_DESCRIBE="0", STAND_IN_EXECUTION="e"
    )
    if refused:
        line = f"site: missing SITE_REGION, SITE_CODE_REF in {site_path(tmp_path)}"
        assert result.stderr.splitlines() == [line]
        assert result.exit_status == 2
        assert calls(records) == []
    else:
        assert result.exit_status == 0, result.stderr
        assert calls(records)


@pytest.mark.parametrize(
    ("values", "cpu", "memory", "timeout", "idle"),
    [
        pytest.param({}, "8", "32Gi", "14400", "60", id="defaults"),
        pytest.param(
            {
                "SITE_CPU": "4",
                "SITE_MEMORY": "16Gi",
                "SITE_TIMEOUT": "3600",
                "SITE_IDLE_MINUTES": "15",
            },
            "4",
            "16Gi",
            "3600",
            "15",
            id="overrides",
        ),
    ],
)
def test_the_sizes_and_the_idle_minutes_have_defaults_the_site_overrides(
    run_job: RunJob,
    records: Path,
    *,
    values: dict[str, str],
    cpu: str,
    memory: str,
    timeout: str,
    idle: str,
) -> None:
    result = run_job(["create"], {**SITE, **values})
    assert result.exit_status == 0, result.stderr
    call = calls(records)[-1]
    assert {f"--cpu={cpu}", f"--memory={memory}", f"--task-timeout={timeout}"} <= set(call)
    assert f"FACTORY_IDLE_SHUTDOWN_MINUTES={idle}" in flag(call, "set-env-vars").split("@")


def test_the_env_list_holds_the_site_values_and_no_path_and_no_secret(
    run_job: RunJob, records: Path
) -> None:
    result = run_job(
        ["create"],
        {**SITE, **MARKED_SITE},
        **MARKED_ENV,
    )
    assert result.exit_status == 0, result.stderr
    listed = flag(calls(records)[-1], "set-env-vars")
    assert listed.startswith("^@^")
    entries = listed.removeprefix("^@^").split("@")
    assert entries == env_list(SITE).removeprefix("^@^").split("@")
    assert f"NO_PROXY={NO_PROXY}" in entries
    assert f"no_proxy={NO_PROXY}" in entries
    for name in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        assert f"{name}={SITE['SITE_PROXY']}" in entries
    assert not [entry for entry in entries if entry.startswith("PATH=")]
    for mark in MARKS:
        assert mark not in listed


def test_the_secrets_reach_the_job_only_as_mounts(run_job: RunJob, records: Path) -> None:
    result = run_job(
        ["create"],
        {**SITE, **MARKED_SITE},
        **MARKED_ENV,
    )
    assert result.exit_status == 0, result.stderr
    recorded = calls(records)
    assert flag(recorded[-1], "set-secrets") == MOUNTS
    texts = [word for call in recorded for word in call] + [wrapper_of(recorded[-1])]
    for mark in MARKS:
        assert not [text for text in texts if mark in text]


def test_the_wrapper_writes_the_provider_and_hands_over_to_the_tagged_start_script(
    run_job: RunJob, records: Path, repository: Path
) -> None:
    start = repository / "vm" / "job-start.sh"
    tagged = start.read_text(encoding="utf-8")
    start.write_text(tagged + "# changed in the work tree only\n", encoding="utf-8")
    result = run_job(["create"], SITE)
    assert result.exit_status == 0, result.stderr
    script = wrapper_of(calls(records)[-1])
    assert f"mkdir -p {JOB_ROOT}" in script
    assert f"{JOB_ROOT}/provider.json" in script
    assert START_SCRIPT in script
    assert script.rstrip().endswith(START)
    assert tagged in script
    assert "changed in the work tree only" not in script
    own = script.replace(tagged, "")
    for text in ("chmod", "cp ", "PATH="):
        assert text not in own


@pytest.mark.parametrize(
    "job_words",
    [
        pytest.param(["create"], id="create"),
        pytest.param(["update"], id="update"),
        pytest.param(["create", "--dry-run"], id="create-dry-run"),
    ],
)
def test_a_code_ref_the_repository_does_not_know_stops_before_gcloud(
    run_job: RunJob, records: Path, job_words: list[str]
) -> None:
    result = run_job(job_words, {**SITE, "SITE_CODE_REF": "unknown-ref"}, STAND_IN_DESCRIBE="0")
    assert "job: unknown-ref is not known here; fetch it first" in result.stderr
    assert result.exit_status == 1
    assert calls(records) == []


@pytest.mark.parametrize(
    ("values", "input_cost", "output_cost"),
    [
        pytest.param({}, 0, 0, id="unset-costs"),
        pytest.param(
            {"SITE_MODEL_INPUT_COST": "3", "SITE_MODEL_OUTPUT_COST": "15.5"},
            3,
            15.5,
            id="set-costs",
        ),
        pytest.param({"SITE_MODEL": 'big"model'}, 0, 0, id="quote-in-model"),
        pytest.param(
            {"SITE_MODEL_BASE_URL": 'https://llm.example.invalid/v1?q="a"'}, 0, 0, id="quote-in-url"
        ),
    ],
)
def test_the_provider_file_the_wrapper_writes_is_a_valid_provider(
    tmp_path: Path,
    run_job: RunJob,
    records: Path,
    *,
    values: dict[str, str],
    input_cost: float,
    output_cost: float,
) -> None:
    site = {**SITE, **values}
    result = run_job(["create"], site)
    assert result.exit_status == 0, result.stderr
    script = wrapper_of(calls(records)[-1])
    root = tmp_path / "job-root"
    # The wrapper runs here with its two folders moved into tmp_path and without the hand-over.
    local = (
        script.replace(START, "exit 0")
        .replace(JOB_ROOT, str(root))
        .replace(START_SCRIPT, str(tmp_path / "job-start.sh"))
    )
    ran = run_script(["-c", local], tmp_path, operator_environment(tmp_path))
    assert ran.exit_status == 0, ran.stderr
    text = (root / "provider.json").read_text(encoding="utf-8")
    model = site["SITE_MODEL"]
    raw = json.loads(text)["models"][model]
    assert isinstance(raw["input_cost"], int | float)
    assert isinstance(raw["output_cost"], int | float)
    provider = read_provider(text)
    assert provider.id == "site"
    assert provider.base_url == site["SITE_MODEL_BASE_URL"]
    assert list(provider.models) == [model]
    assert provider.models[model].input_cost == input_cost
    assert provider.models[model].output_cost == output_cost
    assert provider.small_model == f"site/{model}"


@pytest.mark.parametrize(
    ("verb", "describe", "message"),
    [
        pytest.param("create", "0", f"job: {JOB} exists; use update", id="create-existing"),
        pytest.param("update", "1", f"job: {JOB} does not exist; use create", id="update-missing"),
    ],
)
def test_create_and_update_refuse_the_wrong_state_of_the_job(
    run_job: RunJob, records: Path, verb: str, describe: str, message: str
) -> None:
    result = run_job([verb], SITE, STAND_IN_DESCRIBE=describe)
    shown = result.stderr if verb == "create" else result.stdout + result.stderr
    assert message in shown
    assert result.exit_status == 1
    assert [words(call)[2] for call in calls(records)] == ["describe"]


@pytest.mark.parametrize("verb", ["create", "update"])
def test_a_dry_run_prints_the_call_and_runs_no_gcloud(
    run_job: RunJob, records: Path, verb: str
) -> None:
    result = run_job([verb, "--dry-run"], SITE, STAND_IN_DESCRIBE="0")
    assert result.exit_status == 0, result.stderr
    assert calls(records) == []
    lines = result.stdout.splitlines()
    assert {"run", "jobs", verb, JOB} <= set(lines)
    assert job_flags() <= set(lines)
    assert f"--set-env-vars={env_list(SITE)}" in lines
    assert re.search(r"<wrapper: \d+ bytes>", result.stdout)
    assert LONG_BASE64.search(result.stdout) is None


@pytest.mark.parametrize(
    ("executions", "running"),
    [
        pytest.param("exec-a\t1\n", "exec-a", id="count-1"),
        pytest.param("exec-a\t2\n", "exec-a", id="count-2"),
        pytest.param("exec-a\t0\nexec-b\t\nexec-c\t1\n", "exec-c", id="a-later-row-running"),
        pytest.param("exec-a\t0\nexec-b\t\n", None, id="none-running"),
    ],
)
def test_execute_refuses_to_overlap_a_running_execution(
    tmp_path: Path, run_job: RunJob, records: Path, executions: str, running: str | None
) -> None:
    result = run_job(
        ["execute"], BARE, STAND_IN_EXECUTIONS=executions, STAND_IN_EXECUTION="exec-new"
    )
    recorded = calls(records)
    listing = recorded[0]
    assert words(listing) == ["run", "jobs", "executions", "list"]
    assert f"--job={JOB}" in listing
    assert "--format=value(metadata.name,status.runningCount)" in listing
    if running is not None:
        message = (
            f"job: an execution of {JOB} is still running: {running}; "
            "two executions of one instance must not overlap"
        )
        assert message in result.stdout + result.stderr
        assert result.exit_status == 1
        assert len(recorded) == 1
    else:
        assert result.exit_status == 0, result.stderr
        assert len(recorded) == 2
        assert words(recorded[1]) == ["run", "jobs", "execute", JOB]
        assert {"--async", "--format=value(metadata.name)"} <= set(recorded[1])
        assert result.stdout.splitlines() == ["exec-new"]
        saved = tmp_path / "state" / "kumpel" / "last-execution"
        assert saved.read_text(encoding="utf-8").strip() == "exec-new"


@pytest.mark.parametrize(
    "confirmed", [pytest.param(False, id="without-yes"), pytest.param(True, id="with-yes")]
)
def test_delete_asks_for_yes(run_job: RunJob, records: Path, *, confirmed: bool) -> None:
    result = run_job(["delete", "--yes"] if confirmed else ["delete"], BARE)
    deletes = [call for call in calls(records) if words(call)[2:3] == ["delete"]]
    if confirmed:
        assert result.exit_status == 0, result.stderr
        assert len(deletes) == 1
        assert words(deletes[0]) == ["run", "jobs", "delete", JOB]
        assert "--quiet" in deletes[0]
    else:
        message = f"job: would delete {JOB} and stop its running execution; run again with --yes"
        assert message in result.stdout + result.stderr
        assert result.exit_status == 1
        assert deletes == []


@pytest.mark.parametrize(
    ("job_words", "values", "failing", "describe", "status"),
    [
        pytest.param(["create"], SITE, "create", "1", 1, id="create"),
        pytest.param(["update"], SITE, "update", "0", 1, id="update"),
        pytest.param(["execute"], BARE, "executions list", "1", 3, id="execute-list"),
        pytest.param(["execute"], BARE, "execute", "1", 1, id="execute"),
        pytest.param(["delete", "--yes"], BARE, "delete", "1", 1, id="delete"),
    ],
)
def test_a_failing_gcloud_shows_its_error_and_its_status(
    run_job: RunJob,
    *,
    job_words: list[str],
    values: dict[str, str],
    failing: str,
    describe: str,
    status: int,
) -> None:
    result = run_job(
        job_words,
        values,
        STAND_IN_FAIL=failing,
        STAND_IN_FAIL_STATUS=str(status),
        STAND_IN_DESCRIBE=describe,
        STAND_IN_EXECUTION="exec-new",
    )
    assert "ERROR: (gcloud) FAILTEXT" in result.stderr
    assert result.exit_status == status


@pytest.mark.parametrize(
    "job_words",
    [pytest.param(["execute"], id="execute"), pytest.param(["delete", "--yes"], id="delete")],
)
def test_execute_and_delete_name_a_missing_job(
    tmp_path: Path, run_job: RunJob, records: Path, job_words: list[str]
) -> None:
    values = {key: value for key, value in BARE.items() if key != "SITE_JOB"}
    result = run_job(job_words, values, STAND_IN_EXECUTION="exec-new")
    assert result.stderr.splitlines() == [f"site: missing SITE_JOB in {site_path(tmp_path)}"]
    assert result.exit_status == 2
    assert calls(records) == []


def test_execute_saves_the_name_under_home_without_xdg_state_home(
    tmp_path: Path, run_job: RunJob
) -> None:
    result = run_job(["execute"], BARE, unset=("XDG_STATE_HOME",), STAND_IN_EXECUTION="exec-new")
    assert result.exit_status == 0, result.stderr
    saved = tmp_path / "home" / ".local" / "state" / "kumpel" / "last-execution"
    assert saved.read_text(encoding="utf-8").strip() == "exec-new"


USAGE = "usage: job.sh create [--dry-run] | update [--dry-run] | execute | delete [--yes]"


@pytest.mark.parametrize(
    "job_words",
    [
        pytest.param([], id="no-command"),
        pytest.param(["unknown"], id="unknown-command"),
        pytest.param(["create", "--yes"], id="create-yes"),
        pytest.param(["update", "--force"], id="update-force"),
        pytest.param(["execute", "--dry-run"], id="execute-dry-run"),
        pytest.param(["delete", "--dry-run"], id="delete-dry-run"),
    ],
)
def test_a_wrong_command_line_prints_the_usage(
    run_job: RunJob, records: Path, job_words: list[str]
) -> None:
    result = run_job(job_words, SITE, STAND_IN_DESCRIBE="0", STAND_IN_EXECUTION="exec-new")
    assert USAGE in result.stderr.splitlines()
    assert result.exit_status == 2
    assert calls(records) == []


def test_a_start_script_holding_the_wrappers_end_line_is_refused(
    run_job: RunJob, records: Path, repository: Path
) -> None:
    start = repository / "vm" / "job-start.sh"
    start.write_text(start.read_text(encoding="utf-8") + "JOB_START_SH_END\n", encoding="utf-8")
    commit_all(repository, "a start script holding the end line")
    run_git(repository, "tag", "t2")
    result = run_job(["create"], {**SITE, "SITE_CODE_REF": "t2"})
    message = "job: vm/job-start.sh holds the line JOB_START_SH_END; the wrapper cannot carry it"
    assert message in result.stderr.splitlines()
    assert result.exit_status == 1
    assert calls(records) == []


DESCRIBE_TEXT = "ERROR: (gcloud) DESCRIBETEXT"


@pytest.mark.parametrize("verb", ["update", "create"])
def test_a_failing_describe_is_shown_by_update_and_hidden_by_create(
    run_job: RunJob, records: Path, verb: str
) -> None:
    result = run_job(
        [verb], SITE, STAND_IN_DESCRIBE="1", STAND_IN_DESCRIBE_TEXT=DESCRIBE_TEXT + "\n"
    )
    verbs = [words(call)[2] for call in calls(records)]
    if verb == "update":
        message = f"job: {JOB} does not exist; use create"
        assert DESCRIBE_TEXT in result.stderr
        assert message in result.stdout + result.stderr
        if message in result.stderr:
            assert result.stderr.index(DESCRIBE_TEXT) < result.stderr.index(message)
        assert result.exit_status == 1
        assert verbs == ["describe"]
    else:
        assert DESCRIBE_TEXT not in result.stdout + result.stderr
        assert result.exit_status == 0, result.stderr
        assert verbs == ["describe", "create"]
