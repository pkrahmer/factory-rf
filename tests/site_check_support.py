"""The operator's `site check` on a machine in `tmp_path`: its site, its stand-ins, its lines."""

import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NamedTuple

from factory.shared.adapters.process import ProcessResult
from git_support import run_git, write_executable
from operator_support import CURL_STAND_IN, make_work_tree, operator_environment, run_site
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
    sys.stderr.write(answers["describe_error"])
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
    describe_error: str = ""
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


def link_system(folder: Path) -> Path:
    """Fill `folder` with links to the machine's programs, without those the stand-ins replace."""
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
