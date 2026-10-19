"""Streaming an output that takes more than one read, against real Python child processes."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, ProcessResult, Stream, run_streaming
from process_support import Recorder, python_argv

LONG_LINE_LENGTH = 200000
TIME_LIMIT = timedelta(seconds=20)


def _text(result: ProcessResult, stream: Stream) -> str:
    return result.stdout if stream == "stdout" else result.stderr


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_line_longer_than_one_read_reaches_the_callback_and_the_result_whole(
    tmp_path: Path, stream: Stream
) -> None:
    code = f"import sys; sys.{stream}.write('x' * {LONG_LINE_LENGTH} + '\\n')"
    recorder = Recorder()

    result = run_streaming(
        ProcessRequest(argv=python_argv(code), cwd=tmp_path, time_limit=TIME_LIMIT), recorder
    )

    assert recorder.calls == [(stream, "x" * LONG_LINE_LENGTH)]
    assert len(_text(result, stream)) == LONG_LINE_LENGTH + 1


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_line_split_across_two_writes_reaches_the_callback_once_and_whole(
    tmp_path: Path, stream: Stream
) -> None:
    code = (
        "import sys, time; "
        f"out = sys.{stream}; "
        "out.write('{\"a\":'); out.flush(); "
        "time.sleep(0.5); "
        "out.write('1}\\n'); out.flush()"
    )
    recorder = Recorder()

    result = run_streaming(
        ProcessRequest(argv=python_argv(code), cwd=tmp_path, time_limit=TIME_LIMIT), recorder
    )

    assert [line for given, line in recorder.calls if given == stream] == ['{"a":1}']
    assert _text(result, stream) == '{"a":1}\n'
