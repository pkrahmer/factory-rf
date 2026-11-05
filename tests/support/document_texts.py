"""Builders for the documents' texts, the operator guide's files included, clean unless asked."""

from collections.abc import Sequence
from pathlib import Path

from factory.pipeline.domain.fault_paths import FAULT_PATHS
from factory.pipeline.domain.stop_table import STOP_TABLE, StopRow
from factory.shared.domain.documents import (
    DECISION_LOG,
    OPERATOR_GUIDE,
    OPERATOR_GUIDE_FILES,
    OPERATOR_INSTALL,
    OPERATOR_STOPS,
    PROJECT_GUIDE,
    PROJECT_GUIDE_SECTIONS,
    README,
)
from factory.shared.domain.kill_point_cases import KILL_POINT_CASES

DESTINATION_WORDS = {
    "health_status": "health status",
    "pull_request": "pull request",
    "none": "no stop",
}
INSTALL_SECTIONS = ("Install", "Configuration")
STOPS_SECTIONS = ("The stops",)
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


def operator_index(*, prefix: str = "", suffix: str = "") -> str:
    """A clean index of the operator guide, with optional text before and after its body."""
    return _document("Operator guide", ("Topics",), (), prefix, suffix)


def operator_install(
    *, sections: Sequence[str] = INSTALL_SECTIONS, prefix: str = "", suffix: str = ""
) -> str:
    """The operator guide's `install.md` with the given sections."""
    return _document("Install", sections, (), prefix, suffix)


def operator_stops(
    *,
    sections: Sequence[str] = STOPS_SECTIONS,
    without_stop: str | None = None,
    extra_rows: Sequence[str] = (),
    prefix: str = "",
    suffix: str = "",
) -> str:
    """The guide's `stops.md`: the given sections and one row per stop but `without_stop`."""
    rows = [stop_row(row) for row in STOP_TABLE if row.id != without_stop]
    return _document("The stops", sections, [*rows, *extra_rows], prefix, suffix)


def operator_topic(*, prefix: str = "", suffix: str = "") -> str:
    """A clean topic file of the operator guide that has no required section."""
    return _document("A topic", ("Running it",), (), prefix, suffix)


def operator_file(path: str, *, prefix: str = "", suffix: str = "") -> str:
    """The clean text of the operator guide's index or topic file at `path`, with extra text."""
    if path == OPERATOR_GUIDE:
        return operator_index(prefix=prefix, suffix=suffix)
    if path == OPERATOR_INSTALL:
        return operator_install(prefix=prefix, suffix=suffix)
    if path == OPERATOR_STOPS:
        return operator_stops(prefix=prefix, suffix=suffix)
    return operator_topic(prefix=prefix, suffix=suffix)


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
    """Every document, the operator guide's index and topic files included, each clean."""
    return {
        README: readme(),
        OPERATOR_GUIDE: operator_index(),
        **{path: operator_file(path) for path in OPERATOR_GUIDE_FILES},
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
