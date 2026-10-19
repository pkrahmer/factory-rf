"""The documents command names itself in the usage it prints for a wrong argument."""

import pytest

from factory.entry.check_documents import main

USAGE = "usage: check-documents [-h] [--root ROOT]\n"


@pytest.mark.parametrize(
    ("argv", "error"),
    [
        pytest.param(["--bogus"], "unrecognized arguments: --bogus", id="unknown-argument"),
        pytest.param(["--root"], "argument --root: expected one argument", id="root-without-value"),
    ],
)
def test_a_wrong_argument_prints_the_usage_naming_the_command_and_exits_two(
    argv: list[str], error: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(argv)

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == f"{USAGE}check-documents: error: {error}\n"
