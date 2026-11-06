"""The missing lines and the time line of the document check tests."""

import re

TOPIC_FILES = (
    "install.md",
    "agent-runtime.md",
    "machine.md",
    "site.md",
    "cloud-run.md",
    "health.md",
    "stops.md",
    "pipeline.md",
    "records.md",
    "work-items.md",
)
MISSING_LINES = (
    "README.md: missing\n"
    "docs/operator-guide/README.md: missing\n"
    + "".join(f"docs/operator-guide/{name}: missing\n" for name in TOPIC_FILES)
    + "docs/project-guide/README.md: missing\n"
    "docs/decisions.md: missing\n"
)
REPORT_HEADING = "Report (not checked yet):"
TIME_LINE = r"documents ok \(\d+(\.\d+)? s\)"


def line_of(text: str, line: str) -> int:
    """The 1-based number of the first line of `text` that equals `line`."""
    return text.splitlines().index(line) + 1


NOT_RUN = re.compile(r": not run \([^)]*\)\n\Z")


def without_report_lines(printed: list[str]) -> str:
    """`printed` without its `does not exist` lines, the report heading and the `not run` lines."""
    return "".join(
        line
        for line in printed
        if not line.endswith(" does not exist\n")
        and line != f"{REPORT_HEADING}\n"
        and NOT_RUN.search(line) is None
    )
