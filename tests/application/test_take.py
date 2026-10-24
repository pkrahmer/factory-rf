"""The take copies from the dataset into the work tree what the role may write, and no more."""

from collections.abc import Callable

import pytest

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.domain.git import ChangeKind
from factory.domain.paths import cost_records_path
from human_clone import HumanClone
from take_support import (
    AGENT_TEXT,
    DATASET_CHECKOUT,
    changed,
    copy_work_item_to_dataset,
    dataset_of,
    dataset_text,
    take_stage,
    write_dataset,
)
from undo_support import GUIDE, GUIDE_TEXT, IN_PROGRESS, KEPT, PATH, SECOND, start_stage
from work_item_support import checkout_text

STORY_FORM_FILE = "factory/story-form.md"
BROKEN_FRONT_MATTER = "---\nstage: [unclosed\n  : :\n---\n# First story\n"
OWN_WRITE_PATHS = ["src/*", "{work_item}"]


def _at_start(boundaries: Boundaries, start: StageStart, path: str) -> str:
    text = boundaries.git.show_file(start.commit, path)
    assert text is not None
    return text


@pytest.mark.parametrize(
    ("write_paths", "agent", "changes", "host", "unchanged", "left"),
    [
        pytest.param(
            OWN_WRITE_PATHS,
            {"src/new.py": AGENT_TEXT, KEPT: AGENT_TEXT},
            [("src/new.py", "added"), (KEPT, "modified"), ("src/old.py", "deleted")],
            {"src/new.py": AGENT_TEXT, KEPT: AGENT_TEXT, "src/old.py": None},
            [],
            [],
            id="taken",
        ),
        pytest.param(
            OWN_WRITE_PATHS,
            {GUIDE: AGENT_TEXT},
            [(GUIDE, "modified")],
            {GUIDE: GUIDE_TEXT},
            [],
            [GUIDE],
            id="outside-the-write-paths",
        ),
        pytest.param(
            ["*"],
            {"pyproject.toml": AGENT_TEXT, STORY_FORM_FILE: AGENT_TEXT},
            [("pyproject.toml", "added"), (STORY_FORM_FILE, "modified")],
            {"pyproject.toml": None},
            [STORY_FORM_FILE],
            [STORY_FORM_FILE, "pyproject.toml"],
            id="protected",
        ),
    ],
)
def test_the_take_copies_what_the_role_may_write_and_leaves_the_rest(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    write_paths: list[str],
    agent: dict[str, str],
    changes: list[tuple[str, ChangeKind]],
    host: dict[str, str | None],
    unchanged: list[str],
    left: list[str],
) -> None:
    start = start_stage(boundaries, human, write_paths=write_paths)
    (boundaries.checkout / "src" / "old.py").write_text("old\n", encoding="utf-8")
    before = {path: checkout_text(boundaries, path) for path in unchanged}
    write_dataset(boundaries, agent)

    report = take_stage(boundaries, start, [changed(path, kind) for path, kind in changes])

    assert {path: checkout_text(boundaries, path) for path in host} == host
    assert {path: checkout_text(boundaries, path) for path in unchanged} == before
    assert {path: dataset_text(boundaries, path) for path in agent} == agent
    assert report.left == left


@pytest.mark.parametrize(
    ("path", "change", "is_left"),
    [
        pytest.param(SECOND, "modified", True, id="second-work-item"),
        pytest.param(cost_records_path(PATH), "added", True, id="own-cost-record"),
        pytest.param(f"{IN_PROGRESS}/notes.txt", "added", True, id="notes"),
        pytest.param(f"{IN_PROGRESS}/sub/x", "added", False, id="below-in-progress"),
    ],
)
def test_everything_else_directly_in_an_in_progress_folder_is_left_whatever_the_write_paths(
    boundaries: Boundaries, human: HumanClone, *, path: str, change: ChangeKind, is_left: bool
) -> None:
    start = start_stage(boundaries, human, write_paths=["*"])
    before = checkout_text(boundaries, path)
    write_dataset(boundaries, {path: AGENT_TEXT})

    report = take_stage(boundaries, start, [changed(path, change)])

    if is_left:
        assert report.left == [path]
        assert checkout_text(boundaries, path) == before
    else:
        assert report.left == []
        assert checkout_text(boundaries, path) == AGENT_TEXT


def _section_and_state(text: str) -> str | None:
    edited = text.replace("Original.", "Changed by the agent.").replace(
        "stage: intake", "stage: done"
    )
    assert "stage: done" in edited
    return edited


def _section(text: str) -> str | None:
    return text.replace("Original.", "Changed by the agent.")


def _deleted(text: str) -> str | None:
    del text
    return None


def _broken(text: str) -> str | None:
    del text
    return BROKEN_FRONT_MATTER


@pytest.mark.parametrize(
    ("write_paths", "edit", "expected", "restored", "is_left"),
    [
        pytest.param(
            OWN_WRITE_PATHS, _section_and_state, "baseline-state", True, False, id="state"
        ),
        pytest.param(OWN_WRITE_PATHS, _section, "agent", False, False, id="section-only"),
        pytest.param(OWN_WRITE_PATHS, _deleted, "start", True, False, id="deleted"),
        pytest.param(OWN_WRITE_PATHS, _broken, "start", True, False, id="broken"),
        pytest.param(["src/*"], _section, "start", False, True, id="not-writable"),
    ],
)
def test_the_work_items_state_and_journal_come_back_from_the_stage_start(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    write_paths: list[str],
    edit: Callable[[str], str | None],
    expected: str,
    restored: bool,
    is_left: bool,
) -> None:
    start = start_stage(boundaries, human, write_paths=write_paths)
    edited = edit(copy_work_item_to_dataset(boundaries))
    if edited is None:
        change: ChangeKind = "deleted"
        (dataset_of(boundaries) / DATASET_CHECKOUT / PATH).unlink()
    else:
        change = "modified"
        write_dataset(boundaries, {PATH: edited})

    report = take_stage(boundaries, start, [changed(PATH, change)])

    at_start = _at_start(boundaries, start, PATH)
    if expected == "baseline-state":
        assert edited is not None
        baseline = boundaries.work_item_reader.parse(at_start)
        taken = boundaries.work_item_reader.read(boundaries.checkout / PATH)
        assert taken.state == baseline.state
        assert taken.body == baseline.body.replace("Original.", "Changed by the agent.")
    elif expected == "agent":
        assert checkout_text(boundaries, PATH) == edited
    else:
        assert checkout_text(boundaries, PATH) == at_start
    assert report.restored_work_item is restored
    assert report.left == ([PATH] if is_left else [])
