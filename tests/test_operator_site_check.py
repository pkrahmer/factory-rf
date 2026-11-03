"""The operator's `site check`: read-only checks of a machine's setup, one line each."""

import json
import os
import re
import shutil
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NamedTuple

import pytest

from factory.adapters.process import ProcessResult
from git_support import run_git, write_executable
from operator_support import (
    CURL_STAND_IN,
    ROOT,
    example_keys,
    make_work_tree,
    operator_environment,
    run_site,
)
from recording_stand_in_support import read_records

NAMES = [
    "site file",
    "keys",
    "tools",
    "token",
    "repository",
    "checkout",
    "identity",
    "secrets",
    "code",
    "no_proxy",
    "job",
]
REPOSITORY = "owner/repo"
JOB = "factory-job"
REF = "release-7"
PROXY = "http://proxy.example.net:3128"
HOSTING_NAME = "hosting-sm"
MODEL_NAME = "model-sm"
IMPERSONATE = "deployer@p1.iam.gserviceaccount.com"
REPOSITORY_URL = f"https://repo.example.net/{REPOSITORY}.git"
CODE_URL = "https://code.example.net/owner/factory.git"
NO_ACCESS = "hosting: the token command failed; see SITE_TOKEN_CMD in the site file"
# The command builds the token, so its text is in no file the test writes.
MARK_COMMAND = "printf 'MARK%s\\n' MARK"
MARK = "TOKENMARK"
# A token command that succeeds and prints nothing.
SILENT_COMMAND = "true"
# The `origin` url of each kind of checkout that is a work tree; `None` adds no origin.
ORIGINS: dict[str, str | None] = {
    "work tree": REPOSITORY_URL,
    "other origin": "https://repo.example.net/owner/other.git",
    "no origin": None,
    "scp origin": f"git@repo.example.net:{REPOSITORY}.git",
    "origin without .git": f"https://repo.example.net/{REPOSITORY}",
    "lookalike origin": f"https://repo.example.net/x{REPOSITORY}.git",
}
# Every value the job and the hosting client need, with no SITE_RESET_REPOSITORY among them.
SITE: dict[str, str] = {
    "SITE_PROJECT": "p1",
    "SITE_REGION": "europe-west3",
    "SITE_RUN_AS": "runner@p1.iam.gserviceaccount.com",
    "SITE_CONNECTOR": "conn-1",
    "SITE_PROXY": PROXY,
    "SITE_NO_PROXY": ".example.invalid",
    "SITE_JOB": JOB,
    "SITE_INSTANCE": "inst-x",
    "SITE_REPOSITORY_URL": REPOSITORY_URL,
    "SITE_CODE_URL": CODE_URL,
    "SITE_CODE_REF": REF,
    "SITE_HOSTING_SECRET": HOSTING_NAME,
    "SITE_MODEL_SECRET": MODEL_NAME,
    "SITE_MODEL_BASE_URL": "https://llm.example.invalid/v1",
    "SITE_MODEL": "big-model",
    "SITE_LOGIN_URL": "https://login.example.invalid/token",
    "SITE_LOGIN_SCOPE": "api://llm/.default",
    "SITE_LOGIN_CLIENT_ID": "client-1",
    "SITE_REPOSITORY": REPOSITORY,
    "SITE_API_URL": "https://api.example.net",
    "SITE_TOKEN_CMD": MARK_COMMAND,
}
# The programs a run finds only as the test's stand-ins, or not at all.
HIDDEN = frozenset({"gcloud", "curl", "git", "python3", "gh"})

# A stand-in for gcloud: it records its arguments and answers as the answers file says;
# `secrets versions access` prints a value, which the test then finds in the record.
GCLOUD_STAND_IN = r"""
import json, sys

arguments = sys.argv[1:]
with open(RECORD, "a", encoding="utf-8") as record:
    record.write(json.dumps(arguments) + "\n")
with open(ANSWERS, encoding="utf-8") as source:
    answers = json.load(source)
words = [word for word in arguments if not word.startswith("-")]
if "versions" in words and "access" in words:
    print("SECRETVALUE")
elif words[:3] == ["run", "jobs", "list"]:
    sys.stderr.write(answers["list_error"])
    sys.exit(answers["list_status"])
elif words[:3] == ["run", "jobs", "describe"]:
    sys.exit(answers["describe_status"])
elif words[:2] == ["secrets", "describe"]:
    name = words[2] if len(words) > 2 else ""
    if name in answers["failing_secrets"]:
        sys.stderr.write(f"ERROR: (gcloud.secrets.describe) Secret [{name}] not found.\n")
        sys.exit(1)
    print(f"name: projects/p1/secrets/{name}")
"""

# A stand-in for git: it records its arguments and its environment, answers `ls-remote` from the
# answers file (patterns, --heads, --tags and --exit-code as git reads them) and hands every
# other call to the real git.
GIT_STAND_IN = r"""
import json, os, sys

arguments = sys.argv[1:]
with open(RECORD, "a", encoding="utf-8") as record:
    record.write(json.dumps({"argv": arguments, "env": dict(os.environ)}) + "\n")
if "ls-remote" in arguments:
    with open(ANSWERS, encoding="utf-8") as source:
        answers = json.load(source)
    if answers["ls_remote_status"]:
        sys.stderr.write("fatal: unable to access the code host\n")
        sys.exit(answers["ls_remote_status"])
    rest = arguments[arguments.index("ls-remote") + 1 :]
    patterns = [word for word in rest if not word.startswith("-")][1:]
    flags = (("--heads", "refs/heads/"), ("--tags", "refs/tags/"))
    kinds = [kind for flag, kind in flags if flag in rest]
    listed = [
        ref
        for ref in answers["refs"]
        if (not kinds or ref.startswith(tuple(kinds)))
        and (not patterns or any(ref == p or ref.endswith("/" + p) for p in patterns))
    ]
    for ref in listed:
        print("a" * 40 + "\t" + ref)
    sys.exit(2 if "--exit-code" in rest and not listed else 0)
os.execv(REAL, [REAL, *arguments])
"""


@dataclass(frozen=True)
class Setup:
    """A machine's state: the site's changes, the missing programs and the stand-ins' answers."""

    changes: tuple[tuple[str, str | None], ...] = ()
    site_file: bool = True
    missing: frozenset[str] = frozenset()
    checkout: str = "work tree"
    repository: str = "push"
    list_status: int = 0
    list_error: str = ""
    failing_secrets: tuple[str, ...] = ()
    describe_status: int = 0
    ls_remote_status: int = 0
    refs: tuple[str, ...] = (f"refs/heads/{REF}",)

    def answers(self) -> str:
        """The stand-ins' answers as JSON."""
        answers = asdict(self)
        for name in ("changes", "site_file", "missing", "checkout", "repository"):
            del answers[name]
        return json.dumps(answers)


class CheckLine(NamedTuple):
    """One check's line: `ok` or `FAIL`, the check's name and the text after `: `."""

    status: str
    name: str
    detail: str


class Machine:
    """An operator's machine in `tmp_path`: the site file, the checkout and the stand-ins."""

    def __init__(self, tmp_path: Path, system: Path) -> None:
        self.root = tmp_path
        self.system = system
        self.records = tmp_path / "records"
        self.records.mkdir()
        self.site_file = tmp_path / "site" / "site.env"

    def run(self, setup: Setup | None = None, words: tuple[str, ...] = ("check",)) -> ProcessResult:
        """Build the machine as `setup` says and run `site` with `words`."""
        setup = setup or Setup()
        checkout = self._checkout(setup.checkout)
        if setup.site_file:
            values: dict[str, str | None] = {**SITE, "SITE_CHECKOUT": str(checkout)}
            values.update(dict(setup.changes))
            self.site_file.parent.mkdir()
            text = "".join(f"{key}={value}\n" for key, value in values.items() if value is not None)
            self.site_file.write_text(text, encoding="utf-8")
        answers = self.records / "answers.json"
        answers.write_text(setup.answers(), encoding="utf-8")
        routes = self.records / "routes.json"
        body = {"full_name": REPOSITORY, "permissions": {"push": setup.repository == "push"}}
        found = {} if setup.repository == "missing" else {f"/repos/{REPOSITORY}": json.dumps(body)}
        routes.write_text(json.dumps(found), encoding="utf-8")
        folder = self._stand_ins(setup.missing, answers, routes)
        temporary = self.root / "tmp"
        temporary.mkdir()
        env = {
            **operator_environment(self.root),
            "PATH": os.pathsep.join([str(folder), str(self.system)]),
            "FACTORY_SITE": str(self.site_file),
            "TMPDIR": str(temporary),
            "GIT_CONFIG_NOSYSTEM": "1",
        }
        return run_site(list(words), self.root, env)

    def gcloud_calls(self) -> list[list[str]]:
        """The argument lists `gcloud` was called with, in order."""
        return read_records(self.records / "gcloud.jsonl")

    def git_calls(self) -> list[dict[str, object]]:
        """The calls of `git`, each with its `argv` and its `env`, in order."""
        return read_records(self.records / "git.jsonl")

    def curl_calls(self) -> list[dict[str, object]]:
        """The calls of `curl`, each with its `argv` and its `stdin`, in order."""
        return read_records(self.records / "curl.jsonl")

    def ls_remote_calls(self) -> list[dict[str, object]]:
        """The calls of `git ls-remote`."""
        return [call for call in self.git_calls() if git_command(call)[0] == "ls-remote"]

    def _checkout(self, kind: str) -> Path:
        if kind == "plain":
            folder = self.root / "plain"
            folder.mkdir()
            return folder
        folder = make_work_tree(self.root / "checkout")
        url = ORIGINS[kind]
        if url is not None:
            run_git(folder, "remote", "add", "origin", url)
        return folder

    def _stand_ins(self, missing: frozenset[str], answers: Path, routes: Path) -> Path:
        folder = self.root / "bin"
        folder.mkdir()
        real_git = shutil.which("git")
        assert real_git is not None
        programs = {
            "gcloud": header(RECORD=self.records / "gcloud.jsonl", ANSWERS=answers)
            + GCLOUD_STAND_IN,
            "git": header(RECORD=self.records / "git.jsonl", ANSWERS=answers, REAL=real_git)
            + GIT_STAND_IN,
            "curl": "import os\n"
            + "os.environ.update("
            + repr(
                {
                    "STAND_IN_RECORD": str(self.records / "curl.jsonl"),
                    "STAND_IN_CURL_ROUTES": str(routes),
                }
            )
            + ")\n"
            + CURL_STAND_IN,
        }
        for name, body in programs.items():
            if name not in missing:
                write_executable(folder, body, name=name)
        python = shutil.which("python3")
        assert python is not None
        if "python3" not in missing:
            (folder / "python3").symlink_to(python)
        return folder


def header(**names: object) -> str:
    """Python assignments of the stand-in's own constants, one a line."""
    return "".join(f"{name} = {str(value)!r}\n" for name, value in names.items())


def gcloud_words(call: list[str]) -> list[str]:
    """The words of a gcloud call that are no flag, in order."""
    return [word for word in call if not word.startswith("-")]


def git_command(call: dict[str, object]) -> list[str]:
    """The words of a git call from its subcommand on, past git's own options."""
    argv = call["argv"]
    assert isinstance(argv, list)
    arguments = [str(word) for word in argv]
    while arguments and arguments[0].startswith("-"):
        arguments = arguments[2:] if arguments[0] in ("-C", "-c") else arguments[1:]
    return arguments or [""]


def check_lines(stdout: str) -> list[CheckLine]:
    """The check lines of the output, every line but the last."""
    return [parse(line) for line in stdout.splitlines()[:-1]]


def parse(line: str) -> CheckLine:
    """The line's status, check name and detail."""
    status, _, rest = line.partition(" ")
    for name in NAMES:
        if rest == name:
            return CheckLine(status, name, "")
        if rest.startswith(f"{name}: "):
            return CheckLine(status, name, rest.removeprefix(f"{name}: "))
    raise AssertionError(f"not a check line: {line!r}")


def line_of(stdout: str, name: str) -> CheckLine:
    """The one line of the check `name`."""
    lines = [line for line in check_lines(stdout) if line.name == name]
    assert len(lines) == 1, stdout
    return lines[0]


def site(**changes: str | None) -> tuple[tuple[str, str | None], ...]:
    """The site's changes; `None` removes the key."""
    return tuple(changes.items())


@pytest.fixture(scope="module")
def system(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A folder of links to the machine's programs, without those the stand-ins replace."""
    folder = tmp_path_factory.mktemp("system")
    for entry in os.environ["PATH"].split(os.pathsep):
        directory = Path(entry)
        if not directory.is_dir():
            continue
        for program in sorted(directory.iterdir()):
            link = folder / program.name
            if program.name in HIDDEN or os.path.lexists(link):
                continue
            if program.is_file() and os.access(program, os.X_OK):
                link.symlink_to(program)
    return folder


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


@pytest.mark.parametrize(
    ("describe_status", "line"),
    [
        pytest.param(0, f"ok job: {JOB} exists", id="exists"),
        pytest.param(1, f"ok job: {JOB} does not exist yet", id="does-not-exist-yet"),
    ],
)
def test_the_job_check_tells_whether_the_job_exists_and_never_fails(
    machine: Machine, describe_status: int, line: str
) -> None:
    result = machine.run(Setup(describe_status=describe_status))
    assert line in result.stdout.splitlines()
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
    text = (ROOT / "docs" / "operator-guide.md").read_text(encoding="utf-8")
    assert [key for key in example_keys() if not re.search(rf"\b{key}\b", text)] == []
