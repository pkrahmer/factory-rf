"""What the document check tests share: the expected lines, the output filters, the block helper."""

import re
from collections.abc import Sequence
from pathlib import Path

from factory.shared.domain.documents import CHECKED_DOCUMENTS, OPERATOR_INSTALL
from support.document_texts import FENCE
from support.git_support import commit_all

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
NOT_RUN = re.compile(r": not run \([^)]*\)\n\Z")


def line_of(text: str, line: str) -> int:
    """The 1-based number of the first line of `text` that equals `line`."""
    return text.splitlines().index(line) + 1


def without_report_lines(printed: list[str]) -> str:
    """`printed` without its `does not exist` lines, the report heading and the `not run` lines."""
    return "".join(
        line
        for line in printed
        if not line.endswith(" does not exist\n")
        and line != f"{REPORT_HEADING}\n"
        and NOT_RUN.search(line) is None
    )


def append_block(root: Path, document: str, info: str, lines: list[str]) -> int:
    """Append a fenced block to `document` under `root`, commit; the line of its opening fence."""
    path = root / document
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    first_line = len(text.splitlines()) + 2
    text += "\n" + "\n".join([f"{FENCE}{info}", *lines, FENCE]) + "\n"
    path.write_text(text, encoding="utf-8")
    commit_all(root, "A block")
    return first_line


def findings_from(lines: list[str], document: str, first_line: int) -> list[str]:
    """The lines about `document` that name a line at or after `first_line`."""
    pattern = re.compile(rf"{re.escape(document)}:(\d+): ")
    return [
        line
        for line in lines
        if (found := pattern.match(line)) is not None and int(found.group(1)) >= first_line
    ]


def write_checked_list(root: Path, paths: Sequence[str]) -> None:
    """Write the list of checked documents under `root`, one path per line; commit a change."""
    text = "".join(f"{path}\n" for path in paths)
    path = root / CHECKED_DOCUMENTS
    # An unchanged list would make the commit empty, and `commit_all` would fail.
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")
    commit_all(root, "The checked documents")


def drop_settings_row(root: Path, name: str) -> None:
    """Remove the settings table row of `name` from the install file under `root`."""
    path = root / OPERATOR_INSTALL
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if not line.startswith(f"| `{name}` |")]
    assert len(kept) == len(lines) - 1
    path.write_text("".join(kept), encoding="utf-8")
