"""The operator's `site check`: read-only checks of a machine's setup, one line each."""

import json
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from support.operator_support import (
    ROOT,
    example_keys,
)
from support.site_check_support import (
    CODE_URL,
    HOSTING_NAME,
    IMPERSONATE,
    JOB,
    MARK,
    MODEL_NAME,
    NAMES,
    NO_ACCESS,
    PROXY,
    REF,
    REPOSITORY,
    SILENT_COMMAND,
    Machine,
    Setup,
    check_lines,
    gcloud_words,
    git_command,
    line_of,
    link_system,
    site,
)


@pytest.fixture(scope="module")
def system(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A folder of links to the machine's programs, without those the stand-ins replace."""
    return link_system(tmp_path_factory.mktemp("system"))


@pytest.fixture
def machine(tmp_path: Path, system: Path) -> Machine:
    """A fresh operator's machine."""
    return Machine(tmp_path, system)


def test_a_ready_machine_passes_every_check_in_order(machine: Machine) -> None:
    result = machine.run()
    expected = [f"ok {name}" for name in NAMES[:-1]] + [f"ok job: {JOB} exists", "site: ready"]
    assert result.stdout.splitlines() == expected, result.stderr
    assert result.exit_status == 0


@pytest.mark.parametrize(
    ("setup", "check", "detail", "failed"),
    [
        pytest.param(
            Setup(site_file=False),
            "site file",
            lambda d: (
                d.startswith("site: no site file at ") and d.endswith("/site.env; run: site init")
            ),
            1,
            id="site-file-missing",
        ),
        pytest.param(
            Setup(changes=site(SITE_CONNECTOR=None)),
            "keys",
            lambda d: "SITE_CONNECTOR" in d and "SITE_RESET_REPOSITORY" not in d,
            1,
            id="key-missing",
        ),
        pytest.param(
            Setup(missing=frozenset({"gcloud"})),
            "tools",
            lambda d: "gcloud" in d,
            3,
            id="gcloud-not-on-the-path",
        ),
        pytest.param(
            Setup(changes=site(SITE_TOKEN_CMD=SILENT_COMMAND)),
            "token",
            lambda d: d == NO_ACCESS,
            2,
            id="token-command-prints-nothing",
        ),
        pytest.param(
            Setup(repository="missing"),
            "repository",
            lambda d: d == f"hosting: GET /repos/{REPOSITORY}: 404 Not Found",
            1,
            id="repository-not-found",
        ),
        pytest.param(
            Setup(repository="pull"),
            "repository",
            lambda d: d == "the token has no push permission",
            1,
            id="no-push-permission",
        ),
        pytest.param(
            Setup(checkout="plain"),
            "checkout",
            lambda d: "work tree" in d,
            1,
            id="checkout-not-a-work-tree",
        ),
        pytest.param(
            Setup(checkout="other origin"),
            "checkout",
            lambda d: "origin" in d,
            1,
            id="checkout-of-another-repository",
        ),
        pytest.param(
            Setup(
                list_status=1,
                list_error="ERROR: (gcloud.run.jobs.list) LISTFAIL\nsecond line\nthird line\n",
            ),
            "identity",
            lambda d: d == "ERROR: (gcloud.run.jobs.list) LISTFAIL",
            1,
            id="jobs-list-fails-with-a-multi-line-error",
        ),
        pytest.param(
            Setup(failing_secrets=(MODEL_NAME,)),
            "secrets",
            lambda d: MODEL_NAME in d and HOSTING_NAME not in d,
            1,
            id="second-secret-not-visible",
        ),
        pytest.param(
            Setup(ls_remote_status=128),
            "code",
            lambda d: d != "",
            1,
            id="ls-remote-fails",
        ),
        pytest.param(
            Setup(refs=("refs/heads/other",)),
            "code",
            lambda d: REF in d,
            1,
            id="ref-not-listed",
        ),
    ],
)
def test_each_failing_check_names_its_fault_and_the_others_still_run(
    machine: Machine, setup: Setup, check: str, detail: Callable[[str], bool], failed: int
) -> None:
    result = machine.run(setup)
    lines = check_lines(result.stdout)
    assert [line.name for line in lines] == (NAMES if setup.site_file else ["site file"])
    own = line_of(result.stdout, check)
    assert own.status == "FAIL", result.stdout
    assert detail(own.detail), own.detail
    assert [line.status for line in lines].count("FAIL") == failed, result.stdout
    assert result.stdout.splitlines()[-1] == f"site: {failed} failed"
    assert result.exit_status == 1


def test_two_failures_are_counted(machine: Machine) -> None:
    result = machine.run(Setup(repository="missing", failing_secrets=(HOSTING_NAME,)))
    assert result.stdout.splitlines()[-1] == "site: 2 failed", result.stdout
    assert result.exit_status == 1


@pytest.mark.parametrize(
    ("changes", "status", "host"),
    [
        pytest.param(site(), "ok", "", id="model-covered-code-not"),
        pytest.param(
            site(SITE_CODE_URL="https://code.example.invalid/owner/factory.git"),
            "FAIL",
            "code.example.invalid",
            id="code-host-covered",
        ),
        pytest.param(
            site(SITE_REPOSITORY_URL="https://repo.example.invalid/owner/repo.git"),
            "FAIL",
            "repo.example.invalid",
            id="repository-host-covered",
        ),
        pytest.param(
            site(SITE_API_URL="https://api.example.invalid"),
            "FAIL",
            "api.example.invalid",
            id="api-host-covered",
        ),
        pytest.param(
            site(SITE_MODEL_BASE_URL="https://llm.example.net/v1"),
            "FAIL",
            "llm.example.net",
            id="model-host-not-covered",
        ),
        pytest.param(
            site(
                SITE_NO_PROXY="example.invalid",
                SITE_MODEL_BASE_URL="https://a.b.example.invalid/v1",
            ),
            "ok",
            "",
            id="domain-covers-a-subdomain",
        ),
        pytest.param(
            site(
                SITE_NO_PROXY="example.invalid", SITE_MODEL_BASE_URL="https://badexample.invalid/v1"
            ),
            "FAIL",
            "badexample.invalid",
            id="domain-does-not-cover-a-longer-name",
        ),
        pytest.param(
            site(SITE_MODEL_BASE_URL="https://example.invalid/v1"),
            "ok",
            "",
            id="leading-dot-ignored",
        ),
    ],
)
def test_no_proxy_bypasses_the_model_host_and_never_a_code_host(
    machine: Machine, changes: tuple[tuple[str, str | None], ...], status: str, host: str
) -> None:
    result = machine.run(Setup(changes=changes))
    line = line_of(result.stdout, "no_proxy")
    assert line.status == status, result.stdout
    assert host in line.detail


@pytest.mark.parametrize(
    ("changes", "check", "key", "calls"),
    [
        pytest.param(
            site(SITE_HOSTING_SECRET=None),
            "secrets",
            "SITE_HOSTING_SECRET",
            lambda m: [c for c in m.gcloud_calls() if "secrets" in c],
            id="secrets",
        ),
        pytest.param(
            site(SITE_CODE_URL=None),
            "code",
            "SITE_CODE_URL",
            lambda m: m.ls_remote_calls(),
            id="code",
        ),
        pytest.param(
            site(SITE_REPOSITORY=None),
            "repository",
            "SITE_REPOSITORY",
            lambda m: m.curl_calls(),
            id="repository",
        ),
    ],
)
def test_a_check_without_its_keys_says_what_it_needs_and_does_not_run(
    machine: Machine,
    changes: tuple[tuple[str, str | None], ...],
    check: str,
    key: str,
    calls: Callable[[Machine], list[object]],
) -> None:
    result = machine.run(Setup(changes=changes))
    line = line_of(result.stdout, check)
    assert line.status == "FAIL", result.stdout
    assert line.detail.startswith("needs ")
    assert key in line.detail
    assert calls(machine) == []
    assert line_of(result.stdout, "identity").status == "ok"
    assert any(gcloud_words(call)[:3] == ["run", "jobs", "list"] for call in machine.gcloud_calls())


@pytest.mark.parametrize(
    ("ref", "refs", "status"),
    [
        pytest.param("a" * 40, ("refs/heads/other",), "ok", id="commit-id-of-40"),
        pytest.param("a" * 39, ("refs/heads/other",), "FAIL", id="hex-of-39-is-looked-up"),
        pytest.param("a" * 41, ("refs/heads/other",), "FAIL", id="hex-of-41-is-looked-up"),
        pytest.param("g" * 40, ("refs/heads/other",), "FAIL", id="not-hex-is-looked-up"),
        pytest.param(REF, (f"refs/heads/{REF}",), "ok", id="branch-found"),
        pytest.param(REF, ("refs/heads/other",), "FAIL", id="branch-not-found"),
        pytest.param("v1.2", ("refs/tags/v1.2",), "ok", id="tag-found"),
    ],
)
def test_a_commit_id_is_accepted_without_lookup_and_a_name_must_be_listed(
    machine: Machine, ref: str, refs: tuple[str, ...], status: str
) -> None:
    result = machine.run(Setup(changes=site(SITE_CODE_REF=ref), refs=refs))
    assert line_of(result.stdout, "code").status == status, result.stdout
    if ref == "a" * 40:
        calls = machine.ls_remote_calls()
        assert len(calls) == 1
        operands = [word for word in git_command(calls[0])[1:] if not word.startswith("-")]
        assert operands == [CODE_URL]


def is_read_only_git(command: list[str]) -> bool:
    """Whether the git call is `ls-remote` or one of the local reads."""
    name, rest = command[0], command[1:]
    operands = [word for word in rest if not word.startswith("-")]
    return (
        name in ("ls-remote", "rev-parse")
        or (name == "remote" and rest[:1] == ["get-url"])
        or (name == "config" and ("--get" in rest or rest == operands) and len(operands) == 1)
    )


def test_site_check_makes_no_write(machine: Machine) -> None:
    machine.run()
    for call in machine.gcloud_calls():
        words = gcloud_words(call)
        assert words[:3] in (["run", "jobs", "list"], ["run", "jobs", "describe"]) or words[:2] == [
            "secrets",
            "describe",
        ], call
    for request in machine.curl_calls():
        methods = re.findall(r'^request = "([A-Z]+)"$', str(request["stdin"]), re.MULTILINE)
        assert methods == ["GET"], request
    for git_call in machine.git_calls():
        command = git_command(git_call)
        assert "push" not in command
        assert is_read_only_git(command), command


def test_no_secret_value_is_read_or_printed(machine: Machine) -> None:
    result = machine.run()
    for call in machine.gcloud_calls():
        assert not ("versions" in call and "access" in call), call
    assert MARK not in result.stdout
    assert MARK not in result.stderr


@pytest.mark.parametrize(
    "words",
    [
        pytest.param(("check", "extra"), id="one-argument"),
        pytest.param(("check", "extra", "more"), id="two-arguments"),
    ],
)
def test_an_argument_after_check_prints_the_usage(machine: Machine, words: tuple[str, ...]) -> None:
    result = machine.run(words=words)
    assert result.stderr.splitlines() == ["usage: site check"]
    assert result.exit_status == 2


def test_the_operator_readme_names_every_script_and_library() -> None:
    text = (ROOT / "operator" / "README.md").read_text(encoding="utf-8")
    folders = ["lib", "bin", "job", "skill/kumpel/scripts"]
    files = [path for folder in folders for path in (ROOT / "operator" / folder).iterdir()]
    unnamed = [
        path.name
        for path in files
        if path.is_file() and not re.search(rf"(?<![\w.-]){re.escape(path.name)}(?![\w.-])", text)
    ]
    assert unnamed == []


NOT_FOUND = f"ERROR: (gcloud.run.jobs.describe) Cannot find job [{JOB}].\n"
DENIED = (
    "ERROR: (gcloud.run.jobs.describe) PERMISSION_DENIED: Permission 'run.jobs.get' denied\n"
    "This command is authenticated as deployer@p1.iam.gserviceaccount.com\n"
)
API_NOT_FOUND = f"ERROR: (gcloud.run.jobs.describe) NOT_FOUND: Resource '{JOB}' was not found\n"


@pytest.mark.parametrize(
    ("describe_status", "describe_error", "line"),
    [
        pytest.param(0, "", f"ok job: {JOB} exists", id="exists"),
        pytest.param(1, NOT_FOUND, f"ok job: {JOB} does not exist yet", id="does-not-exist-yet"),
        pytest.param(
            1,
            DENIED,
            f"ok job: {JOB} cannot be read: {DENIED.splitlines()[0]}",
            id="cannot-be-read",
        ),
        pytest.param(1, API_NOT_FOUND, f"ok job: {JOB} does not exist yet", id="api-not-found"),
        pytest.param(
            1,
            "",
            f"ok job: {JOB} cannot be read: gcloud run jobs describe failed",
            id="no-error-text",
        ),
    ],
)
def test_the_job_check_tells_whether_the_job_exists_and_never_fails(
    machine: Machine, describe_status: int, describe_error: str, line: str
) -> None:
    result = machine.run(Setup(describe_status=describe_status, describe_error=describe_error))
    assert line in result.stdout.splitlines()
    assert result.stdout.splitlines()[-1] == "site: ready"
    assert result.exit_status == 0
    describes = [
        call
        for call in machine.gcloud_calls()
        if gcloud_words(call)[:3] == ["run", "jobs", "describe"]
    ]
    assert len(describes) == 1
    assert JOB in describes[0]


def test_ls_remote_runs_through_the_proxy_without_a_credential(machine: Machine) -> None:
    machine.run()
    calls = machine.ls_remote_calls()
    assert len(calls) == 1
    env = calls[0]["env"]
    assert isinstance(env, dict)
    assert env.get("https_proxy") == PROXY
    configuration = {
        name: value for name, value in env.items() if str(name).startswith("GIT_CONFIG_")
    }
    assert not any(
        "extraheader" in str(value).lower() or "authorization" in str(value).lower()
        for value in configuration.values()
    ), configuration
    assert "extraheader" not in " ".join(git_command(calls[0])).lower()
    assert MARK not in json.dumps(calls[0])


@pytest.mark.parametrize(
    ("changes", "flags"),
    [
        pytest.param(
            site(SITE_IMPERSONATE=IMPERSONATE),
            [f"--impersonate-service-account={IMPERSONATE}"],
            id="set",
        ),
        pytest.param(site(), [], id="unset"),
    ],
)
def test_the_identity_check_impersonates_when_the_site_says_so(
    machine: Machine, changes: tuple[tuple[str, str | None], ...], flags: list[str]
) -> None:
    machine.run(Setup(changes=changes))
    lists = [
        call for call in machine.gcloud_calls() if gcloud_words(call)[:3] == ["run", "jobs", "list"]
    ]
    assert len(lists) == 1
    impersonation = [word for word in lists[0] if word.startswith("--impersonate-service-account")]
    assert impersonation == flags


@pytest.mark.parametrize(
    ("changes", "flags"),
    [
        pytest.param(
            site(SITE_IMPERSONATE=IMPERSONATE),
            [f"--impersonate-service-account={IMPERSONATE}"],
            id="set",
        ),
        pytest.param(site(), [], id="unset"),
    ],
)
def test_the_secrets_and_job_checks_impersonate_when_the_site_says_so(
    machine: Machine, changes: tuple[tuple[str, str | None], ...], flags: list[str]
) -> None:
    machine.run(Setup(changes=changes))
    calls = [
        call
        for call in machine.gcloud_calls()
        if gcloud_words(call)[:2] == ["secrets", "describe"]
        or gcloud_words(call)[:3] == ["run", "jobs", "describe"]
    ]
    kinds = sorted(" ".join(gcloud_words(call)[:3]) for call in calls)
    assert kinds == [
        "run jobs describe",
        f"secrets describe {HOSTING_NAME}",
        f"secrets describe {MODEL_NAME}",
    ]
    for call in calls:
        impersonation = [word for word in call if word.startswith("--impersonate-service-account")]
        assert impersonation == flags, call


@pytest.mark.parametrize(
    ("checkout", "status", "detail"),
    [
        pytest.param(
            "no origin",
            "FAIL",
            lambda d: "origin" in d and ("no origin" in d or "missing" in d),
            id="no-origin",
        ),
        pytest.param("scp origin", "ok", lambda d: d == "", id="scp-form"),
        pytest.param("origin without .git", "ok", lambda d: d == "", id="without-dot-git"),
        pytest.param("lookalike origin", "FAIL", lambda d: d != "", id="lookalike-owner"),
    ],
)
def test_the_checkout_check_reads_the_origin_url(
    machine: Machine, checkout: str, status: str, detail: Callable[[str], bool]
) -> None:
    result = machine.run(Setup(checkout=checkout))
    line = line_of(result.stdout, "checkout")
    assert line.status == status, result.stdout
    assert detail(line.detail), line.detail


def test_the_tools_check_names_every_missing_tool(machine: Machine) -> None:
    result = machine.run(Setup(missing=frozenset({"gcloud", "curl"})))
    line = line_of(result.stdout, "tools")
    assert line.status == "FAIL"
    assert "gcloud" in line.detail
    assert "curl" in line.detail


def test_the_guide_names_every_key_of_the_example_site_file() -> None:
    text = (ROOT / "docs" / "operator-guide" / "site.md").read_text(encoding="utf-8")
    assert [key for key in example_keys() if not re.search(rf"\b{key}\b", text)] == []
