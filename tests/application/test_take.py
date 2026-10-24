"""The take copies from the dataset into the work tree what the role may write; the rest stays."""

from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.domain.paths import cost_records_path
from git_support import run_git
from human_clone import HumanClone
from take_support import (
    AGENT_TEXT,
    BROKEN_FRONT_MATTER,
    changes,
    make_dataset,
    run_take,
    tree,
    write_dataset,
)
from undo_support import GUIDE, GUIDE_TEXT, IN_PROGRESS, KEPT, PATH, SECOND, start_stage
from work_item_support import checkout_text

STORY_FORM_FILE = "factory/story-form.md"
OLD = "src/old.py"
OLD_TEXT = "gone = 1\n"
NEW = "src/new.py"
SECOND_TEXT = "# Second story\n\nAs committed.\n"


def _at_start(boundaries: Boundaries, start: StageStart, path: str) -> str:
    text = boundaries.git.show_file(start.commit, path)
    assert text is not None
    return text


def _with_old(boundaries: Boundaries, human: HumanClone, write_paths: list[str]) -> StageStart:
    # `src/old.py` is on `main`, so the host holds it for the agent's deletion to remove.
    human.push_file("main", OLD, OLD_TEXT)
    return start_stage(boundaries, human, write_paths=write_paths)


def _agent_writes_src(mount_point: Path) -> None:
    write_dataset(mount_point, {f"checkout/{NEW}": AGENT_TEXT, f"checkout/{KEPT}": AGENT_TEXT})
    (mount_point / "checkout" / OLD).unlink()


SRC_CHANGES = (
    (f"checkout/{NEW}", "added"),
    (f"checkout/{KEPT}", "modified"),
    (f"checkout/{OLD}", "deleted"),
)


@pytest.mark.parametrize(
    ("write_paths", "agent", "changed", "host", "left"),
    [
        pytest.param(
            ["src/*", "{work_item}"],
            {},
            SRC_CHANGES,
            {NEW: AGENT_TEXT, KEPT: AGENT_TEXT, OLD: None},
            [],
            id="inside-the-write-paths",
        ),
        pytest.param(
            ["src/*", "{work_item}"],
            {f"checkout/{GUIDE}": AGENT_TEXT},
            ((f"checkout/{GUIDE}", "modified"),),
            {GUIDE: GUIDE_TEXT},
            [GUIDE],
            id="outside-the-write-paths",
        ),
        pytest.param(
            ["*"],
            {"checkout/pyproject.toml": AGENT_TEXT, f"checkout/{STORY_FORM_FILE}": AGENT_TEXT},
            (("checkout/pyproject.toml", "added"), (f"checkout/{STORY_FORM_FILE}", "modified")),
            {"pyproject.toml": None, STORY_FORM_FILE: "as at the start"},
            [STORY_FORM_FILE, "pyproject.toml"],
            id="protected",
        ),
    ],
)
def test_a_changed_path_is_taken_only_where_the_role_may_write(
    boundaries: Boundaries,
    human: HumanClone,
    tmp_path: Path,
    *,
    write_paths: list[str],
    agent: dict[str, str],
    changed: tuple[tuple[str, str], ...],
    host: dict[str, str | None],
    left: list[str],
) -> None:
    start = _with_old(boundaries, human, write_paths)
    mount_point = make_dataset(boundaries, tmp_path)
    if changed == SRC_CHANGES:
        _agent_writes_src(mount_point)
    write_dataset(mount_point, agent)
    story_form = _at_start(boundaries, start, STORY_FORM_FILE)

    report = run_take(boundaries, start, mount_point, changes(*changed))

    for path, text in host.items():
        expected = story_form if text == "as at the start" else text
        assert checkout_text(boundaries, path) == expected, path
    for path in left:
        assert (mount_point / "checkout" / path).read_text(encoding="utf-8") == AGENT_TEXT
    assert report.left == left


@pytest.mark.parametrize(
    ("path", "change", "left"),
    [
        pytest.param(SECOND, "modified", True, id="second-work-item"),
        pytest.param(cost_records_path(PATH), "added", True, id="own-cost-record"),
        pytest.param(f"{IN_PROGRESS}/notes.txt", "added", True, id="notes"),
        pytest.param(f"{IN_PROGRESS}/sub/x", "added", False, id="below-the-folder"),
    ],
)
def test_every_other_file_directly_in_an_in_progress_folder_is_left(
    boundaries: Boundaries,
    human: HumanClone,
    tmp_path: Path,
    *,
    path: str,
    change: str,
    left: bool,
) -> None:
    start = start_stage(boundaries, human, write_paths=["*"])
    mount_point = make_dataset(boundaries, tmp_path)
    write_dataset(mount_point, {f"checkout/{path}": AGENT_TEXT})
    before = checkout_text(boundaries, path)

    report = run_take(boundaries, start, mount_point, changes((f"checkout/{path}", change)))

    if left:
        assert report.left == [path]
        assert checkout_text(boundaries, path) == before
        assert before in (None, SECOND_TEXT)
    else:
        assert report.left == []
        assert checkout_text(boundaries, path) == AGENT_TEXT


def _edit(mount_point: Path, *, state: bool) -> str:
    target = mount_point / "checkout" / PATH
    edited = target.read_text(encoding="utf-8").replace("Original.", "Changed by the agent.")
    if state:
        assert "stage: intake" in edited
        edited = edited.replace("stage: intake", "stage: done")
    target.write_text(edited, encoding="utf-8")
    return edited


@pytest.mark.parametrize(
    ("case", "write_paths", "change", "restored", "left"),
    [
        pytest.param("section-and-state", None, "modified", True, [], id="section-and-state"),
        pytest.param("section-only", None, "modified", False, [], id="section-only"),
        pytest.param("deleted", None, "deleted", True, [], id="deleted"),
        pytest.param("broken", None, "modified", True, [], id="broken"),
        pytest.param("section-only", ["src/*"], "modified", False, [PATH], id="not-writable"),
    ],
)
def test_the_work_items_state_and_journal_come_back_from_the_stage_start(
    boundaries: Boundaries,
    human: HumanClone,
    tmp_path: Path,
    *,
    case: str,
    write_paths: list[str] | None,
    change: str,
    restored: bool,
    left: list[str],
) -> None:
    start = start_stage(boundaries, human, write_paths=write_paths)
    at_start = _at_start(boundaries, start, PATH)
    baseline = boundaries.work_item_reader.parse(at_start)
    mount_point = make_dataset(boundaries, tmp_path)
    dataset_item = mount_point / "checkout" / PATH
    edited = ""
    if case == "deleted":
        dataset_item.unlink()
    elif case == "broken":
        dataset_item.write_text(BROKEN_FRONT_MATTER, encoding="utf-8")
    else:
        edited = _edit(mount_point, state=case == "section-and-state")

    report = run_take(boundaries, start, mount_point, changes((f"checkout/{PATH}", change)))

    assert report.restored_work_item is restored
    assert report.left == left
    if case == "section-and-state":
        host = boundaries.work_item_reader.read(boundaries.checkout / PATH)
        assert host.state == baseline.state
        assert host.body == baseline.body.replace("Original.", "Changed by the agent.")
    elif case == "section-only" and write_paths is None:
        assert checkout_text(boundaries, PATH) == edited
    else:
        assert checkout_text(boundaries, PATH) == at_start


def test_left_ascends_and_holds_a_path_given_twice_once(
    boundaries: Boundaries, human: HumanClone, tmp_path: Path
) -> None:
    start = start_stage(boundaries, human)
    mount_point = make_dataset(boundaries, tmp_path)
    write_dataset(mount_point, {f"checkout/{GUIDE}": AGENT_TEXT, "checkout/a.txt": AGENT_TEXT})
    changed = changes(
        (f"checkout/{GUIDE}", "modified"),
        ("checkout/a.txt", "added"),
        (f"checkout/{GUIDE}", "modified"),
    )

    report = run_take(boundaries, start, mount_point, changed)

    assert report.left == ["a.txt", GUIDE]


def test_the_take_writes_nothing_in_the_dataset_and_no_commit(
    boundaries: Boundaries, human: HumanClone, tmp_path: Path
) -> None:
    start = _with_old(boundaries, human, ["src/*", "{work_item}"])
    mount_point = make_dataset(boundaries, tmp_path)
    _agent_writes_src(mount_point)
    _edit(mount_point, state=True)
    dataset = tree(mount_point)
    head = boundaries.git.resolve("HEAD")
    commits = run_git(boundaries.checkout, "rev-list", "--all", "--count")

    report = run_take(
        boundaries, start, mount_point, changes(*SRC_CHANGES, (f"checkout/{PATH}", "modified"))
    )

    assert report.restored_work_item is True
    assert checkout_text(boundaries, NEW) == AGENT_TEXT
    assert tree(mount_point) == dataset
    assert boundaries.git.resolve("HEAD") == head
    assert run_git(boundaries.checkout, "rev-list", "--all", "--count") == commits
