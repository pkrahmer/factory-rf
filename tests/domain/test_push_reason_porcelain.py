"""A push's reason leaves out git's porcelain frame and writes each kept line plainly."""

import pytest

from factory.domain.git import push_reason

TO_LINE = "To /srv/project.git"
DONE = "Done"
WORDS = ["alpha", "bravo", "charlie", "delta", "echo"]


def _output(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def test_the_reason_keeps_the_servers_line_and_the_refused_ref() -> None:
    output = _output(
        [
            "remote: Internal Server Error",
            TO_LINE,
            "!\trefs/heads/b:refs/heads/b\t[remote rejected] (pre-receive hook declined)",
            DONE,
        ]
    )

    assert push_reason(output) == (
        "remote: Internal Server Error"
        " | ! refs/heads/b:refs/heads/b [remote rejected] (pre-receive hook declined)"
    )


@pytest.mark.parametrize(
    ("line", "reason"),
    [
        pytest.param("   Done", "alpha", id="indented-done-left-out"),
        pytest.param("To https://github.com/o/r.git", "alpha", id="to-line-left-out"),
        pytest.param("remote: Done", "alpha | remote: Done", id="remote-done-kept"),
        pytest.param("remote: To be retried", "alpha | remote: To be retried", id="remote-to-kept"),
    ],
)
def test_the_reason_leaves_out_the_porcelain_frame_only(line: str, reason: str) -> None:
    assert push_reason(_output(["alpha", line])) == reason


@pytest.mark.parametrize(
    ("lines", "reason"),
    [
        pytest.param(["a\tb"], "a b", id="tab-inside"),
        pytest.param(["a  b"], "a b", id="two-spaces"),
        pytest.param(["a\t \tb"], "a b", id="mixed-run"),
        pytest.param(
            ["alpha", "bravo", "\t\t", "charlie"], "alpha | bravo | charlie", id="tabs-only-empty"
        ),
    ],
)
def test_whitespace_in_a_kept_line_becomes_one_space(lines: list[str], reason: str) -> None:
    assert push_reason(_output([*lines, DONE])) == reason


@pytest.mark.parametrize(
    ("count", "kept"),
    [
        pytest.param(3, WORDS[:3], id="three-lines"),
        pytest.param(4, WORDS[1:4], id="four-lines"),
        pytest.param(5, WORDS[2:5], id="five-lines"),
    ],
)
def test_the_reason_keeps_the_last_three_lines_after_the_frame(count: int, kept: list[str]) -> None:
    lines = WORDS[:count]
    output = _output([*lines[:1], TO_LINE, *lines[1:], DONE])

    assert push_reason(output) == " | ".join(kept)


@pytest.mark.parametrize(
    ("length", "kept"),
    [pytest.param(300, 300, id="300-kept"), pytest.param(301, 300, id="301-cut")],
)
def test_a_reason_with_the_frame_is_cut_at_300_characters(length: int, kept: int) -> None:
    line = "".join(str(index % 10) for index in range(length))

    assert push_reason(_output([TO_LINE, line, DONE])) == line[:kept]
