"""The undo puts back every mark an agent may not leave, by the stage-start commit."""

import json
import re
from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.adapters.claude_guard import judge
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart
from factory.application.undo import UndoReport, UndoService
from factory.application.write_paths import WritePathService
from factory.domain.errors import WorkItemFormatError
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord, NewEntry, append_entry
from factory.domain.paths import cost_records_path
from factory.domain.work_item import WorkItemDocument, initial_state
from git_support import PIPELINE_YAML, write_files
from human_clone import HumanClone

INSTANCE = "factory-1"
BRANCH = branch_name("F0001-S0001")
IN_PROGRESS = "factory/features/F0001-example/in-progress"
PATH = f"{IN_PROGRESS}/F0001-S0001-first.md"
SECOND = f"{IN_PROGRESS}/F0001-S0002-second.md"
THIRD_COSTS = f"{IN_PROGRESS}/F0001-S0003-third.costs.jsonl"
NOTES = f"{IN_PROGRESS}/notes.txt"
PIPELINE_FILE = "factory/pipeline.yml"
STORY_FORM_FILE = "factory/story-form.md"
GUIDE = "docs/guide.md"
GUIDE_TEXT = "# Guide\n\nAs committed.\n"
KEPT = "src/kept.py"
KEPT_TEXT = "x = 1\n"
BODY = (
    "# First story\n\n## Description\n\nOriginal.\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
)
CREATED = JournalRecord(number=1, speaker="human", kind="created")
INTAKE_ROLE = 'intake: {write_paths: ["{work_item}"]}'
BASE_FILES = {GUIDE: GUIDE_TEXT, KEPT: KEPT_TEXT, SECOND: "# Second story\n\nAs committed.\n"}
BROKEN_FRONT_MATTER = "---\nstage: [unclosed\n  : :\n---\n# First story\n"
AGENT_TEXT = "written by the agent\n"


def _pipeline(write_paths: list[str] | None) -> str:
    if write_paths is None:
        return PIPELINE_YAML
    return PIPELINE_YAML.replace(INTAKE_ROLE, f"intake: {{write_paths: {json.dumps(write_paths)}}}")


def _start(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    stage: str = "intake",
    write_paths: list[str] | None = None,
) -> StageStart:
    """Push the definition, commit the work item and the base files on its branch, claim."""
    text = _pipeline(write_paths)
    if text != PIPELINE_YAML:
        human.push_file("main", PIPELINE_FILE, text)
    git = boundaries.git
    git.fetch()
    git.checkout(BRANCH, start_point="origin/main")
    write_files(boundaries.checkout, BASE_FILES)
    state = initial_state(stage).model_copy(update={"journal": [CREATED]})
    document = WorkItemDocument(state=state, body=BODY)
    target = boundaries.checkout / PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    boundaries.work_item_writer.write(target, document)
    git.commit("prepare the work item")
    assert git.push(BRANCH) == "pushed"
    definition = boundaries.pipeline_reader.parse(text)
    return ClaimService(boundaries, INSTANCE, definition).claim(BRANCH, PATH, document, stage)


def _text(boundaries: Boundaries, path: str) -> str | None:
    target = boundaries.checkout / path
    return target.read_text(encoding="utf-8") if target.exists() else None


def _at_start(boundaries: Boundaries, start: StageStart, path: str) -> str:
    text = boundaries.git.show_file(start.commit, path)
    assert text is not None
    return text


def _edit_section(boundaries: Boundaries) -> str:
    target = boundaries.checkout / PATH
    edited = target.read_text(encoding="utf-8").replace("Original.", "Changed by the agent.")
    target.write_text(edited, encoding="utf-8")
    return edited


def _payload(file_path: Path) -> str:
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(file_path)}})


def _undo(boundaries: Boundaries, start: StageStart) -> UndoReport:
    return UndoService(boundaries).undo(start, PATH)


def test_a_modified_tracked_file_outside_the_write_paths_is_reverted(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
    write_files(boundaries.checkout, {GUIDE: AGENT_TEXT})

    report = _undo(boundaries, start)

    assert _text(boundaries, GUIDE) == GUIDE_TEXT
    assert report.reverted == [GUIDE]
    assert report.deleted == []


def test_a_new_untracked_file_outside_the_write_paths_is_deleted(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
    write_files(boundaries.checkout, {"docs/new.md": AGENT_TEXT})

    report = _undo(boundaries, start)

    assert _text(boundaries, "docs/new.md") is None
    assert report.deleted == ["docs/new.md"]
    assert report.reverted == []


def test_a_deleted_tracked_file_outside_the_write_paths_is_restored(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
    (boundaries.checkout / GUIDE).unlink()

    report = _undo(boundaries, start)

    assert _text(boundaries, GUIDE) == GUIDE_TEXT
    assert report.reverted == [GUIDE]
    assert report.deleted == []


def test_a_file_changed_in_the_agents_own_commit_is_reverted_without_a_new_commit(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
    write_files(boundaries.checkout, {GUIDE: AGENT_TEXT})
    agent_commit = boundaries.git.commit("the agent's own commit")
    head = boundaries.git.resolve("HEAD")

    report = _undo(boundaries, start)

    assert _text(boundaries, GUIDE) == GUIDE_TEXT
    assert report.reverted == [GUIDE]
    assert boundaries.git.resolve("HEAD") == head
    assert boundaries.git.is_ancestor(agent_commit, "HEAD")


def test_files_inside_the_write_paths_are_left_as_the_agent_wrote_them(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human, write_paths=["src/*", "{work_item}"])
    write_files(boundaries.checkout, {KEPT: AGENT_TEXT, "src/new.py": AGENT_TEXT})

    report = _undo(boundaries, start)

    assert _text(boundaries, KEPT) == AGENT_TEXT
    assert _text(boundaries, "src/new.py") == AGENT_TEXT
    assert report.reverted == []
    assert report.deleted == []


def test_protected_paths_are_undone_although_a_write_path_matches_them(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human, write_paths=["*"])
    story_form = _at_start(boundaries, start, STORY_FORM_FILE)
    write_files(
        boundaries.checkout,
        {STORY_FORM_FILE: AGENT_TEXT, "pyproject.toml": AGENT_TEXT, "src/a.py": AGENT_TEXT},
    )

    report = _undo(boundaries, start)

    assert _text(boundaries, STORY_FORM_FILE) == story_form
    assert _text(boundaries, "pyproject.toml") is None
    assert _text(boundaries, "src/a.py") == AGENT_TEXT
    assert report.reverted == [STORY_FORM_FILE]
    assert report.deleted == ["pyproject.toml"]


def test_everything_else_in_an_in_progress_folder_is_undone_whatever_the_write_paths_say(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human, write_paths=["*"])
    second = _at_start(boundaries, start, SECOND)
    own_costs = cost_records_path(PATH)
    write_files(
        boundaries.checkout,
        {SECOND: AGENT_TEXT, own_costs: "{}\n", THIRD_COSTS: "{}\n", NOTES: AGENT_TEXT},
    )
    edited = _edit_section(boundaries)

    report = _undo(boundaries, start)

    assert _text(boundaries, SECOND) == second
    for path in (own_costs, THIRD_COSTS, NOTES):
        assert _text(boundaries, path) is None
    assert report.reverted == [SECOND]
    assert report.deleted == sorted([own_costs, THIRD_COSTS, NOTES])
    assert _text(boundaries, PATH) == edited


def test_files_not_directly_in_an_in_progress_folder_follow_the_write_paths(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human, write_paths=["*"])
    backlog = "factory/features/F0001-example/backlog"
    agent_files = {
        f"{backlog}/F0001-S0001-first.md": AGENT_TEXT,
        f"{backlog}/extra.md": AGENT_TEXT,
        f"{IN_PROGRESS}/sub/notes.txt": AGENT_TEXT,
    }
    assert _at_start(boundaries, start, f"{backlog}/F0001-S0001-first.md") != AGENT_TEXT
    write_files(boundaries.checkout, agent_files)

    report = _undo(boundaries, start)

    for path in agent_files:
        assert _text(boundaries, path) == AGENT_TEXT
    assert report.reverted == []
    assert report.deleted == []


def test_the_work_items_state_and_journal_are_restored_and_its_section_edit_kept(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
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

    report = _undo(boundaries, start)

    restored = boundaries.work_item_reader.read(target)
    assert restored.state == baseline.state
    assert restored.body == baseline.body.replace("Original.", "Changed by the agent.")
    assert report.restored_work_item is True
    assert PATH not in report.reverted


def test_a_work_item_with_only_a_section_edit_is_left_as_the_agent_left_it(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
    edited = _edit_section(boundaries)

    report = _undo(boundaries, start)

    assert _text(boundaries, PATH) == edited
    assert report.restored_work_item is False


def test_a_work_item_the_agent_deleted_is_restored_whole(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
    (boundaries.checkout / PATH).unlink()

    report = _undo(boundaries, start)

    assert _text(boundaries, PATH) == _at_start(boundaries, start, PATH)
    assert report.restored_work_item is True
    assert PATH not in report.reverted
    assert PATH not in report.deleted


def test_a_work_item_the_agent_broke_is_restored_whole(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
    write_files(boundaries.checkout, {PATH: BROKEN_FRONT_MATTER})

    report = _undo(boundaries, start)

    assert _text(boundaries, PATH) == _at_start(boundaries, start, PATH)
    assert report.restored_work_item is True
    assert PATH not in report.reverted
    assert PATH not in report.deleted


def test_a_work_item_the_role_may_not_write_is_reverted_whole(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human, stage="doing")
    _edit_section(boundaries)

    report = _undo(boundaries, start)

    assert _text(boundaries, PATH) == _at_start(boundaries, start, PATH)
    assert report.reverted == [PATH]
    assert report.restored_work_item is False


def test_a_widened_pipeline_definition_in_the_work_tree_widens_nothing(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
    write_files(boundaries.checkout, {PIPELINE_FILE: _pipeline(["*"]), "docs/extra.md": AGENT_TEXT})

    report = _undo(boundaries, start)

    assert _text(boundaries, "docs/extra.md") is None
    assert "docs/extra.md" in report.deleted
    assert _text(boundaries, PIPELINE_FILE) == PIPELINE_YAML


def test_an_invalid_pipeline_definition_in_the_work_tree_does_not_stop_the_undo(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
    write_files(
        boundaries.checkout,
        {PIPELINE_FILE: "stages: [unclosed\n  : :\n", "docs/extra.md": AGENT_TEXT},
    )

    report = _undo(boundaries, start)

    assert _text(boundaries, PIPELINE_FILE) == PIPELINE_YAML
    assert _text(boundaries, "docs/extra.md") is None
    assert "docs/extra.md" in report.deleted


def test_the_guard_refuses_exactly_what_the_undo_puts_back(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human, stage="doing")
    paths = ["src/a.py", "docs/a.md", "tests/t.py", "pyproject.toml", PIPELINE_FILE]
    settings = WritePathService(boundaries).at(start, PATH)
    verdicts = {path: judge(_payload(settings.root / path), settings) for path in paths}
    refused = {path for path, verdict in verdicts.items() if not verdict.allowed}
    write_files(boundaries.checkout, dict.fromkeys(paths, AGENT_TEXT))

    report = _undo(boundaries, start)

    assert refused == {"docs/a.md", "tests/t.py", "pyproject.toml", PIPELINE_FILE}
    assert set(report.reverted) | set(report.deleted) == refused


def test_the_lists_ascend_without_repeats_and_a_second_undo_finds_nothing(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = _start(boundaries, human)
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

    first = _undo(boundaries, start)
    second = _undo(boundaries, start)

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
    start = baseline(boundaries, _start(boundaries, human))
    write_files(boundaries.checkout, {GUIDE: AGENT_TEXT})

    with pytest.raises(WorkItemFormatError, match=re.escape(PATH)):
        _undo(boundaries, start)

    assert _text(boundaries, GUIDE) == AGENT_TEXT


def test_the_undo_report_is_frozen() -> None:
    report = UndoReport(reverted=[], deleted=[], restored_work_item=False)
    field = "reverted"

    with pytest.raises(ValidationError):
        setattr(report, field, ["docs/a.md"])


def test_the_undo_report_forbids_unknown_fields() -> None:
    model: type[BaseModel] = UndoReport

    with pytest.raises(ValidationError):
        model(reverted=[], deleted=[], restored_work_item=False, extra=1)
