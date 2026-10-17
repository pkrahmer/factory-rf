"""The duplicates command: reads pylint's and vulture's output and a baseline, prints the report."""

import json
import sys
from pathlib import Path
from typing import NamedTuple

import pytest

from factory.entry.check_duplicates import main

SIMILAR_KEY = "similar-code factory.a, factory.b: x = 1"
DEAD_KEY = "dead-code src/factory/c.py: unused function 'old'"
OTHER_DEAD_KEY = "dead-code src/factory/d.py: unused variable 'spare'"
PYLINT_JSON = json.dumps(
    [
        {
            "symbol": "duplicate-code",
            "message": "Similar lines in 2 files\n==factory.a:[1:5]\n==factory.b:[9:13]\n    x = 1",
        }
    ]
)
VULTURE_TEXT = "src/factory/c.py:7: unused function 'old' (60% confidence)\n"
DEAD_NEW_LINE = "new " + DEAD_KEY + " at src/factory/c.py:7: unused function 'old' (60% confidence)"


class Inputs(NamedTuple):
    pylint: Path
    vulture: Path
    baseline: Path


@pytest.fixture
def inputs(tmp_path: Path) -> Inputs:
    pylint = tmp_path / "pylint.json"
    pylint.write_text(PYLINT_JSON, encoding="utf-8")
    vulture = tmp_path / "vulture.txt"
    vulture.write_text(VULTURE_TEXT, encoding="utf-8")
    return Inputs(pylint=pylint, vulture=vulture, baseline=tmp_path / "baseline.txt")


def _arguments(inputs: Inputs, *extra: str) -> list[str]:
    return [str(inputs.pylint), str(inputs.vulture), "--baseline", str(inputs.baseline), *extra]


@pytest.mark.parametrize(
    ("baseline", "output", "status"),
    [
        (f"{SIMILAR_KEY}\n{DEAD_KEY}\n", "duplicates: 0 new, 2 known, 0 gone\n", 0),
        (f"{SIMILAR_KEY}\n", f"{DEAD_NEW_LINE}\nduplicates: 1 new, 1 known, 0 gone\n", 1),
        (
            f"{SIMILAR_KEY}\n{DEAD_KEY}\nextra-key\n",
            "gone extra-key\nduplicates: 0 new, 2 known, 1 gone\n",
            0,
        ),
    ],
    ids=["every-key", "one-key-missing", "one-key-more"],
)
def test_the_report_is_printed_and_only_new_findings_fail(
    inputs: Inputs, capsys: pytest.CaptureFixture[str], baseline: str, output: str, status: int
) -> None:
    inputs.baseline.write_text(baseline, encoding="utf-8")

    result = main(_arguments(inputs))

    assert capsys.readouterr().out == output
    assert result == status


def test_write_baseline_writes_every_key_once_and_the_next_run_passes(
    inputs: Inputs, capsys: pytest.CaptureFixture[str]
) -> None:
    inputs.vulture.write_text(
        "src/factory/c.py:7: unused function 'old' (60% confidence)\n"
        "src/factory/c.py:31: unused function 'old' (60% confidence)\n"
        "src/factory/d.py:4: unused variable 'spare' (60% confidence)\n",
        encoding="utf-8",
    )

    written = main(_arguments(inputs, "--write-baseline"))

    assert inputs.baseline.read_text(encoding="utf-8") == (
        "# Accepted findings of make duplicates, one key per line.\n"
        f"{SIMILAR_KEY}\n{DEAD_KEY}\n{OTHER_DEAD_KEY}\n"
    )
    assert capsys.readouterr().out == (
        f"duplicates: baseline of 3 findings written to {inputs.baseline}\n"
    )
    assert written == 0
    assert main(_arguments(inputs)) == 0


@pytest.mark.parametrize(
    "fault",
    ["missing-input", "unparsable-pylint", "unparsable-vulture", "missing-baseline"],
)
def test_an_unreadable_input_prints_one_error_line_and_returns_two(
    inputs: Inputs, capsys: pytest.CaptureFixture[str], fault: str
) -> None:
    inputs.baseline.write_text(f"{SIMILAR_KEY}\n{DEAD_KEY}\n", encoding="utf-8")
    if fault == "missing-input":
        inputs.pylint.unlink()
    elif fault == "unparsable-pylint":
        inputs.pylint.write_text("not json", encoding="utf-8")
    elif fault == "unparsable-vulture":
        inputs.vulture.write_text("oops\n", encoding="utf-8")
    else:
        inputs.baseline.unlink()

    status = main(_arguments(inputs))

    error = capsys.readouterr().err
    assert error.startswith("check-duplicates: ")
    assert error.count("\n") == 1
    assert error.endswith("\n")
    assert status == 2


def test_without_arguments_the_process_arguments_are_read(
    inputs: Inputs, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    inputs.baseline.write_text(f"{SIMILAR_KEY}\n", encoding="utf-8")
    given = main(_arguments(inputs))
    given_output = capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["check-duplicates", *_arguments(inputs)])

    status = main(None)

    assert capsys.readouterr().out == given_output
    assert status == given


@pytest.mark.parametrize("extra", [[], ["--write-baseline"]], ids=["plain", "write-baseline"])
def test_without_a_baseline_option_argparse_refuses(inputs: Inputs, extra: list[str]) -> None:
    with pytest.raises(SystemExit) as refused:
        main([str(inputs.pylint), str(inputs.vulture), *extra])

    assert refused.value.code == 2
