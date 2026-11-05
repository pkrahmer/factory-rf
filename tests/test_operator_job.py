"""The operator's job script: the job's call to `gcloud` built from the site's values."""

import json
import re
from pathlib import Path

import pytest

from factory.agents.domain.opencode_provider import read_provider
from git_support import commit_all, run_git
from operator_job_support import (
    BARE,
    IMPERSONATE,
    INSTANCE,
    JOB,
    JOB_ROOT,
    START,
    START_SCRIPT,
    TAG,
    RunJob,
    job_runner,
    make_job_repository,
    provider_text,
    words,
    wrapper_of,
)
from recording_stand_in_support import read_records

HOSTING_MOUNT = "/secrets/hosting-token"
MODEL_MOUNT = "/secrets-llm/client-secret"
HOSTING_NAME = "hosting-sm"
MODEL_NAME = "model-sm"
MOUNTS = f"{HOSTING_MOUNT}={HOSTING_NAME}:latest,{MODEL_MOUNT}={MODEL_NAME}:latest"
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
LONG_BASE64 = re.compile(r"[A-Za-z0-9+/=]{101,}")
# What must never reach the job: a token command and secrets in the environment.
MARKED_SITE = {"SITE_TOKEN_CMD": "printf 'TOKEN%s' MARK"}
MARKS = ("TOKENMARK", "SECRETMARK")
MARKED_ENV = dict(zip(("GITHUB_TOKEN", "ANTHROPIC_API_KEY"), MARKS, strict=True))


def env_list(values: dict[str, str], idle: str = "30") -> str:
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


def job_flags(cpu: str = "4", memory: str = "16Gi", timeout: str = "86400") -> set[str]:
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


def flag(call: list[str], name: str) -> str:
    """The value of the one flag `--name=` of `call`."""
    values = [word.removeprefix(f"--{name}=") for word in call if word.startswith(f"--{name}=")]
    assert len(values) == 1, call
    return values[0]


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """A git repository with `operator/` and `vm/` committed and tagged `t1`."""
    return make_job_repository(tmp_path / "repo")


@pytest.fixture
def records(tmp_path: Path) -> Path:
    """The file the `gcloud` stand-in records its calls in."""
    return tmp_path / "gcloud.jsonl"


@pytest.fixture
def run_job(tmp_path: Path, repository: Path, records: Path) -> RunJob:
    """Run `job.sh` of `repository` with `words`, a site file of `values` and extra variables.

    The names in `unset` are left out of the environment.
    """
    return job_runner(tmp_path, repository, records)


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
    recorded = read_records(records)
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
    recorded = read_records(records)
    assert recorded
    for call in recorded:
        assert f"--project={SITE['SITE_PROJECT']}" in call
        assert f"--region={SITE['SITE_REGION']}" in call
        carried = [word for word in call if word.startswith("--impersonate-service-account")]
        assert carried == ([f"--impersonate-service-account={IMPERSONATE}"] if impersonate else [])


@pytest.mark.parametrize(
    ("job_words", "values", "missing"),
    [
        pytest.param(["create"], SITE, ("SITE_REGION", "SITE_CODE_REF"), id="create"),
        pytest.param(["update"], SITE, ("SITE_REGION", "SITE_CODE_REF"), id="update"),
        pytest.param(["execute"], BARE, (), id="execute"),
        pytest.param(["delete", "--yes"], BARE, (), id="delete"),
        pytest.param(["execute"], BARE, ("SITE_JOB",), id="execute-without-job"),
        pytest.param(["delete", "--yes"], BARE, ("SITE_JOB",), id="delete-without-job"),
    ],
)
def test_missing_site_keys_are_named_in_one_line(
    tmp_path: Path,
    run_job: RunJob,
    records: Path,
    job_words: list[str],
    values: dict[str, str],
    *,
    missing: tuple[str, ...],
) -> None:
    kept = {key: value for key, value in values.items() if key not in missing}
    result = run_job(job_words, kept, STAND_IN_DESCRIBE="0", STAND_IN_EXECUTION="e")
    if missing:
        line = f"site: missing {', '.join(missing)} in {site_path(tmp_path)}"
        assert result.stderr.splitlines() == [line]
        assert result.exit_status == 2
        assert read_records(records) == []
    else:
        assert result.exit_status == 0, result.stderr
        assert read_records(records)


@pytest.mark.parametrize(
    ("values", "cpu", "memory", "timeout", "idle"),
    [
        pytest.param({}, "4", "16Gi", "86400", "30", id="defaults"),
        pytest.param(
            {
                "SITE_CPU": "8",
                "SITE_MEMORY": "32Gi",
                "SITE_TIMEOUT": "3600",
                "SITE_IDLE_MINUTES": "15",
            },
            "8",
            "32Gi",
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
    call = read_records(records)[-1]
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
    listed = flag(read_records(records)[-1], "set-env-vars")
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
    recorded = read_records(records)
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
    script = wrapper_of(read_records(records)[-1])
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
    assert read_records(records) == []


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
    text = provider_text(tmp_path, read_records(records)[-1])
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
    assert [words(call)[2] for call in read_records(records)] == ["describe"]


@pytest.mark.parametrize("verb", ["create", "update"])
def test_a_dry_run_prints_the_call_and_runs_no_gcloud(
    run_job: RunJob, records: Path, verb: str
) -> None:
    result = run_job([verb, "--dry-run"], SITE, STAND_IN_DESCRIBE="0")
    assert result.exit_status == 0, result.stderr
    assert read_records(records) == []
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
    recorded = read_records(records)
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
    deletes = [call for call in read_records(records) if words(call)[2:3] == ["delete"]]
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


def test_execute_saves_the_name_under_home_without_xdg_state_home(
    tmp_path: Path, run_job: RunJob
) -> None:
    result = run_job(["execute"], BARE, unset=("XDG_STATE_HOME",), STAND_IN_EXECUTION="exec-new")
    assert result.exit_status == 0, result.stderr
    saved = tmp_path / "home" / ".local" / "state" / "kumpel" / "last-execution"
    assert saved.read_text(encoding="utf-8").strip() == "exec-new"


USAGE = (
    "usage: job.sh create [--dry-run] | update [--dry-run] | execute | delete [--yes]"
    " | log [N] [--execution NAME] [--quiet] | status"
)


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
    assert read_records(records) == []


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
    assert read_records(records) == []


DESCRIBE_TEXT = "ERROR: (gcloud) DESCRIBETEXT"


@pytest.mark.parametrize("verb", ["update", "create"])
def test_a_failing_describe_is_shown_by_update_and_hidden_by_create(
    run_job: RunJob, records: Path, verb: str
) -> None:
    result = run_job(
        [verb], SITE, STAND_IN_DESCRIBE="1", STAND_IN_DESCRIBE_TEXT=DESCRIBE_TEXT + "\n"
    )
    verbs = [words(call)[2] for call in read_records(records)]
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


def found(job_words: list[str]) -> str:
    """The `describe` status under which the command `job_words` goes on: `update` needs the job."""
    return "0" if job_words[0] == "update" else "1"


INSTANCE_REFUSED = "job: SITE_INSTANCE may hold only letters, digits, '.', '_' and '-'"


@pytest.mark.parametrize(
    ("job_words", "instance", "refused"),
    [
        *(
            pytest.param(["create"], instance, True, id=f"create-{instance}")
            for instance in ("a;rm", "a b", "$(x)", "a/b", "a@b", "inst-ä")
        ),
        pytest.param(["update"], "a;rm", True, id="update-a;rm"),
        pytest.param(["create", "--dry-run"], "a;rm", True, id="create-dry-run-a;rm"),
        pytest.param(["create"], "Inst-1.b_c", False, id="create-Inst-1.b_c"),
    ],
)
def test_an_instance_name_holds_only_letters_digits_dots_underscores_and_dashes(
    run_job: RunJob, records: Path, job_words: list[str], instance: str, *, refused: bool
) -> None:
    result = run_job(
        job_words, {**SITE, "SITE_INSTANCE": instance}, STAND_IN_DESCRIBE=found(job_words)
    )
    if refused:
        assert INSTANCE_REFUSED in result.stderr.splitlines()
        assert result.exit_status == 1
        assert read_records(records) == []
    else:
        assert result.exit_status == 0, result.stderr
        assert words(read_records(records)[-1])[2] == "create"


ENV_KEYS = (
    "SITE_REPOSITORY_URL",
    "SITE_CODE_URL",
    "SITE_CODE_REF",
    "SITE_PROXY",
    "SITE_NO_PROXY",
    "SITE_MODEL",
    "SITE_LOGIN_URL",
    "SITE_LOGIN_SCOPE",
    "SITE_LOGIN_CLIENT_ID",
    "SITE_IDLE_MINUTES",
)
WITHOUT_AT = {**SITE, "SITE_IDLE_MINUTES": "60"}
SSH_URL = "git@host:org/work.git"


def with_at(key: str) -> str:
    """A value of `key` holding `@`: the SSH form of the repository's URL, else `@` added."""
    return SSH_URL if key == "SITE_REPOSITORY_URL" else WITHOUT_AT[key] + "@x"


@pytest.mark.parametrize(
    ("job_words", "key"),
    [
        *(pytest.param(["create"], key, id=f"create-{key}") for key in ENV_KEYS),
        pytest.param(["update"], "SITE_REPOSITORY_URL", id="update-ssh-url"),
        pytest.param(["create", "--dry-run"], "SITE_REPOSITORY_URL", id="create-dry-run-ssh-url"),
        pytest.param(["create"], None, id="create-without-at"),
    ],
)
def test_a_value_of_the_env_list_holds_no_at_sign(
    run_job: RunJob, records: Path, job_words: list[str], key: str | None
) -> None:
    values = WITHOUT_AT if key is None else {**WITHOUT_AT, key: with_at(key)}
    result = run_job(job_words, values, STAND_IN_DESCRIBE=found(job_words))
    if key is not None:
        message = f"job: {key} holds '@', the delimiter of the job's env list"
        assert message in result.stderr.splitlines()
        assert result.exit_status == 1
        assert read_records(records) == []
    else:
        assert result.exit_status == 0, result.stderr
        assert words(read_records(records)[-1])[2] == "create"


INPUT_COST = "SITE_MODEL_INPUT_COST"
OUTPUT_COST = "SITE_MODEL_OUTPUT_COST"


@pytest.mark.parametrize(
    ("job_words", "key", "cost"),
    [
        pytest.param(["create"], INPUT_COST, "abc", id="create-input-abc"),
        pytest.param(["create"], OUTPUT_COST, "nan", id="create-output-nan"),
        pytest.param(["create"], INPUT_COST, "inf", id="create-input-inf"),
        pytest.param(["create"], OUTPUT_COST, "-1", id="create-output-minus-1"),
        pytest.param(["create"], INPUT_COST, "1e3", id="create-input-1e3"),
        pytest.param(["create"], OUTPUT_COST, "1.2.3", id="create-output-1.2.3"),
        pytest.param(["create"], INPUT_COST, ".", id="create-input-dot"),
        pytest.param(["create"], OUTPUT_COST, "abc", id="create-output-abc"),
        pytest.param(["update"], INPUT_COST, "abc", id="update-input-abc"),
        pytest.param(["create", "--dry-run"], INPUT_COST, "abc", id="create-dry-run-input-abc"),
        *(
            pytest.param(["create"], None, cost, id=f"create-accepted-{cost}")
            for cost in ("0", "3", "15.5", ".5", "1.")
        ),
    ],
)
def test_a_price_is_digits_with_at_most_one_dot(
    tmp_path: Path,
    run_job: RunJob,
    records: Path,
    job_words: list[str],
    *,
    key: str | None,
    cost: str,
) -> None:
    if key is not None:
        result = run_job(job_words, {**SITE, key: cost}, STAND_IN_DESCRIBE=found(job_words))
        assert f"job: {key} is not a number" in result.stderr.splitlines()
        assert result.exit_status == 1
        assert read_records(records) == []
    else:
        result = run_job(job_words, {**SITE, INPUT_COST: cost, OUTPUT_COST: cost})
        assert result.exit_status == 0, result.stderr
        text = provider_text(tmp_path, read_records(records)[-1])
        written = json.loads(text)["models"][SITE["SITE_MODEL"]]
        for name in ("input_cost", "output_cost"):
            assert isinstance(written[name], int | float)
            assert written[name] == float(cost)
