"""Builders for the four documents' texts, clean unless a test asks for a fault."""

from collections.abc import Sequence
from pathlib import Path

from factory.domain.documents import (
    DECISION_LOG,
    OPERATOR_GUIDE,
    OPERATOR_GUIDE_SECTIONS,
    PROJECT_GUIDE,
    PROJECT_GUIDE_SECTIONS,
    README,
)
from factory.domain.fault_paths import FAULT_PATHS
from factory.domain.kill_point_cases import KILL_POINT_CASES
from factory.domain.stop_table import STOP_TABLE, StopRow

DESTINATION_WORDS = {
    "health_status": "health status",
    "pull_request": "pull request",
    "none": "no stop",
}
PATH_7_TEST = "test_round_cap_question_killed_between_post_and_record_posts_once_and_waits"


def stop_row(row: StopRow) -> str:
    """The table row of one stop, its id in backticks and its destination in words."""
    return f"| `{row.id}` | {DESTINATION_WORDS[row.destination]} |"


def _document(
    title: str, sections: Sequence[str], rows: Sequence[str], prefix: str, suffix: str
) -> str:
    lines = [f"# {title}", "", prefix, ""]
    for name in sections:
        lines += [f"## {name}", "", "The factory works on work items.", ""]
    lines += [*rows, "", suffix, ""]
    return "\n".join(lines)


def readme(*, prefix: str = "", suffix: str = "") -> str:
    """A clean README, with optional text before and after its body."""
    return _document("The factory", ("Running it",), (), prefix, suffix)


def operator_guide(
    *,
    sections: Sequence[str] = OPERATOR_GUIDE_SECTIONS,
    without_stop: str | None = None,
    extra_rows: Sequence[str] = (),
    prefix: str = "",
    suffix: str = "",
) -> str:
    """An operator guide: the given sections and one row per stop but `without_stop`."""
    rows = [stop_row(row) for row in STOP_TABLE if row.id != without_stop]
    return _document("Operator guide", sections, [*rows, *extra_rows], prefix, suffix)


def project_guide(
    *,
    sections: Sequence[str] = PROJECT_GUIDE_SECTIONS,
    without_case: str | None = None,
    without_path: int | None = None,
    extra_rows: Sequence[str] = (),
    prefix: str = "",
    suffix: str = "",
) -> str:
    """A project guide: the given sections and one row per case and per path but those left out."""
    rows = [
        f"| `{case.id}` | {case.dies} |" for case in KILL_POINT_CASES if case.id != without_case
    ]
    rows += [
        f"| {path.number} | `{path.test}` |" for path in FAULT_PATHS if path.number != without_path
    ]
    return _document("Project guide", sections, [*rows, *extra_rows], prefix, suffix)


def decision_log(*, suffix: str = "") -> str:
    """A clean decision log with one decision, and optional text after it."""
    return f"# Decisions\n\n## 001 One package\n\nOne package under src.\n\n{suffix}\n"


def clean_texts() -> dict[str, str | None]:
    """The four documents, each clean."""
    return {
        README: readme(),
        OPERATOR_GUIDE: operator_guide(),
        PROJECT_GUIDE: project_guide(),
        DECISION_LOG: decision_log(),
    }


def write_documents(root: Path, texts: dict[str, str | None]) -> None:
    """Write each text that is not None under root as UTF-8 bytes."""
    for path, text in texts.items():
        if text is None:
            continue
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))
