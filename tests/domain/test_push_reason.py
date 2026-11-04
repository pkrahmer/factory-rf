"""The reason of a failed push: git's last non-empty lines, at most three and 300 characters."""

import pytest

from factory.domain.git import push_reason

SERVER_ERROR = """\
remote: Internal Server Error
To https://github.com/owner/name.git
 ! [remote rejected] main -> main (Internal Server Error)
error: failed to push some refs to 'https://github.com/owner/name.git'
"""
NON_FAST_FORWARD = """\
To https://github.com/owner/name.git
 ! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs to 'https://github.com/owner/name.git'
hint: Updates were rejected because the tip of your current branch is behind
"""
UNREACHABLE = """\
fatal: unable to access 'https://github.com/owner/name.git/': Could not resolve host: github.com
"""
ADVICE_AFTER_CAUSE = """\
fatal: '/tmp/moved.git' does not appear to be a git repository
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
hint: see 'git help push'
"""
WORDS = ["alpha", "bravo", "charlie", "delta", "echo"]


@pytest.mark.parametrize(
    ("output", "held"),
    [
        pytest.param(
            SERVER_ERROR, "! [remote rejected] main -> main (Internal Server Error)", id="server"
        ),
        pytest.param(NON_FAST_FORWARD, "(non-fast-forward)", id="non-fast-forward"),
        pytest.param(UNREACHABLE, "Could not resolve host: github.com", id="unreachable"),
        pytest.param(
            ADVICE_AFTER_CAUSE, "does not appear to be a git repository", id="advice-left-out"
        ),
    ],
)
def test_the_reason_holds_gits_last_lines(output: str, held: str) -> None:
    assert held in push_reason(output)


@pytest.mark.parametrize(
    ("count", "kept"),
    [
        pytest.param(3, WORDS[:3], id="three-lines"),
        pytest.param(4, WORDS[1:4], id="four-lines"),
        pytest.param(5, WORDS[2:5], id="five-lines"),
    ],
)
def test_the_reason_keeps_the_last_three_non_empty_lines(count: int, kept: list[str]) -> None:
    output = "\n\n".join(WORDS[:count]) + "\n\n"

    reason = push_reason(output)

    assert [word for word in WORDS if word in reason] == kept


@pytest.mark.parametrize(
    ("length", "kept"),
    [pytest.param(300, 300, id="300-kept"), pytest.param(301, 300, id="301-cut")],
)
def test_a_one_line_reason_is_cut_at_300_characters(length: int, kept: int) -> None:
    line = "".join(str(index % 10) for index in range(length))

    assert push_reason(line + "\n") == line[:kept]


def test_a_joined_reason_over_300_characters_keeps_its_first_300() -> None:
    lines = [letter * 150 for letter in "xyz"]

    reason = push_reason("\n".join(lines) + "\n")

    assert len(reason) == 300
    assert reason.startswith(lines[0])
    assert "z" * 150 not in reason


CAUSE = " ! [remote rejected] main -> main (Internal Server Error)"
ACCESS_ADVICE = "Please make sure you have the correct access rights"
EXISTS_ADVICE = "and the repository exists."
HINTS = ["hint: first", "hint: second", "hint: third"]
REMOTE_ACCESS = "remote: " + ACCESS_ADVICE


@pytest.mark.parametrize(
    ("lines", "reason"),
    [
        pytest.param(
            [CAUSE, "    " + ACCESS_ADVICE, "    " + EXISTS_ADVICE],
            CAUSE.strip(),
            id="advice-lines-left-out",
        ),
        pytest.param([CAUSE, *HINTS], CAUSE.strip(), id="hint-lines-left-out"),
        pytest.param([REMOTE_ACCESS], REMOTE_ACCESS, id="more-than-advice-kept"),
    ],
)
def test_the_reason_leaves_out_gits_advice_lines(lines: list[str], reason: str) -> None:
    assert push_reason("\n".join(lines) + "\n") == reason
