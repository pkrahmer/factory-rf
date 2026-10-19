"""The duplicates command: pylint's and vulture's output compared with a baseline of keys."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from factory.domain.duplicates import (
    DuplicateFinding,
    compare,
    dead_code_findings,
    read_baseline,
    report_lines,
    similar_code_findings,
)
from factory.entry.inputs import UnreadableInput, read_input

_PROGRAM = "check-duplicates"
_BASELINE_HEADER = "# Accepted findings of make duplicates, one key per line."
_NOTHING_NEW = 0
_SOMETHING_NEW = 1
_FAILURE = 2


def _findings(pylint: Path, vulture: Path) -> list[DuplicateFinding]:
    try:
        return similar_code_findings(read_input(pylint)) + dead_code_findings(read_input(vulture))
    except ValueError as error:
        raise UnreadableInput(str(error)) from error


def _write_baseline(path: Path, findings: Sequence[DuplicateFinding]) -> int:
    keys = list(dict.fromkeys(finding.key for finding in findings))
    path.write_text("".join(f"{line}\n" for line in [_BASELINE_HEADER, *keys]), encoding="utf-8")
    print(f"duplicates: baseline of {len(keys)} findings written to {path}")
    return _NOTHING_NEW


def _report(baseline: Path, findings: Sequence[DuplicateFinding]) -> int:
    report = compare(findings, read_baseline(read_input(baseline)))
    for line in report_lines(report):
        print(line)
    return _SOMETHING_NEW if report.new else _NOTHING_NEW


def main(argv: Sequence[str] | None = None) -> int:
    """Print the report and return 1 when a finding is new, 0 otherwise, 2 on unreadable input."""
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("pylint", type=Path)
    parser.add_argument("vulture", type=Path)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--write-baseline", action="store_true")
    arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    baseline: Path = arguments.baseline
    try:
        findings = _findings(arguments.pylint, arguments.vulture)
        if arguments.write_baseline:
            return _write_baseline(baseline, findings)
        return _report(baseline, findings)
    except UnreadableInput as error:
        print(f"{_PROGRAM}: {error}", file=sys.stderr)
        return _FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
