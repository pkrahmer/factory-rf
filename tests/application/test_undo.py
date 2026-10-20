"""The undo puts back every mark an agent may not leave, by the stage-start commit."""

import re
from collections.abc import Callable

import pytest

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.undo import UndoReport
from factory.application.write_paths import WritePathService
from factory.domain.errors import WorkItemFormatError
from factory.domain.journal import NewEntry, append_entry
from factory.domain.paths import cost_records_path
from factory.domain.write_paths import refusal
from git_support import PIPELINE_YAML, write_files
from human_clone import HumanClone
from undo_support import (
    GUIDE,
    GUIDE_TEXT,
    IN_PROGRESS,
    KEPT,
    PATH,
    PIPELINE_FILE,
    SECOND,
    pipeline_text,
    start_stage,
    undo_stage,
)
from work_item_support import checkout_text

THIRD_COSTS = f"{IN_PROGRESS}/F0001-S0003-third.costs.jsonl"
NOTES = f"{IN_PROGRESS}/notes.txt"
STORY_FORM_FILE = "factory/story-form.md"
BROKEN_FRONT_MATTER = "---\nstage: [unclosed\n  : :\n---\n# First story\n"
AGENT_TEXT = "written by the agent\n"


def _at_start(boundaries: Boundaries, start: StageStart, path: str) -> str:
    text = boundaries.git.show_file(start.commit, path)
    assert text is not None
    return text


def _edit_section(boundaries: Boundaries) -> str:
    target = boundaries.checkout / PATH
    edited = target.read_text(encoding="utf-8").replace("Original.", "Changed by the agent.")
    target.write_text(edited, encoding="utf-8")
    return edited


def test_a_modified_tracked_file_outside_the_write_paths_is_reverted(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    write_files(boundaries.checkout, {GUIDE: AGENT_TEXT})

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, GUIDE) == GUIDE_TEXT
    assert report.reverted == [GUIDE]
    assert report.deleted == []


def test_a_new_untracked_file_outside_the_write_paths_is_deleted(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    write_files(boundaries.checkout, {"docs/new.md": AGENT_TEXT})

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, "docs/new.md") is None
    assert report.deleted == ["docs/new.md"]
    assert report.reverted == []


def test_a_deleted_tracked_file_outside_the_write_paths_is_restored(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    (boundaries.checkout / GUIDE).unlink()

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, GUIDE) == GUIDE_TEXT
    assert report.reverted == [GUIDE]
    assert report.deleted == []


def test_a_file_changed_in_the_agents_own_commit_is_reverted_without_a_new_commit(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    write_files(boundaries.checkout, {GUIDE: AGENT_TEXT})
    agent_commit = boundaries.git.commit("the agent's own commit")
    head = boundaries.git.resolve("HEAD")

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, GUIDE) == GUIDE_TEXT
    assert report.reverted == [GUIDE]
    assert boundaries.git.resolve("HEAD") == head
    assert boundaries.git.is_ancestor(agent_commit, "HEAD")


def test_files_inside_the_write_paths_are_left_as_the_agent_wrote_them(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human, write_paths=["src/*", "{work_item}"])
    write_files(boundaries.checkout, {KEPT: AGENT_TEXT, "src/new.py": AGENT_TEXT})

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, KEPT) == AGENT_TEXT
    assert checkout_text(boundaries, "src/new.py") == AGENT_TEXT
    assert report.reverted == []
    assert report.deleted == []


def test_protected_paths_are_undone_although_a_write_path_matches_them(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human, write_paths=["*"])
    story_form = _at_start(boundaries, start, STORY_FORM_FILE)
    write_files(
        boundaries.checkout,
        {STORY_FORM_FILE: AGENT_TEXT, "pyproject.toml": AGENT_TEXT, "src/a.py": AGENT_TEXT},
    )

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, STORY_FORM_FILE) == story_form
    assert checkout_text(boundaries, "pyproject.toml") is None
    assert checkout_text(boundaries, "src/a.py") == AGENT_TEXT
    assert report.reverted == [STORY_FORM_FILE]
    assert report.deleted == ["pyproject.toml"]


def test_everything_else_in_an_in_progress_folder_is_undone_whatever_the_write_paths_say(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human, write_paths=["*"])
    second = _at_start(boundaries, start, SECOND)
    own_costs = cost_records_path(PATH)
    write_files(
        boundaries.checkout,
        {SECOND: AGENT_TEXT, own_costs: "{}\n", THIRD_COSTS: "{}\n", NOTES: AGENT_TEXT},
    )
    edited = _edit_section(boundaries)

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, SECOND) == second
    for path in (own_costs, THIRD_COSTS, NOTES):
        assert checkout_text(boundaries, path) is None
    assert report.reverted == [SECOND]
    assert report.deleted == sorted([own_costs, THIRD_COSTS, NOTES])
    assert checkout_text(boundaries, PATH) == edited


def test_files_not_directly_in_an_in_progress_folder_follow_the_write_paths(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human, write_paths=["*"])
    backlog = "factory/features/F0001-example/backlog"
    agent_files = {
        f"{backlog}/F0001-S0001-first.md": AGENT_TEXT,
        f"{backlog}/extra.md": AGENT_TEXT,
        f"{IN_PROGRESS}/sub/notes.txt": AGENT_TEXT,
        "src/in-progress/notes.txt": AGENT_TEXT,
    }
    assert _at_start(boundaries, start, f"{backlog}/F0001-S0001-first.md") != AGENT_TEXT
    write_files(boundaries.checkout, agent_files)

    report = undo_stage(boundaries, start)

    for path in agent_files:
        assert checkout_text(boundaries, path) == AGENT_TEXT
    assert report.reverted == []
    assert report.deleted == []


def test_the_work_items_state_and_journal_are_restored_and_its_section_edit_kept(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    baseline = boundaries.work_item_reader.parse(_at_start(boundaries, start, PATH))
    target = boundaries.checkout / PATH
    current = boundaries.work_item_reader.read(target)
    assert current.state is not None
    raised = current.model_copy(
        update={
            "state": current.state.model_copy(update={"attempts": 3}),
            "body": current.body.replace("Original.", "Changed by the agent."),
        }
    )
    entry = NewEntry(speaker="factory", kind="result", text="the agent wrote this.")
    boundaries.work_item_writer.write(target, append_entry(raised, entry))

    report = undo_stage(boundaries, start)

    restored = boundaries.work_item_reader.read(target)
    assert restored.state == baseline.state
    assert restored.body == baseline.body.replace("Original.", "Changed by the agent.")
    assert report.restored_work_item is True
    assert PATH not in report.reverted


def test_a_work_item_with_only_a_section_edit_is_left_as_the_agent_left_it(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    edited = _edit_section(boundaries)

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, PATH) == edited
    assert report.restored_work_item is False


def test_a_work_item_the_agent_deleted_is_restored_whole(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    (boundaries.checkout / PATH).unlink()

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, PATH) == _at_start(boundaries, start, PATH)
    assert report.restored_work_item is True
    assert PATH not in report.reverted
    assert PATH not in report.deleted


def test_a_work_item_the_agent_broke_is_restored_whole(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    write_files(boundaries.checkout, {PATH: BROKEN_FRONT_MATTER})

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, PATH) == _at_start(boundaries, start, PATH)
    assert report.restored_work_item is True
    assert PATH not in report.reverted
    assert PATH not in report.deleted


def test_a_work_item_the_role_may_not_write_is_reverted_whole(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human, stage="doing")
    _edit_section(boundaries)

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, PATH) == _at_start(boundaries, start, PATH)
    assert report.reverted == [PATH]
    assert report.restored_work_item is False


def test_a_widened_pipeline_definition_in_the_work_tree_widens_nothing(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    write_files(
        boundaries.checkout, {PIPELINE_FILE: pipeline_text(["*"]), "docs/extra.md": AGENT_TEXT}
    )

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, "docs/extra.md") is None
    assert "docs/extra.md" in report.deleted
    assert checkout_text(boundaries, PIPELINE_FILE) == PIPELINE_YAML


def test_an_invalid_pipeline_definition_in_the_work_tree_does_not_stop_the_undo(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    write_files(
        boundaries.checkout,
        {PIPELINE_FILE: "stages: [unclosed\n  : :\n", "docs/extra.md": AGENT_TEXT},
    )

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, PIPELINE_FILE) == PIPELINE_YAML
    assert checkout_text(boundaries, "docs/extra.md") is None
    assert "docs/extra.md" in report.deleted


def test_the_guard_refuses_exactly_what_the_undo_puts_back(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human, stage="doing")
    paths = ["src/a.py", "docs/a.md", "tests/t.py", "pyproject.toml", PIPELINE_FILE]
    settings = WritePathService(boundaries).at(start, PATH)
    refused = {path for path in paths if refusal(path, settings) is not None}
    write_files(boundaries.checkout, dict.fromkeys(paths, AGENT_TEXT))

    report = undo_stage(boundaries, start)

    assert refused == {"docs/a.md", "tests/t.py", "pyproject.toml", PIPELINE_FILE}
    assert set(report.reverted) | set(report.deleted) == refused


def test_the_lists_ascend_without_repeats_and_a_second_undo_finds_nothing(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human)
    write_files(
        boundaries.checkout,
        {
            "tests/z.py": AGENT_TEXT,
            "docs/b.md": AGENT_TEXT,
            "a.txt": AGENT_TEXT,
            GUIDE: AGENT_TEXT,
            KEPT: AGENT_TEXT,
            PIPELINE_FILE: AGENT_TEXT,
        },
    )
    target = boundaries.checkout / PATH
    target.write_text(
        target.read_text(encoding="utf-8").replace("attempts: 0", "attempts: 4"), encoding="utf-8"
    )

    first = undo_stage(boundaries, start)
    second = undo_stage(boundaries, start)

    assert first.reverted == sorted(set(first.reverted))
    assert first.deleted == sorted(set(first.deleted))
    assert first.reverted == [GUIDE, PIPELINE_FILE, KEPT]
    assert first.deleted == ["a.txt", "docs/b.md", "tests/z.py"]
    assert first.restored_work_item is True
    assert second == UndoReport(reverted=[], deleted=[], restored_work_item=False)


def _without_work_item(boundaries: Boundaries, start: StageStart) -> StageStart:
    commit = boundaries.git.resolve("origin/main")
    assert commit is not None
    return StageStart(commit=commit, claim=start.claim)


def _with_broken_work_item(boundaries: Boundaries, start: StageStart) -> StageStart:
    write_files(boundaries.checkout, {PATH: BROKEN_FRONT_MATTER})
    commit = boundaries.git.commit("break the work item")
    return StageStart(commit=commit, claim=start.claim)


@pytest.mark.parametrize("baseline", [_without_work_item, _with_broken_work_item])
def test_a_missing_or_unreadable_baseline_raises_before_any_path_is_changed(
    boundaries: Boundaries,
    human: HumanClone,
    baseline: Callable[[Boundaries, StageStart], StageStart],
) -> None:
    start = baseline(boundaries, start_stage(boundaries, human))
    write_files(boundaries.checkout, {GUIDE: AGENT_TEXT})

    with pytest.raises(WorkItemFormatError, match=re.escape(PATH)):
        undo_stage(boundaries, start)

    assert checkout_text(boundaries, GUIDE) == AGENT_TEXT
