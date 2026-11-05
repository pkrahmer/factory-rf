"""The duplicates report: similar and dead code keyed without line numbers, against a baseline."""

import json
import re
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, NonNegativeInt

_DUPLICATE_CODE = "duplicate-code"
_MODULE_LINE_PREFIX = "=="
_MODULE_LINE = re.compile(r"==(?P<module>[\w.]+):\[\d+:\d+\]")
_DEAD_CODE_LINE = re.compile(
    r"(?P<path>[^\s:][^:]*):(?P<line>\d+): (?P<message>.+)"
    r" \((?P<confidence>\d+)% confidence(?:, \d+ lines?)?\)"
)
_COMMENT_PREFIX = "#"


class DuplicateFinding(BaseModel):
    """A similar block or dead code: its line-independent key, where it is, what it is."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    where: str
    message: str


class DuplicateReport(BaseModel):
    """The findings not in the baseline, the count of those in it, and baseline keys not found."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    new: list[DuplicateFinding]
    known: NonNegativeInt
    gone: list[str]


def _pylint_messages(pylint_json: str) -> list[str]:
    try:
        loaded: object = json.loads(pylint_json)
    except json.JSONDecodeError as error:
        raise ValueError(f"pylint output is not JSON: {error}") from error
    if not isinstance(loaded, list):
        raise ValueError("pylint output is not a JSON array")
    messages: list[str] = []
    for element in loaded:
        if not isinstance(element, dict):
            raise ValueError(f"pylint output holds an element that is not an object: {element!r}")
        if element.get("symbol") != _DUPLICATE_CODE:
            continue
        message = element.get("message")
        if not isinstance(message, str):
            raise ValueError(f"duplicate-code object without a string message: {element!r}")
        messages.append(message)
    return messages


def _similar_code_finding(message: str) -> DuplicateFinding:
    lines = message.splitlines()
    places: list[str] = []
    modules: set[str] = set()
    index = 1
    while index < len(lines) and lines[index].startswith(_MODULE_LINE_PREFIX):
        matched = _MODULE_LINE.fullmatch(lines[index])
        if matched is None:
            raise ValueError(f"duplicate-code message with a malformed module line: {message!r}")
        places.append(lines[index].removeprefix(_MODULE_LINE_PREFIX))
        modules.add(matched["module"])
        index += 1
    if not places:
        raise ValueError(f"duplicate-code message without a module line: {message!r}")
    code = [line.strip() for line in lines[index:] if line.strip()]
    if not code:
        raise ValueError(f"duplicate-code message without a code line: {message!r}")
    return DuplicateFinding(
        key=f"similar-code {', '.join(sorted(modules))}: {code[0]}",
        where=", ".join(places),
        message=lines[0],
    )


def similar_code_findings(pylint_json: str) -> list[DuplicateFinding]:
    """Return one finding per `duplicate-code` message of pylint's JSON output."""
    return [_similar_code_finding(message) for message in _pylint_messages(pylint_json)]


def dead_code_findings(vulture_text: str) -> list[DuplicateFinding]:
    """Return one finding per line of vulture's output; blank lines are skipped."""
    findings: list[DuplicateFinding] = []
    for number, line in enumerate(vulture_text.splitlines(), start=1):
        if not line.strip():
            continue
        matched = _DEAD_CODE_LINE.fullmatch(line)
        if matched is None:
            raise ValueError(f"vulture line {number} is not in vulture's form: {line!r}")
        findings.append(
            DuplicateFinding(
                key=f"dead-code {matched['path']}: {matched['message']}",
                where=f"{matched['path']}:{matched['line']}",
                message=f"{matched['message']} ({matched['confidence']}% confidence)",
            )
        )
    return findings


def read_baseline(text: str) -> list[str]:
    """Return the baseline's keys in order, without blank and comment lines."""
    stripped = (line.strip() for line in text.splitlines())
    return [line for line in stripped if line and not line.startswith(_COMMENT_PREFIX)]


def compare(findings: Sequence[DuplicateFinding], baseline: Sequence[str]) -> DuplicateReport:
    """Split the findings into new and known, and name the baseline keys no finding has."""
    accepted = set(baseline)
    found = {finding.key for finding in findings}
    return DuplicateReport(
        new=[finding for finding in findings if finding.key not in accepted],
        known=sum(1 for finding in findings if finding.key in accepted),
        gone=[key for key in baseline if key not in found],
    )


def report_lines(report: DuplicateReport) -> list[str]:
    """Return the `new` lines, the `gone` lines and the closing count line."""
    lines = [f"new {finding.key} at {finding.where}: {finding.message}" for finding in report.new]
    lines += [f"gone {key}" for key in report.gone]
    lines.append(
        f"duplicates: {len(report.new)} new, {report.known} known, {len(report.gone)} gone"
    )
    return lines
