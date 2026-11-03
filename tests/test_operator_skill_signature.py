"""The skill signs its acts: its comments, its start commits; the state reads a signed verdict."""

import os
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.process import ProcessResult
from git_support import clone, run_git
from operator_skill_support import (
    PREFIX,
    SCRIPTS,
    SKILL,
    Operator,
    make_bare_remote,
    pull,
    recorded_requests,
    status_routes,
)
from operator_support import hosting_env, run_script

SIGNATURE = "— Kumpel, for the human who owns this project"
MARKER = "<!-- kumpel -->"
ANSWER = "Yes, as you propose."
ROUTE = "/issues/7/comments"
COMMENTS = f"{PREFIX}{ROUTE}"
KUMPEL = "Kumpel <kumpel@noreply.invalid>"
FEATURE = "factory/features/F0001-example"


def posted_body(operator: Operator) -> str:
    """The `body` of the one request sent, which must be a `POST` of a comment on #7."""
    requests = recorded_requests(operator.records)
    assert [(request.method, request.route) for request in requests] == [("POST", ROUTE)]
    body = requests[0].body
    assert isinstance(body, dict)
    text = body["body"]
    assert isinstance(text, str)
    return text


@pytest.fixture
def answering(operator: Operator) -> Operator:
    """The operator's machine whose host accepts a comment on pull request 7."""
    operator.answer({COMMENTS: {"id": 1, "body": "posted"}})
    return operator


def write_text(operator: Operator, text: str) -> Path:
    """Write `text` to the file a comment is posted from."""
    path = operator.tmp_path / "comment.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_comment_is_posted_with_the_signature_and_the_marker(answering: Operator) -> None:
    path = write_text(answering, f"{ANSWER}\n")
    result = answering.run("comment.sh", "7", str(path))
    assert result.exit_status == 0, result.stderr
    assert result.stdout == "commented #7\n"
    assert posted_body(answering).rstrip("\n") == f"{ANSWER}\n\n{SIGNATURE}\n{MARKER}"


SIGNED_ANSWER = f"{ANSWER}\n\n{SIGNATURE}\n{MARKER}"


@pytest.mark.parametrize(
    ("text", "expected", "signatures"),
    [
        pytest.param(SIGNED_ANSWER, SIGNED_ANSWER, 1, id="ends-signed"),
        pytest.param(
            f"{SIGNED_ANSWER}\nMore.",
            f"{SIGNED_ANSWER}\nMore.\n\n{SIGNATURE}\n{MARKER}",
            2,
            id="signed-then-more-text",
        ),
    ],
)
def test_a_text_is_signed_unless_it_ends_signed(
    answering: Operator, text: str, expected: str, signatures: int
) -> None:
    path = write_text(answering, f"{text}\n")
    result = answering.run("comment.sh", "7", str(path))
    assert result.exit_status == 0, result.stderr
    body = posted_body(answering)
    assert body.rstrip("\n") == expected
    assert body.count(SIGNATURE) == signatures


def missing(operator: Operator) -> list[str]:
    """The arguments of a comment from a file that does not exist."""
    return ["7", str(operator.tmp_path / "absent.md")]


def empty(operator: Operator) -> list[str]:
    """The arguments of a comment from an empty file."""
    return ["7", str(write_text(operator, ""))]


def refused(operator: Operator) -> list[str]:
    """The arguments of a comment the host answers with 404: no route answers it."""
    operator.answer({})
    return ["7", str(write_text(operator, f"{ANSWER}\n"))]


@pytest.mark.parametrize(
    ("arguments", "exit_status", "message", "requests"),
    [
        pytest.param(missing, 1, "comment.sh: nothing to post in {file}", 0, id="missing-file"),
        pytest.param(empty, 1, "comment.sh: nothing to post in {file}", 0, id="empty-file"),
        pytest.param(refused, 1, f"hosting: POST {COMMENTS}: 404 Not Found", 1, id="404"),
        pytest.param(lambda _: [], 2, "usage: comment.sh <pull request> <file>", 0, id="none"),
        pytest.param(lambda _: ["7"], 2, "usage: comment.sh <pull request> <file>", 0, id="one"),
        pytest.param(
            lambda operator: ["7", str(write_text(operator, f"{ANSWER}\n")), "extra"],
            2,
            "usage: comment.sh <pull request> <file>",
            0,
            id="three",
        ),
    ],
)
def test_a_comment_that_cannot_be_posted_is_refused(
    *,
    answering: Operator,
    arguments: Callable[[Operator], list[str]],
    exit_status: int,
    message: str,
    requests: int,
) -> None:
    words = arguments(answering)
    result = answering.run("comment.sh", *words)
    assert result.exit_status == exit_status
    expected = message.format(file=words[-1] if words else "")
    assert expected in result.stderr.splitlines()
    assert len(recorded_requests(answering.records)) == requests


def run_start_story(operator: Operator, story: str) -> ProcessResult:
    """Run `start-story.sh` with no identity in the environment: the clone's own is the human's."""
    env = hosting_env(
        operator.tmp_path,
        operator.site_file,
        operator.records,
        operator.temporary,
        operator.bin_folder,
        KUMPEL_SETTINGS=str(operator.settings_file),
        GIT_CONFIG_GLOBAL=os.devnull,
    )
    return run_script([str(SCRIPTS / "start-story.sh"), story], operator.tmp_path, env)


def test_the_start_commit_is_kumpels_and_the_clone_keeps_its_identity(operator: Operator) -> None:
    files = {
        "README.md": "# Project\n",
        f"{FEATURE}/feature.md": "# Example feature\n",
        f"{FEATURE}/backlog/F0001-S0002-second.md": "# Second story\n",
    }
    bare, _seed = make_bare_remote(operator.tmp_path / "hosting", files)
    clone(bare, operator.checkout)
    run_git(operator.checkout, "config", "user.name", "Human")
    run_git(operator.checkout, "config", "user.email", "human@example.invalid")
    result = run_start_story(operator, "F0001-S0002")
    assert result.exit_status == 0, result.stderr
    pushed = run_git(bare, "log", "-1", "--format=%s%n%an <%ae>%n%cn <%ce>", "main")
    assert pushed.splitlines() == ["F0001-S0002: start", KUMPEL, KUMPEL]
    assert run_git(operator.checkout, "config", "--local", "user.name") == "Human\n"
    assert run_git(operator.checkout, "config", "--local", "user.email") == (
        "human@example.invalid\n"
    )


VERDICT_MARKER = "<!-- kumpel verdict -->"
SIGNED = f"\n{SIGNATURE}\n{MARKER}"
SIGNED_VERDICT = f"Kumpel: ready to merge.\n{VERDICT_MARKER}\n\nThe six checks are green.\n{SIGNED}"


@pytest.mark.parametrize(
    ("body", "state"),
    [
        pytest.param(SIGNED_VERDICT, "verdict posted", id="signed-verdict"),
        pytest.param(
            f"{SIGNED_VERDICT}\n<!-- factory key=abc:question:1 -->",
            "waits: question",
            id="signed-verdict-and-factory-marker",
        ),
        pytest.param(f"{ANSWER}\n\n{SIGNATURE}\n{MARKER}", "working", id="no-verdict-marker"),
        pytest.param(
            f"{VERDICT_MARKER}\nKumpel: ready to merge.\none\ntwo\nthree\nfour\n{SIGNED}",
            "verdict posted",
            id="verdict-marker-at-the-top",
        ),
    ],
)
def test_a_verdict_marker_anywhere_in_the_newest_comment_is_a_posted_verdict(
    operator: Operator, body: str, state: str
) -> None:
    operator.answer(
        status_routes([pull(7, "work-item/F0001-S0001", ["stage:doing"])], {7: ["Earlier.", body]})
    )
    result = operator.run("status.sh")
    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines()[0] == f"#7 F0001-S0001 stage:doing {state}"


def test_no_file_of_the_skill_posts_with_gh() -> None:
    holders = [
        str(path.relative_to(SKILL))
        for path in sorted(SKILL.rglob("*"))
        if path.is_file() and "gh pr comment" in path.read_text(encoding="utf-8")
    ]
    assert holders == []


@pytest.mark.parametrize("name", ["SKILL.md", "references/answering.md", "references/approving.md"])
def test_the_skill_names_the_comment_script(name: str) -> None:
    assert "comment.sh" in (SKILL / name).read_text(encoding="utf-8")
