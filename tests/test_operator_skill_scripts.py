"""The operator's skill scripts: the factory's state through the hosting client and the site."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from factory.adapters.process import ProcessResult
from git_support import clone, commit_all, run_git, write_executable, write_files
from operator_support import CURL_STAND_IN, ROOT, hosting_env, run_script

SCRIPTS = ROOT / "operator" / "skill" / "kumpel" / "scripts"
REPOSITORY = "owner/repo"
PREFIX = f"/repos/{REPOSITORY}"
API_URL = "https://api.example.invalid"
# The command builds the token, so its text is in no file the test writes.
ACCESS_COMMAND = "printf 'tok%s\\n' 123"
NO_ACCESS = "hosting: the token command failed; see SITE_TOKEN_CMD in the site file"
GIT_VARIABLES = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_AUTHOR_NAME": "Operator",
    "GIT_AUTHOR_EMAIL": "operator@example.invalid",
    "GIT_COMMITTER_NAME": "Operator",
    "GIT_COMMITTER_EMAIL": "operator@example.invalid",
}
DEFAULT_SWITCHES = {"merge": False, "answer": True, "start_next": True}
FEATURE = "factory/features/F0001-example"
ITEM = f"{FEATURE}/in-progress/F0001-S0001-first.md"
BRANCH = "work-item/F0001-S0001"
STORY = (
    "# First story\n\n## Smoke test\n\nExpect: one line, `0`.\n\n## Journal\n\n1. human: created.\n"
)
STORY_ON_BRANCH = STORY + (
    "2. smoke-tester: Met its expectations.\n3. reviewer: Findings: none.\n   - all clear\n"
)
JOURNAL_HEADER = (
    "== what the journal says about the smoke test, the findings and the leaves (" + ITEM + ")"
)
LAST_ENTRY_HEADER = "== the journal's last entry"
OLD_TEST = "def test_old() -> None:\n    pass\n"


@dataclass(frozen=True)
class Operator:
    """The operator's machine in `tmp_path`: a site file, the `curl` stand-in and a checkout."""

    tmp_path: Path
    site_file: Path
    records: Path
    temporary: Path
    bin_folder: Path
    routes_file: Path
    settings_file: Path
    checkout: Path

    def write_site(self, **values: str) -> None:
        """Write the site file with exactly `values`."""
        lines = [f"{name}={value}\n" for name, value in values.items()]
        self.site_file.write_text("# the site of a test\n" + "".join(lines), encoding="utf-8")

    def answer(self, routes: dict[str, object]) -> None:
        """Let the `curl` stand-in answer each path (with or without its query) with its JSON."""
        bodies = {route: json.dumps(value) for route, value in routes.items()}
        self.routes_file.write_text(json.dumps(bodies), encoding="utf-8")

    def run(self, script: str, *arguments: str) -> ProcessResult:
        """Run the skill's `script` with `arguments` on this machine."""
        env = hosting_env(
            self.tmp_path,
            self.site_file,
            self.records,
            self.temporary,
            self.bin_folder,
            STAND_IN_CURL_ROUTES=str(self.routes_file),
            KUMPEL_SETTINGS=str(self.settings_file),
            **GIT_VARIABLES,
        )
        return run_script([str(SCRIPTS / script), *arguments], self.tmp_path, env)

    def urls(self) -> list[str]:
        """The path and query of every URL the `curl` stand-in was asked for, in order."""
        path = self.records / "curl.jsonl"
        if not path.exists():
            return []
        found = []
        for line in path.read_text(encoding="utf-8").splitlines():
            configuration = str(json.loads(line)["stdin"])
            match = re.search(r'^url = "([^"]*)"$', configuration, re.MULTILINE)
            if match:
                found.append(match.group(1).removeprefix(API_URL))
        return found


@pytest.fixture
def operator(tmp_path: Path) -> Operator:
    """The operator's machine with a full site file (a token command, no `gh`) and no answers."""
    folders = {name: tmp_path / name for name in ("site", "records", "tmp", "bin")}
    for folder in folders.values():
        folder.mkdir()
    write_executable(folders["bin"], CURL_STAND_IN, name="curl")
    machine = Operator(
        tmp_path=tmp_path,
        site_file=folders["site"] / "site.env",
        records=folders["records"],
        temporary=folders["tmp"],
        bin_folder=folders["bin"],
        routes_file=tmp_path / "routes.json",
        settings_file=tmp_path / "settings" / "settings.json",
        checkout=tmp_path / "checkout",
    )
    machine.write_site(
        SITE_REPOSITORY=REPOSITORY,
        SITE_CHECKOUT=str(machine.checkout),
        SITE_API_URL=API_URL,
        SITE_TOKEN_CMD=ACCESS_COMMAND,
    )
    machine.answer({})
    return machine


def make_bare_remote(root: Path, files: dict[str, str]) -> tuple[Path, Path]:
    """A bare remote `root/remote.git` whose `main` holds `files`, and the seed that pushes."""
    root.mkdir(parents=True, exist_ok=True)
    run_git(root, "init", "-q", "--initial-branch=main", "seed")
    seed = root / "seed"
    write_files(seed, files)
    commit_all(seed, "seed")
    run_git(root, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
    remote = root / "remote.git"
    run_git(seed, "remote", "add", "origin", str(remote))
    run_git(seed, "push", "-q", "origin", "main")
    return remote, seed


def push_branch(seed: Path, branch: str, files: dict[str, str]) -> None:
    """Commit `files` on `branch` in the seed clone and push it."""
    run_git(seed, "checkout", "-q", "-B", branch)
    write_files(seed, files)
    commit_all(seed, f"{branch}: work")
    run_git(seed, "push", "-q", "origin", branch)


def pull(number: int, branch: str, labels: list[str]) -> dict[str, object]:
    """One pull request as the API lists it."""
    return {
        "number": number,
        "state": "open",
        "head": {"ref": branch},
        "labels": [{"name": name} for name in labels],
    }


def comment_routes(number: int, bodies: list[str]) -> dict[str, object]:
    """The issue of pull request `number` with its comment count, and its newest comment."""
    routes: dict[str, object] = {
        f"{PREFIX}/issues/{number}": {"number": number, "comments": len(bodies)}
    }
    if bodies:
        page = f"{PREFIX}/issues/{number}/comments?per_page=1&page={len(bodies)}"
        routes[page] = [{"id": len(bodies), "body": bodies[-1]}]
    return routes


def commits(*messages: str) -> dict[str, object]:
    """The route of the newest commits on `main`, newest first."""
    return {f"{PREFIX}/commits?per_page=20": [{"commit": {"message": text}} for text in messages]}


ARCHIVE = "work item F0001-S0000: merged, archived"


def status_routes(
    pulls: list[dict[str, object]], bodies: dict[int, list[str]]
) -> dict[str, object]:
    """The answers `status.sh` needs: the open pull requests, their comments, the commits."""
    routes: dict[str, object] = {f"{PREFIX}/pulls?state=open&per_page=50": pulls}
    for number, texts in bodies.items():
        routes.update(comment_routes(number, texts))
    routes.update(commits(ARCHIVE))
    return routes


def sections(stdout: str) -> dict[str, list[str]]:
    """The output of `approval.sh` by its `== ` headers, each with the lines under it."""
    found: dict[str, list[str]] = {}
    current: list[str] = []
    for line in stdout.splitlines():
        if line.startswith("== "):
            current = found.setdefault(line, [])
        else:
            current.append(line)
    return found


def section(stdout: str, prefix: str) -> list[str]:
    """The lines under the one header of `approval.sh` that starts with `prefix`."""
    matches = [lines for header, lines in sections(stdout).items() if header.startswith(prefix)]
    assert len(matches) == 1, stdout
    return matches[0]


def test_status_lists_the_open_work_items_and_the_last_archive(operator: Operator) -> None:
    operator.answer(
        status_routes(
            [
                pull(7, "work-item/F0001-S0001", ["stage:doing"]),
                pull(8, "feature/something", ["stage:doing"]),
                pull(9, "work-item/F0001-S0002", ["stage:approval"]),
            ],
            {7: ["Looks good to me."], 8: [], 9: []},
        )
    )
    result = operator.run("status.sh")
    assert result.exit_status == 0, result.stderr
    assert result.stdout == (
        "#7 F0001-S0001 stage:doing working\n"
        "#9 F0001-S0002 stage:approval waits: approval\n"
        f"last archive: {ARCHIVE}\n"
    )


def marker(kind: str) -> str:
    """A comment of the factory whose marker is of `kind`."""
    return f"The factory waits.\n\n<!-- factory key=abc:{kind}:1 -->"


VERDICT = "Verdict: approve.\n\n<!-- kumpel verdict -->"


@pytest.mark.parametrize(
    ("stage", "bodies", "state"),
    [
        *(
            pytest.param("stage:doing", [marker(kind)], f"waits: {kind}", id=kind)
            for kind in (
                "question",
                "attempts_cap",
                "round_cap",
                "crash_cap",
                "stall",
                "expiry",
                "error",
            )
        ),
        pytest.param("stage:doing", [VERDICT], "verdict posted", id="verdict"),
        pytest.param(
            "stage:doing",
            ["Verdict: approve.\n<!-- kumpel verdict -->\none\ntwo\nthree"],
            "working",
            id="verdict-fourth-from-the-end",
        ),
        pytest.param("stage:doing", [], "working", id="no-comments"),
        pytest.param("stage:approval", [], "waits: approval", id="no-comments-at-approval"),
        pytest.param(
            "stage:doing",
            ["Both.\n<!-- kumpel verdict -->\n<!-- factory key=abc:question:1 -->"],
            "waits: question",
            id="marker-and-verdict",
        ),
        pytest.param(
            "stage:approval", [marker("question")], "waits: question", id="marker-at-approval"
        ),
        pytest.param("stage:approval", [VERDICT], "verdict posted", id="verdict-at-approval"),
        pytest.param("stage:doing", [marker("merged")], "working", id="unknown-kind"),
    ],
)
def test_the_newest_comment_decides_the_state(
    operator: Operator, stage: str, bodies: list[str], state: str
) -> None:
    operator.answer(
        status_routes(
            [pull(7, "work-item/F0001-S0001", [stage])],
            {7: ["Earlier.", *bodies] if bodies else []},
        )
    )
    result = operator.run("status.sh")
    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines()[0] == f"#7 F0001-S0001 {stage} {state}"


def test_a_pull_request_without_stage_label_and_many_comments(operator: Operator) -> None:
    bodies = [f"Comment {number}." for number in range(1, 26)]
    operator.answer(status_routes([pull(7, "work-item/F0001-S0001", ["needs-care"])], {7: bodies}))
    result = operator.run("status.sh")
    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines()[0] == "#7 F0001-S0001 stage:? working"
    assert f"{PREFIX}/issues/7/comments?per_page=1&page=25" in operator.urls()


@pytest.mark.parametrize(
    ("messages", "line"),
    [
        pytest.param(
            [
                "work item F0001-S0003: merged, archived later",
                "a work item F0001-S0003: merged, archived",
                "work item F0001-S0002: merged, archived\n\nThe body.",
                "work item F0001-S0001: merged, archived",
            ],
            "last archive: work item F0001-S0002: merged, archived",
            id="newest-archive",
        ),
        pytest.param(
            ["F0001-S0002: start", "work item F0001-S0001: approved"],
            "last archive: no archive commit in the last 20",
            id="no-archive",
        ),
    ],
)
def test_the_last_archive_is_the_newest_archive_subject(
    operator: Operator, messages: list[str], line: str
) -> None:
    routes = status_routes([], {})
    routes.update(commits(*messages))
    operator.answer(routes)
    result = operator.run("status.sh")
    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines() == [line]


@dataclass(frozen=True)
class Approval:
    """A bare remote with a work item's branch, the operator's checkout and the seed that pushes."""

    remote: Path
    seed: Path


MAIN_FILES = {
    "README.md": "# Project\n",
    "tests/test_old.py": OLD_TEST,
    f"{FEATURE}/feature.md": "# Example feature\n",
    ITEM: STORY,
}
BRANCH_FILES = {
    "tests/test_new.py": "def test_new() -> None:\n    pass\n",
    "tests/test_old.py": OLD_TEST + "\n\ndef test_older() -> None:\n    pass\n",
    ITEM: STORY_ON_BRANCH,
}
COST_TABLE = ":cost_table:\n| stage | cost |\n|---|---|\n| doing | $1.00 |\n| **total** | $2.50 |\n"


def approval_routes(comments: list[str]) -> dict[str, object]:
    """The answers `approval.sh 4` needs: the changed files and the comments of the pull request."""
    return {
        f"{PREFIX}/pulls/4/files?per_page=100": [
            {"filename": name} for name in ("tests/test_old.py", "README.md", "tests/test_new.py")
        ],
        f"{PREFIX}/issues/4/comments": [
            {"id": number, "body": body} for number, body in enumerate(comments, 1)
        ],
    }


@pytest.fixture
def approval(operator: Operator) -> Approval:
    """A remote whose branch `work-item/F0001-S0001` changes tests and the story; its checkout."""
    remote, seed = make_bare_remote(operator.tmp_path / "hosting", MAIN_FILES)
    push_branch(seed, BRANCH, BRANCH_FILES)
    clone(remote, operator.checkout)
    operator.answer(approval_routes([]))
    return Approval(remote=remote, seed=seed)


@pytest.mark.parametrize(
    ("comments", "cost"),
    [
        pytest.param(
            [
                ":cost_table:\n| **total** | $1.00 |\n",
                "A comment of the human.",
                COST_TABLE,
                "A later comment.",
            ],
            ["| **total** | $2.50 |"],
            id="newest-table",
        ),
        pytest.param(["A comment of the human."], ["no cost table yet"], id="no-table"),
    ],
)
@pytest.mark.usefixtures("approval")
def test_approval_prints_the_files_and_the_cost_from_the_api(
    operator: Operator, comments: list[str], cost: list[str]
) -> None:
    operator.answer(approval_routes(comments))
    result = operator.run("approval.sh", "4", "F0001-S0001")
    assert result.exit_status == 0, result.stderr
    assert section(result.stdout, "== files") == [
        "tests/test_old.py",
        "README.md",
        "tests/test_new.py",
    ]
    assert section(result.stdout, "== cost") == cost


@pytest.mark.parametrize(
    ("extra", "markers"),
    [
        pytest.param(
            {"src/thing.py": "x = 1  # noqa: E501\n"}, ["2:+x = 1  # noqa: E501"], id="marker"
        ),
        pytest.param({}, ["none"], id="no-marker"),
    ],
)
def test_approval_prints_the_git_sections_from_the_checkout(
    operator: Operator, approval: Approval, extra: dict[str, str], markers: list[str]
) -> None:
    if extra:
        push_branch(approval.seed, BRANCH, extra)
    result = operator.run("approval.sh", "4", "F0001-S0001")
    assert result.exit_status == 0, result.stderr
    assert section(result.stdout, "== tests changed") == [
        "A\ttests/test_new.py",
        "M\ttests/test_old.py",
    ]
    assert section(result.stdout, "== Expect lines") == ["5:Expect: one line, `0`."]
    assert section(result.stdout, "== new markers") == markers


@pytest.mark.usefixtures("approval")
def test_approval_prints_the_journal_sections(operator: Operator) -> None:
    result = operator.run("approval.sh", "4", "F0001-S0001")
    assert result.exit_status == 0, result.stderr
    found = sections(result.stdout)
    assert LAST_ENTRY_HEADER in found
    assert JOURNAL_HEADER in found
    lines = found[JOURNAL_HEADER]
    assert any("Met" in line for line in lines), lines
    assert any("Findings" in line for line in lines), lines


def test_approval_reads_the_branch_as_the_remote_holds_it(
    operator: Operator, approval: Approval
) -> None:
    push_branch(
        approval.seed, BRANCH, {"tests/test_late.py": "def test_late() -> None:\n    pass\n"}
    )
    result = operator.run("approval.sh", "4", "F0001-S0001")
    assert result.exit_status == 0, result.stderr
    assert "A\ttests/test_late.py" in section(result.stdout, "== tests changed")


@pytest.mark.usefixtures("approval")
def test_the_scripts_ask_with_the_query_strings_of_the_interface(operator: Operator) -> None:
    routes = status_routes([pull(7, "work-item/F0001-S0001", ["stage:doing"])], {7: ["Hello."]})
    routes.update(approval_routes([COST_TABLE]))
    operator.answer(routes)
    for script, arguments in (("status.sh", []), ("approval.sh", ["4", "F0001-S0001"])):
        result = operator.run(script, *arguments)
        assert result.exit_status == 0, result.stderr
    urls = operator.urls()
    assert f"{PREFIX}/pulls?state=open&per_page=50" in urls
    assert any(url.startswith(f"{PREFIX}/commits?") and "per_page=20" in url for url in urls), urls
    comments = [url for url in urls if url.startswith(f"{PREFIX}/issues/4/comments")]
    assert comments, urls
    assert all("per_page=100" in url for url in comments), comments


SITE_CHECKOUT = "/site/checkout"
JSON_SETTINGS = {
    "repository": "json/repo",
    "checkout": "/json/checkout",
    "switches": DEFAULT_SWITCHES,
}


@pytest.mark.parametrize(
    ("site", "json_file", "words", "status", "stdout"),
    [
        pytest.param(
            True, False, ["get", "repository"], 0, f"{REPOSITORY}\n", id="site-repository"
        ),
        pytest.param(True, False, ["get", "checkout"], 0, f"{SITE_CHECKOUT}\n", id="site-checkout"),
        pytest.param(False, True, ["get", "repository"], 0, "json/repo\n", id="json-repository"),
        pytest.param(False, True, ["get", "checkout"], 0, "/json/checkout\n", id="json-checkout"),
        pytest.param(
            True, True, ["get", "repository"], 0, f"{REPOSITORY}\n", id="site-wins-repository"
        ),
        pytest.param(
            True, True, ["get", "checkout"], 0, f"{SITE_CHECKOUT}\n", id="site-wins-checkout"
        ),
        pytest.param(
            True,
            True,
            ["show"],
            0,
            f"repository {REPOSITORY}, checkout {SITE_CHECKOUT}\n"
            "switches: merge off, answer on, start_next on\n",
            id="show-site-wins",
        ),
        pytest.param(False, False, ["show"], 1, None, id="show-neither"),
        pytest.param(False, False, ["get", "repository"], None, None, id="get-neither"),
    ],
)
def test_settings_answer_the_repository_and_checkout_from_the_site_first(
    *,
    operator: Operator,
    site: bool,
    json_file: bool,
    words: list[str],
    status: int | None,
    stdout: str | None,
) -> None:
    values = {"SITE_REPOSITORY": REPOSITORY, "SITE_CHECKOUT": SITE_CHECKOUT} if site else {}
    operator.write_site(SITE_API_URL=API_URL, SITE_TOKEN_CMD=ACCESS_COMMAND, **values)
    if json_file:
        operator.settings_file.parent.mkdir(parents=True)
        operator.settings_file.write_text(json.dumps(JSON_SETTINGS), encoding="utf-8")
    if status == 1 and stdout is None:
        stdout = (
            f"no settings at {operator.settings_file}; "
            "run: settings.sh init <owner/name> <checkout>\n"
        )
    result = operator.run("settings.sh", *words)
    if status is None:
        assert result.exit_status != 0, result.stdout
    else:
        assert result.exit_status == status, result.stderr
    if stdout is not None:
        assert result.stdout == stdout


@pytest.mark.parametrize(
    ("site", "arguments", "status", "stderr", "written"),
    [
        pytest.param(
            {"SITE_REPOSITORY": REPOSITORY, "SITE_CHECKOUT": SITE_CHECKOUT},
            [],
            0,
            "",
            {"switches": DEFAULT_SWITCHES},
            id="site-gives-both",
        ),
        pytest.param(
            {},
            [],
            2,
            "usage: settings.sh init <owner/name> <checkout>\n",
            None,
            id="site-gives-neither",
        ),
        pytest.param(
            {"SITE_REPOSITORY": REPOSITORY},
            [],
            2,
            "usage: settings.sh init <owner/name> <checkout>\n",
            None,
            id="site-gives-only-the-repository",
        ),
        pytest.param(
            {},
            [REPOSITORY, "/path"],
            0,
            "",
            {"repository": REPOSITORY, "checkout": "/path", "switches": DEFAULT_SWITCHES},
            id="arguments",
        ),
    ],
)
def test_settings_init_needs_no_arguments_when_the_site_gives_both(
    *,
    operator: Operator,
    site: dict[str, str],
    arguments: list[str],
    status: int,
    stderr: str,
    written: dict[str, object] | None,
) -> None:
    operator.write_site(SITE_API_URL=API_URL, SITE_TOKEN_CMD=ACCESS_COMMAND, **site)
    result = operator.run("settings.sh", "init", *arguments)
    assert (result.exit_status, result.stderr) == (status, stderr)
    if written is not None:
        data = json.loads(operator.settings_file.read_text(encoding="utf-8"))
        assert data == written
    if arguments:
        assert result.stdout == f"settings written: {operator.settings_file}\n"


@pytest.mark.parametrize("faulty", [False, True], ids=["no-site-file", "faulty-site-file"])
def test_settings_answer_from_the_json_file_without_a_usable_site_file(
    operator: Operator, faulty: bool
) -> None:
    operator.settings_file.parent.mkdir(parents=True)
    operator.settings_file.write_text(json.dumps(JSON_SETTINGS), encoding="utf-8")
    if faulty:
        operator.site_file.write_text("not a pair\n", encoding="utf-8")
    else:
        operator.site_file.unlink()
    result = operator.run("settings.sh", "get", "repository")
    assert (result.exit_status, result.stdout) == (0, "json/repo\n"), result.stderr
    if faulty:
        assert f"site: {operator.site_file}:1: not a KEY=value line" in result.stderr.splitlines()


STARTING_FILES = {
    "README.md": "# Project\n",
    f"{FEATURE}/feature.md": "# Example feature\n",
    f"{FEATURE}/backlog/F0001-S0003-third.md": "# Third story\n",
}


@pytest.fixture
def remote(operator: Operator) -> Path:
    """A bare remote whose `main` holds a story in its backlog, cloned as the checkout."""
    bare, _seed = make_bare_remote(operator.tmp_path / "hosting", STARTING_FILES)
    clone(bare, operator.checkout)
    return bare


def test_start_story_moves_the_story_and_pushes_it(operator: Operator, remote: Path) -> None:
    result = operator.run("start-story.sh", "F0001-S0003")
    assert result.exit_status == 0, result.stderr
    assert run_git(remote, "log", "-1", "--format=%s", "main") == "F0001-S0003: start\n"
    files = run_git(remote, "ls-tree", "-r", "--name-only", "main").splitlines()
    assert f"{FEATURE}/in-progress/F0001-S0003-third.md" in files
    assert f"{FEATURE}/backlog/F0001-S0003-third.md" not in files


@pytest.mark.usefixtures("remote")
def test_start_story_refuses_an_id_in_no_backlog(operator: Operator) -> None:
    result = operator.run("start-story.sh", "F0001-S0009")
    assert (result.exit_status, result.stderr) == (
        1,
        "start-story.sh: no story F0001-S0009 in any backlog/\n",
    )


STORIES = "# Example feature\n\n## Stories\n\n- S0001: first\n- S0002: second\n\n## Out of scope\n"


@pytest.mark.parametrize(
    ("files", "line"),
    [
        pytest.param(
            {"done/F0001-S0001-first.md": "# 1\n", "backlog/F0001-S0002-second.md": "# 2\n"},
            "next: F0001-S0002",
            id="next",
        ),
        pytest.param(
            {"in-progress/F0001-S0001-first.md": "# 1\n", "backlog/F0001-S0002-second.md": "# 2\n"},
            "busy: F0001-S0001",
            id="busy",
        ),
        pytest.param(
            {"done/F0001-S0001-first.md": "# 1\n", "done/F0001-S0002-second.md": "# 2\n"},
            "none",
            id="none",
        ),
    ],
)
def test_next_story_names_the_next_story_to_start(
    operator: Operator, files: dict[str, str], line: str
) -> None:
    tree = {"README.md": "# Project\n", f"{FEATURE}/feature.md": STORIES}
    tree.update({f"{FEATURE}/{name}": text for name, text in files.items()})
    bare, _seed = make_bare_remote(operator.tmp_path / "hosting", tree)
    clone(bare, operator.checkout)
    result = operator.run("next-story.sh")
    assert result.exit_status == 0, result.stderr
    assert result.stdout == f"{line}\n"


def test_status_without_a_token_source_stops(operator: Operator) -> None:
    operator.write_site(
        SITE_REPOSITORY=REPOSITORY, SITE_CHECKOUT=str(operator.checkout), SITE_API_URL=API_URL
    )
    operator.answer(status_routes([pull(7, "work-item/F0001-S0001", ["stage:doing"])], {7: []}))
    result = operator.run("status.sh")
    assert result.exit_status != 0
    assert NO_ACCESS in result.stderr
    assert not any(line.startswith("#") for line in result.stdout.splitlines())


def test_no_script_calls_gh() -> None:
    callers = [
        f"{path.name}:{number}"
        for path in sorted(SCRIPTS.glob("*.sh"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if not line.lstrip().startswith("#") and re.search(r"\bgh\b", line)
    ]
    assert callers == []
