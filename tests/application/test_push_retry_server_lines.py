"""A retried push of a stage's result keeps two server lines and leaves out git's summary line."""

import contextlib

from factory.domain.errors import PushFailed
from push_retry_support import PushCase

ONE_LINE = "  echo 'Internal Server Error' >&2\n"
TWO_LINES = "  echo 'Internal Server Error' >&2\n  echo 'request id 1234' >&2\n"


def _arm_with_two_lines(case: PushCase, failures: int) -> None:
    case.arm(failures)
    hook = case.remote / "hooks" / "pre-receive"
    text = hook.read_text(encoding="utf-8")
    assert ONE_LINE in text
    hook.write_text(text.replace(ONE_LINE, TWO_LINES), encoding="utf-8")


def test_a_retry_line_holds_both_server_lines_and_no_summary_line(
    result_case: PushCase,
) -> None:
    _arm_with_two_lines(result_case, 4)

    with contextlib.suppress(PushFailed):
        result_case.push()

    lines = result_case.retry_lines()
    assert lines
    for line in lines:
        assert "remote: Internal Server Error" in line
        assert "remote: request id 1234" in line
        assert "[remote rejected]" in line
        assert "failed to push some refs" not in line
