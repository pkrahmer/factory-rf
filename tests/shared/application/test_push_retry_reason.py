"""A retried push of a stage's result names the server's words, not git's porcelain frame."""

import contextlib

from factory.shared.domain.errors import PushFailed
from push_retry_support import PushCase


def test_a_retry_line_holds_the_servers_message_and_no_porcelain_done(
    result_case: PushCase,
) -> None:
    result_case.arm(4)

    with contextlib.suppress(PushFailed):
        result_case.push()

    lines = result_case.retry_lines()
    assert lines
    for line in lines:
        assert "remote: Internal Server Error" in line
        assert "[remote rejected]" in line
        assert "Done" not in line
