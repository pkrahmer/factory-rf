"""Shared helpers of the take tests: a claimed stage start on a work item's branch."""

import json

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart
from factory.domain.identifiers import branch_name
from factory.domain.work_item import WorkItemDocument
from git_support import PIPELINE_YAML, write_files
from human_clone import HumanClone
from stage_run_support import INSTANCE
from take_support import BROKEN_FRONT_MATTER
from work_item_support import created_state

BRANCH = branch_name("F0001-S0001")
IN_PROGRESS = "factory/features/F0001-example/in-progress"
PATH = f"{IN_PROGRESS}/F0001-S0001-first.md"
SECOND = f"{IN_PROGRESS}/F0001-S0002-second.md"
PIPELINE_FILE = "factory/pipeline.yml"
GUIDE = "docs/guide.md"
GUIDE_TEXT = "# Guide\n\nAs committed.\n"
KEPT = "src/kept.py"
KEPT_TEXT = "x = 1\n"
BODY = (
    "# First story\n\n## Description\n\nOriginal.\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
)
INTAKE_ROLE = 'intake: {write_paths: ["{work_item}"]}'
BASE_FILES = {GUIDE: GUIDE_TEXT, KEPT: KEPT_TEXT, SECOND: "# Second story\n\nAs committed.\n"}


def pipeline_text(write_paths: list[str] | None) -> str:
    """The test pipeline definition, its intake role given `write_paths` when they are set."""
    if write_paths is None:
        return PIPELINE_YAML
    return PIPELINE_YAML.replace(INTAKE_ROLE, f"intake: {{write_paths: {json.dumps(write_paths)}}}")


def start_stage(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    stage: str = "intake",
    write_paths: list[str] | None = None,
) -> StageStart:
    """Push the definition, commit the work item and the base files on its branch, claim."""
    text = pipeline_text(write_paths)
    if text != PIPELINE_YAML:
        human.push_file("main", PIPELINE_FILE, text)
    git = boundaries.git
    git.fetch()
    git.checkout(BRANCH, start_point="origin/main")
    write_files(boundaries.checkout, BASE_FILES)
    document = WorkItemDocument(state=created_state(stage), body=BODY)
    target = boundaries.checkout / PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    boundaries.work_item_writer.write(target, document)
    git.commit("prepare the work item")
    assert git.push(BRANCH) == "pushed"
    definition = boundaries.pipeline_reader.parse(text)
    return ClaimService(boundaries, INSTANCE, definition).claim(BRANCH, PATH, document, stage)


def without_work_item(boundaries: Boundaries, start: StageStart) -> StageStart:
    """The stage start moved to `origin/main`, where the work item is absent."""
    commit = boundaries.git.resolve("origin/main")
    assert commit is not None
    return StageStart(commit=commit, claim=start.claim)


def with_broken_work_item(boundaries: Boundaries, start: StageStart) -> StageStart:
    """The stage start moved to a commit whose work item has unreadable front matter."""
    write_files(boundaries.checkout, {PATH: BROKEN_FRONT_MATTER})
    commit = boundaries.git.commit("break the work item")
    return StageStart(commit=commit, claim=start.claim)
