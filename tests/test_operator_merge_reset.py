"""The skill's merge and reset scripts: their checks, their requests in order and their messages."""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from factory.adapters.process import ProcessResult
from git_support import write_executable
from operator_support import CURL_STAND_IN, ROOT, hosting_env, run_script

SCRIPTS = ROOT / "operator" / "skill" / "kumpel" / "scripts"
REPOSITORY = "owner/repo"
PREFIX = f"/repos/{REPOSITORY}"
API_URL = "https://api.example.invalid"
# The command builds the token, so its text is in no file the test writes.
ACCESS_COMMAND = "printf 'tok%s\\n' 123"
ITEM = "F0001-S0001"
ARCHIVE = f"work item {ITEM}: merged, archived"
TAG = "starting-point"
COMMIT = "c" * 40
TAG_OBJECT = "d" * 40
SHORT = COMMIT[:7]
CHANGES = ("PUT", "PATCH", "POST", "DELETE")

# A router in front of S0003's `curl` stand-in: it reads the request from curl's configuration on
# standard input, counts the calls per method and route, and gives the recording stand-in the
# status and the body that `STAND_IN_ROUTER_ANSWERS` names for that call (the last answer repeats
# for later calls; the path and query first, else the path alone; 404 for any other).
CURL_ROUTER = r"""
import json, os, re, subprocess, sys

configuration = sys.stdin.read()
url = re.search(r'^url = "([^"]*)"$', configuration, re.MULTILINE)
method = re.search(r'^request = "([^"]*)"$', configuration, re.MULTILINE)
route = re.sub(r"^[a-z]+://[^/]*", "", url.group(1) if url else "")
method = method.group(1) if method else "GET"
with open(os.environ["STAND_IN_ROUTER_ANSWERS"], encoding="utf-8") as source:
    answers = json.load(source)
key = f"{method} {route}"
if key not in answers:
    key = f"{method} {route.split('?')[0]}"
counter = os.environ["STAND_IN_ROUTER_ANSWERS"] + ".calls"
counts = {}
if os.path.exists(counter):
    with open(counter, encoding="utf-8") as source:
        counts = json.load(source)
number = counts.get(key, 0)
counts[key] = number + 1
with open(counter, "w", encoding="utf-8") as target:
    json.dump(counts, target)
listed = answers.get(key) or [["404", '{"message": "Not Found"}']]
status, body = listed[min(number, len(listed) - 1)]
env = dict(os.environ, STAND_IN_CURL_STATUS=status, STAND_IN_CURL_BODY=body)
here = os.path.dirname(os.path.abspath(__file__))
completed = subprocess.run(
    [os.path.join(here, "recording-curl"), *sys.argv[1:]], input=configuration, text=True, env=env
)
sys.exit(completed.returncode)
"""


@dataclass(frozen=True)
class Request:
    """One request the `curl` stand-in recorded: its method, its path and query, its JSON body."""

    method: str
    route: str
    body: object


Answers = dict[str, list[tuple[int, object]]]


def ok(body: object) -> list[tuple[int, object]]:
    """One answer, 200 with `body`, for every call."""
    return [(200, body)]


@dataclass(frozen=True)
class Machine:
    """The operator's machine in `tmp_path`: a site file, the `curl` stand-ins and the answers."""

    tmp_path: Path
    site_file: Path
    records: Path
    temporary: Path
    bin_folder: Path
    answers_file: Path

    def write_site(self, **values: str) -> None:
        """Write the site file with the API, the token command and exactly `values` besides."""
        lines = [f"{name}={value}\n" for name, value in values.items()]
        text = f"SITE_API_URL={API_URL}\nSITE_TOKEN_CMD={ACCESS_COMMAND}\n" + "".join(lines)
        self.site_file.write_text("# the site of a test\n" + text, encoding="utf-8")

    def answer(self, answers: Answers) -> None:
        """Let the stand-in answer each `METHOD /path` with its answers, one per call in order."""
        encoded = {
            f"{key.split(' ', 1)[0]} {PREFIX}{key.split(' ', 1)[1]}": [
                [str(status), body if isinstance(body, str) else json.dumps(body)]
                for status, body in listed
            ]
            for key, listed in answers.items()
        }
        self.answers_file.write_text(json.dumps(encoded), encoding="utf-8")

    def run(self, script: str, *arguments: str, **values: str) -> ProcessResult:
        """Run the skill's `script` with `arguments` on this machine, with `values` in its env."""
        env = hosting_env(
            self.tmp_path,
            self.site_file,
            self.records,
            self.temporary,
            self.bin_folder,
            STAND_IN_ROUTER_ANSWERS=str(self.answers_file),
            KUMPEL_SETTINGS=str(self.tmp_path / "settings" / "settings.json"),
            **values,
        )
        return run_script([str(SCRIPTS / script), *arguments], self.tmp_path, env)

    def requests(self) -> list[Request]:
        """Every request the `curl` stand-in recorded, in order, its route without the prefix."""
        path = self.records / "curl.jsonl"
        if not path.exists():
            return []
        found = []
        for line in path.read_text(encoding="utf-8").splitlines():
            configuration = str(json.loads(line)["stdin"])
            url = re.search(r'^url = "([^"]*)"$', configuration, re.MULTILINE)
            method = re.search(r'^request = "([^"]*)"$', configuration, re.MULTILINE)
            data = re.search(r'^data = (".*")$', configuration, re.MULTILINE)
            assert url is not None
            assert method is not None
            route = url.group(1).removeprefix(API_URL).removeprefix(PREFIX)
            body = json.loads(json.loads(data.group(1))) if data else None
            found.append(Request(method.group(1), route, body))
        return found

    def changes(self) -> list[Request]:
        """The recorded requests that change something, in order."""
        return [request for request in self.requests() if request.method in CHANGES]


@pytest.fixture
def machine(tmp_path: Path) -> Machine:
    """The machine with a site that names the repository as resettable, and no answers."""
    folders = {name: tmp_path / name for name in ("site", "records", "tmp", "bin")}
    for folder in folders.values():
        folder.mkdir()
    write_executable(folders["bin"], CURL_STAND_IN, name="recording-curl")
    write_executable(folders["bin"], CURL_ROUTER, name="curl")
    built = Machine(
        tmp_path=tmp_path,
        site_file=folders["site"] / "site.env",
        records=folders["records"],
        temporary=folders["tmp"],
        bin_folder=folders["bin"],
        answers_file=tmp_path / "answers.json",
    )
    built.write_site(SITE_REPOSITORY=REPOSITORY, SITE_RESET_REPOSITORY=REPOSITORY)
    built.answer({})
    return built


def printed(result: ProcessResult) -> list[str]:
    """The lines the run printed, its standard output first."""
    return result.stdout.splitlines() + result.stderr.splitlines()


def in_order(lines: list[str], expected: list[str]) -> bool:
    """`expected` are lines of `lines`, in this order."""
    remaining = iter(lines)
    return all(line in remaining for line in expected)


# merge.sh


def pull_request(
    *, state: str = "open", draft: bool = False, labels: tuple[str, ...] = ("stage:approval",)
) -> dict[str, object]:
    """Pull request 5 as `GET /pulls/5` answers it."""
    return {
        "number": 5,
        "state": state,
        "draft": draft,
        "head": {"ref": f"work-item/{ITEM}"},
        "labels": [{"name": name} for name in labels],
    }


def commit_list(*subjects: str) -> list[dict[str, object]]:
    """The newest commits on `main`, newest first."""
    return [{"sha": "e" * 40, "commit": {"message": f"{text}\n"}} for text in subjects]


def merge_answers(
    pull: dict[str, object] | None = None,
    commits: list[tuple[int, object]] | None = None,
) -> Answers:
    """The answers of a merge: the pull request, a merge that succeeds, the commit list."""
    return {
        "GET /pulls/5": ok(pull_request() if pull is None else pull),
        "PUT /pulls/5/merge": ok({"merged": True, "sha": "f" * 40}),
        "GET /commits?per_page=20": commits or ok(commit_list(ARCHIVE, "earlier work")),
    }


MERGE_FAST = {"KUMPEL_POLL_SECONDS": "0", "KUMPEL_ARCHIVE_WAIT": "60"}


def test_an_approved_pull_request_is_merged_and_its_archive_awaited(machine: Machine) -> None:
    machine.answer(merge_answers())
    result = machine.run("merge.sh", "5", ITEM, **MERGE_FAST)
    assert result.exit_status == 0, result.stderr
    puts = [request for request in machine.requests() if request.method == "PUT"]
    assert puts == [Request("PUT", "/pulls/5/merge", {"merge_method": "merge"})]
    routes = [request.route for request in machine.requests()]
    assert "/commits?per_page=20" in routes[routes.index("/pulls/5/merge") :]
    assert in_order(printed(result), ["merged #5", f"archived {ITEM}"])


@pytest.mark.parametrize(
    ("pull", "message"),
    [
        pytest.param(pull_request(state="closed"), "merge.sh: #5 is not open", id="closed"),
        pytest.param(pull_request(draft=True), "merge.sh: #5 is a draft", id="draft"),
        pytest.param(
            pull_request(labels=("stage:review",)),
            "merge.sh: #5 is not at stage:approval",
            id="not-at-approval",
        ),
        pytest.param(
            {**pull_request(), "head": {"ref": "work-item/F0001-S0002"}},
            f"merge.sh: #5 is not the pull request of {ITEM}",
            id="another-work-item",
        ),
    ],
)
def test_a_pull_request_that_is_not_ready_for_the_merge_is_refused(
    machine: Machine, pull: dict[str, object], message: str
) -> None:
    machine.answer(merge_answers(pull))
    result = machine.run("merge.sh", "5", ITEM, **MERGE_FAST)
    assert result.exit_status == 1
    assert message in printed(result)
    assert [request for request in machine.requests() if request.method == "PUT"] == []


def test_a_merge_the_host_refuses_stops_without_polling(machine: Machine) -> None:
    answers = merge_answers()
    answers["PUT /pulls/5/merge"] = [(405, {"message": "Pull Request is not mergeable"})]
    machine.answer(answers)
    result = machine.run("merge.sh", "5", ITEM, **MERGE_FAST)
    assert result.exit_status == 1
    assert f"hosting: PUT {PREFIX}/pulls/5/merge: 405 Pull Request is not mergeable" in printed(
        result
    )
    assert "/commits?per_page=20" not in [request.route for request in machine.requests()]


@pytest.mark.parametrize(
    ("commits", "wait", "exit_status", "line"),
    [
        pytest.param(
            ok(commit_list("earlier work")),
            "0",
            1,
            f"merge.sh: merged, but no archive commit for {ITEM} after 0 s",
            id="no-archive-commit",
        ),
        pytest.param(
            [
                (200, commit_list("earlier work")),
                (200, commit_list("earlier work")),
                (200, commit_list(ARCHIVE, "earlier work")),
            ],
            "60",
            0,
            f"archived {ITEM}",
            id="archive-commit-in-the-third-poll",
        ),
    ],
)
def test_the_merge_waits_for_the_archive_commit(
    *,
    machine: Machine,
    commits: list[tuple[int, object]],
    wait: str,
    exit_status: int,
    line: str,
) -> None:
    machine.answer(merge_answers(commits=commits))
    result = machine.run("merge.sh", "5", ITEM, KUMPEL_POLL_SECONDS="0", KUMPEL_ARCHIVE_WAIT=wait)
    assert result.exit_status == exit_status, result.stderr
    assert in_order(printed(result), ["merged #5", line])


# reset-to-tag.sh


def open_pull(number: int, branch: str) -> dict[str, object]:
    """An open pull request as the list of open pull requests gives it."""
    return {"number": number, "state": "open", "head": {"ref": branch}}


BRANCHES = ("work-item/F0001-S0001", "work-item/F0001-S0002", "work-item/F0001-S0003")
NOT_FOUND: list[tuple[int, object]] = [(404, {"message": "Not Found"})]
REFUSED: list[tuple[int, object]] = [(422, {"message": "Validation Failed"})]


def reset_answers(
    *,
    annotated: bool = False,
    pulls: list[dict[str, object]] | None = None,
    branches: tuple[str, ...] = BRANCHES,
) -> Answers:
    """The answers of a reset to `TAG`: the tag, the pull requests, the branches, the changes."""
    if pulls is None:
        pulls = [
            open_pull(7, "work-item/F0001-S0001"),
            open_pull(8, "work-item/F0001-S0002"),
            open_pull(9, "feature-of-a-human"),
        ]
    answers: Answers = {
        "GET /pulls?state=open&per_page=100": ok(pulls),
        "GET /git/matching-refs/heads/work-item/": ok(
            [{"ref": f"refs/heads/{branch}", "object": {"sha": "b" * 40}} for branch in branches]
        ),
        "PATCH /git/refs/heads/main": ok({"ref": "refs/heads/main", "object": {"sha": COMMIT}}),
    }
    if annotated:
        answers[f"GET /git/ref/tags/{TAG}"] = ok(
            {"ref": f"refs/tags/{TAG}", "object": {"type": "tag", "sha": TAG_OBJECT}}
        )
        answers[f"GET /git/tags/{TAG_OBJECT}"] = ok(
            {"sha": TAG_OBJECT, "object": {"type": "commit", "sha": COMMIT}}
        )
    else:
        answers[f"GET /git/ref/tags/{TAG}"] = ok(
            {"ref": f"refs/tags/{TAG}", "object": {"type": "commit", "sha": COMMIT}}
        )
    for pull in pulls:
        answers[f"PATCH /pulls/{pull['number']}"] = ok({**pull, "state": "closed"})
    for branch in branches:
        answers[f"DELETE /git/refs/heads/{branch}"] = [(204, "")]
    return answers


def full_reset() -> list[Request]:
    """The changes of a full reset of `reset_answers()`, in their order."""
    return [
        Request("PATCH", "/pulls/7", {"state": "closed"}),
        Request("PATCH", "/pulls/8", {"state": "closed"}),
        *(Request("DELETE", f"/git/refs/heads/{branch}", None) for branch in BRANCHES),
        Request("PATCH", "/git/refs/heads/main", {"sha": COMMIT, "force": True}),
    ]


@pytest.mark.parametrize(
    ("site", "exit_status", "message"),
    [
        pytest.param(
            {"SITE_REPOSITORY": REPOSITORY, "SITE_RESET_REPOSITORY": "owner/other"},
            1,
            f"reset-to-tag.sh: {REPOSITORY} is not the site's resettable repository",
            id="another-resettable-repository",
        ),
        pytest.param(
            {"SITE_REPOSITORY": REPOSITORY},
            2,
            "site: missing SITE_RESET_REPOSITORY in {site_file}",
            id="no-resettable-repository",
        ),
        pytest.param(
            {"SITE_RESET_REPOSITORY": REPOSITORY},
            2,
            "site: missing SITE_REPOSITORY in {site_file}",
            id="no-repository",
        ),
    ],
)
def test_a_repository_the_site_does_not_name_as_resettable_is_not_reset(
    machine: Machine, site: dict[str, str], exit_status: int, message: str
) -> None:
    machine.write_site(**site)
    machine.answer(reset_answers())
    result = machine.run("reset-to-tag.sh", TAG, "--yes")
    assert result.exit_status == exit_status
    assert message.format(site_file=machine.site_file) in printed(result)
    assert machine.changes() == []


def test_without_yes_the_reset_prints_its_plan_and_changes_nothing(machine: Machine) -> None:
    machine.answer(reset_answers())
    result = machine.run("reset-to-tag.sh", TAG)
    assert result.exit_status == 1
    assert {request.method for request in machine.requests()} <= {"GET"}
    assert in_order(
        printed(result),
        [
            "would close 2 open work-item pull request(s)",
            "would delete 3 work-item branch(es)",
            f"would move main to {SHORT}",
            "run again with --yes",
        ],
    )


def test_a_tag_that_does_not_exist_changes_nothing(machine: Machine) -> None:
    answers = reset_answers()
    answers[f"GET /git/ref/tags/{TAG}"] = NOT_FOUND
    machine.answer(answers)
    result = machine.run("reset-to-tag.sh", TAG, "--yes")
    assert result.exit_status == 1
    assert f"reset-to-tag.sh: no tag {TAG}" in printed(result)
    assert machine.changes() == []


@pytest.mark.parametrize(
    "annotated", [pytest.param(True, id="annotated"), pytest.param(False, id="lightweight")]
)
def test_the_tag_is_followed_to_its_commit(machine: Machine, annotated: bool) -> None:
    machine.answer(reset_answers(annotated=annotated))
    result = machine.run("reset-to-tag.sh", TAG, "--yes")
    assert result.exit_status == 0, result.stderr
    assert machine.changes()[-1] == Request(
        "PATCH", "/git/refs/heads/main", {"sha": COMMIT, "force": True}
    )


def test_with_yes_the_reset_closes_deletes_and_moves_in_this_order(machine: Machine) -> None:
    machine.answer(reset_answers())
    result = machine.run("reset-to-tag.sh", TAG, "--yes")
    assert result.exit_status == 0, result.stderr
    assert machine.changes() == full_reset()
    assert in_order(
        printed(result),
        [
            "closed #7",
            "closed #8",
            *(f"deleted {branch}" for branch in BRANCHES),
            f"moved main to {SHORT}",
        ],
    )
    assert "closed #9" not in printed(result)


@pytest.mark.parametrize(
    ("failing", "sent", "message"),
    [
        pytest.param(
            "PATCH /pulls/7",
            full_reset()[:1],
            f"hosting: PATCH {PREFIX}/pulls/7: 422 Validation Failed",
            id="close",
        ),
        pytest.param(
            f"DELETE /git/refs/heads/{BRANCHES[2]}",
            full_reset()[:5],
            f"hosting: DELETE {PREFIX}/git/refs/heads/{BRANCHES[2]}: 422 Validation Failed",
            id="third-delete",
        ),
        pytest.param(
            "PATCH /git/refs/heads/main",
            full_reset(),
            f"hosting: PATCH {PREFIX}/git/refs/heads/main: 422 Validation Failed",
            id="move-of-main",
        ),
    ],
)
def test_a_failing_call_stops_the_reset_there(
    machine: Machine, failing: str, sent: list[Request], message: str
) -> None:
    answers = reset_answers()
    answers[failing] = REFUSED
    machine.answer(answers)
    result = machine.run("reset-to-tag.sh", TAG, "--yes")
    assert result.exit_status == 1
    assert message in printed(result)
    assert machine.changes() == sent


def test_a_reset_with_nothing_to_close_or_delete_only_moves_main(machine: Machine) -> None:
    machine.answer(reset_answers(pulls=[], branches=()))
    result = machine.run("reset-to-tag.sh", TAG, "--yes")
    assert result.exit_status == 0, result.stderr
    assert machine.changes() == [
        Request("PATCH", "/git/refs/heads/main", {"sha": COMMIT, "force": True})
    ]
    assert printed(result) == [f"moved main to {SHORT}"]


@dataclass(frozen=True)
class Run:
    """One run of a script with its answers and its arguments, on the fixture's site."""

    script: str
    arguments: tuple[str, ...]
    answers: Answers


def failing(name: str) -> Answers:
    """The answers of a full reset with the change `name` refused."""
    return {**reset_answers(), name: REFUSED}


RUNS: list[Callable[[], Run]] = [
    lambda: Run("merge.sh", ("5", ITEM), merge_answers()),
    lambda: Run("reset-to-tag.sh", (TAG,), reset_answers()),
    lambda: Run("reset-to-tag.sh", (TAG, "--yes"), reset_answers()),
    lambda: Run("reset-to-tag.sh", (TAG, "--yes"), reset_answers(annotated=True)),
    lambda: Run("reset-to-tag.sh", (TAG, "--yes"), reset_answers(pulls=[], branches=())),
    lambda: Run("reset-to-tag.sh", (TAG, "--yes"), failing("PATCH /pulls/7")),
    lambda: Run(
        "reset-to-tag.sh", (TAG, "--yes"), failing(f"DELETE /git/refs/heads/{BRANCHES[2]}")
    ),
    lambda: Run("reset-to-tag.sh", (TAG, "--yes"), failing("PATCH /git/refs/heads/main")),
]
# What a change may touch: a pull request, a work item's branch, `main`.
ALLOWED_CHANGE = re.compile(r"^/pulls/\d+(/merge)?$|^/git/refs/heads/(work-item/.+|main)$")


@pytest.mark.parametrize(
    "make_run",
    [pytest.param(make_run, id=f"run-{index}") for index, make_run in enumerate(RUNS, start=1)],
)
def test_no_change_touches_another_ref_or_a_tag(
    machine: Machine, make_run: Callable[[], Run]
) -> None:
    run = make_run()
    machine.answer(run.answers)
    machine.run(run.script, *run.arguments, **MERGE_FAST)
    assert machine.requests()
    for request in machine.changes():
        assert ALLOWED_CHANGE.match(request.route), request
        assert "/tags" not in request.route, request
    closed = {request.route for request in machine.changes() if request.method == "PATCH"}
    assert "/pulls/9" not in closed
