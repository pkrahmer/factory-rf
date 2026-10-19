"""The mutants command: mutmut's results read, and the report or the names to run again printed."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from factory.domain.mutants import mutation_report, parse_results, rerun_names
from factory.entry.inputs import UnreadableInput, read_input

_PROGRAM = "check-mutants"
_COMPLETE = 0
_PARTIAL = 1
_FAILURE = 2


def _at_least_one(text: str) -> int:
    try:
        seconds = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"not an integer: {text!r}") from error
    if seconds < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, not {seconds}")
    return seconds


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("results", type=Path)
    parser.add_argument("modules", nargs="+")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--stopped-after", type=_at_least_one)
    mode.add_argument("--names", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Print the report and return 1 when it is partial, 0 otherwise, 2 on unreadable input."""
    arguments = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    modules: list[str] = arguments.modules
    try:
        results = parse_results(read_input(arguments.results))
    except (UnreadableInput, ValueError) as error:
        print(f"{_PROGRAM}: {error}", file=sys.stderr)
        return _FAILURE
    if arguments.names:
        for name in rerun_names(results, modules):
            print(name)
        return _COMPLETE
    report = mutation_report(results, modules, stopped_after=arguments.stopped_after)
    for line in report.lines:
        print(line)
    return _PARTIAL if report.partial else _COMPLETE


if __name__ == "__main__":
    raise SystemExit(main())
