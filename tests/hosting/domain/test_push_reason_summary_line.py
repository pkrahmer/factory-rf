"""A push reason leaves out git's closing "failed to push some refs" line, not other errors."""

import pytest

from factory.hosting.domain.git import push_reason

TO_LINE = "To /srv/project.git"
DONE = "Done"
REF_LINE = "!\trefs/heads/b:refs/heads/b\t[remote rejected] (pre-receive hook declined)"
PLAIN_REF_LINE = "! refs/heads/b:refs/heads/b [remote rejected] (pre-receive hook declined)"
SUMMARY_LINE = "error: failed to push some refs to '/srv/project.git'"


def _output(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def test_the_reason_leaves_out_gits_summary_line_of_a_refused_push() -> None:
    output = _output(["remote: Internal Server Error", SUMMARY_LINE, TO_LINE, REF_LINE, DONE])

    assert push_reason(output) == f"remote: Internal Server Error | {PLAIN_REF_LINE}"


@pytest.mark.parametrize(
    ("line", "reason"),
    [
        pytest.param(
            "error: failed to push some refs to 'https://github.com/o/r.git'",
            "alpha",
            id="summary-left-out",
        ),
        pytest.param(
            "   error: failed to push some refs to 'https://github.com/o/r.git'",
            "alpha",
            id="indented-summary-left-out",
        ),
        pytest.param(
            "error: src refspec main does not match any",
            "alpha | error: src refspec main does not match any",
            id="other-error-kept",
        ),
        pytest.param(
            "remote: error: failed to push some refs to x",
            "alpha | remote: error: failed to push some refs to x",
            id="words-further-in-kept",
        ),
    ],
)
def test_the_reason_leaves_out_only_the_summary_line(line: str, reason: str) -> None:
    assert push_reason(_output(["alpha", line])) == reason


def test_two_server_lines_and_the_ref_line_fill_the_reason() -> None:
    output = _output(
        [
            "remote: Internal Server Error",
            "remote: request id 1234",
            SUMMARY_LINE,
            TO_LINE,
            REF_LINE,
            DONE,
        ]
    )

    assert push_reason(output) == (
        f"remote: Internal Server Error | remote: request id 1234 | {PLAIN_REF_LINE}"
    )
