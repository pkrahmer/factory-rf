"""The acceptance service opens a due acceptance and reads the reviewer's facts from main."""

from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from bill_support import completed_records, sidecar_text
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.acceptance import AcceptanceService, OpenedAcceptance
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart
from factory.application.costs import BillService
from factory.application.write_paths import WritePathService
from factory.domain.acceptance import AcceptanceState, acceptance_head
from factory.domain.bills import bill, cost_line
from factory.domain.errors import CannotHandle, PushFailed, WorkItemFormatError
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument
from factory.domain.write_paths import is_writable
from git_support import PIPELINE_YAML, remote_commit, run_git, write_files
from human_clone import HumanClone

FEATURES = "factory/features"
TODO = f"{FEATURES}/F0002-todo"
FEATURE_FILE = f"{TODO}/feature.md"
ARCHIVED = ["F0002-S0001", "F0002-S0002"]
ARCHIVED_PATHS = [f"{TODO}/done/F0002-S0001-a.md", f"{TODO}/done/F0002-S0002-b.md"]
ACCEPTANCE = "F0002-A0001"
BRANCH = f"work-item/{ACCEPTANCE}"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"


@pytest.fixture
def definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition, with the acceptance stage `acceptance`."""
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)


def _push_todo(human: HumanClone, *, feature_text: str | None = "# Todo service\n") -> None:
    if feature_text is not None:
        human.push_file("main", FEATURE_FILE, feature_text)
    human.push_file("main", ARCHIVED_PATHS[0], "# A\n")
    human.push_file("main", ARCHIVED_PATHS[1], "# B\n")


def _service(boundaries: Boundaries, definition: PipelineDefinition) -> AcceptanceService:
    boundaries.git.fetch()
    return AcceptanceService(boundaries, definition)


def _remote_refs(remote: Path) -> str:
    return run_git(remote, "for-each-ref")


def _report_text(state: AcceptanceState) -> str:
    return FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body="# Acceptance\n"))


def _claimed(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone
) -> StageStart:
    _push_todo(human)
    opened = _service(boundaries, definition).open("F0002")
    text = (boundaries.checkout / opened.path).read_text(encoding="utf-8")
    document = boundaries.work_item_reader.parse(text)
    claims = ClaimService(boundaries, "factory-1", definition)
    return claims.claim(opened.branch, opened.path, document, "acceptance")


def test_the_service_needs_an_acceptance_stage(
    boundaries: Boundaries, definition: PipelineDefinition
) -> None:
    without = definition.model_copy(update={"acceptance_stage": None})

    with pytest.raises(ValueError):
        AcceptanceService(boundaries, without)


def test_opening_pushes_the_report_head_on_the_acceptance_branch(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone, remote: Path
) -> None:
    _push_todo(human)

    opened = _service(boundaries, definition).open("F0002")

    pushed = remote_commit(remote, BRANCH)
    assert pushed is not None
    assert opened == OpenedAcceptance(id=ACCEPTANCE, branch=BRANCH, path=REPORT, commit=pushed)
    boundaries.git.fetch()
    head = acceptance_head("Todo service", "acceptance", ARCHIVED)
    rendered = boundaries.work_item_writer.render(head)
    assert boundaries.git.show_file(f"origin/{BRANCH}", REPORT) == rendered


@pytest.mark.parametrize("in_progress_folder", [False, True], ids=["no-folder", "folder"])
def test_opening_adds_one_commit_with_only_the_report_and_no_pull_request(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    human: HumanClone,
    *,
    remote: Path,
    hosting: FakeHostingService,
    in_progress_folder: bool,
) -> None:
    _push_todo(human)
    if in_progress_folder:
        human.push_file("main", f"{TODO}/in-progress/.gitkeep", "")

    _service(boundaries, definition).open("F0002")

    assert run_git(remote, "rev-list", f"main..{BRANCH}").split() == [remote_commit(remote, BRANCH)]
    assert run_git(remote, "rev-parse", f"{BRANCH}^").strip() == remote_commit(remote, "main")
    added = run_git(remote, "diff-tree", "--no-commit-id", "--name-status", "-r", BRANCH)
    assert added.splitlines() == [f"A\t{REPORT}"]
    assert hosting.pull_requests() == []


@pytest.mark.parametrize(
    "feature_text", [None, "Todo service\n\nNo title here.\n"], ids=["missing", "untitled"]
)
def test_opening_without_a_feature_title_is_a_format_error_and_pushes_nothing(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    human: HumanClone,
    remote: Path,
    feature_text: str | None,
) -> None:
    _push_todo(human, feature_text=feature_text)
    before = _remote_refs(remote)

    with pytest.raises(WorkItemFormatError) as raised:
        _service(boundaries, definition).open("F0002")

    assert raised.value.path == FEATURE_FILE
    assert _remote_refs(remote) == before


def test_opening_takes_the_first_title_of_the_feature_file(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone
) -> None:
    _push_todo(human, feature_text="Intro\n\n# Todo service\n\n# Later heading\n")

    _service(boundaries, definition).open("F0002")

    boundaries.git.fetch()
    head = acceptance_head("Todo service", "acceptance", ARCHIVED)
    rendered = boundaries.work_item_writer.render(head)
    assert boundaries.git.show_file(f"origin/{BRANCH}", REPORT) == rendered


def test_opening_a_feature_that_is_not_due_cannot_be_handled_and_pushes_nothing(
    boundaries: Boundaries, definition: PipelineDefinition, remote: Path
) -> None:
    before = _remote_refs(remote)

    with pytest.raises(CannotHandle) as raised:
        _service(boundaries, definition).open("F0001")

    assert (raised.value.kind, raised.value.reason) == (
        "acceptance_due",
        "feature F0001 is incomplete, not due",
    )
    assert _remote_refs(remote) == before


def test_opening_again_after_a_kill_before_the_push_leaves_one_branch_with_one_commit(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    human: HumanClone,
    remote: Path,
    kill_points: KillPoints,
) -> None:
    _push_todo(human)
    kill_points.arm(KillPoint.BEFORE_PUSH)

    with pytest.raises(InjectedKill):
        _service(boundaries, definition).open("F0002")
    _service(boundaries, definition).open("F0002")

    branches = run_git(remote, "for-each-ref", "--format=%(refname)", "refs/heads/work-item/")
    assert branches.split() == [f"refs/heads/{BRANCH}"]
    assert len(run_git(remote, "rev-list", f"main..{BRANCH}").split()) == 1


def test_opening_onto_a_branch_the_checkout_has_not_fetched_is_a_rejected_push(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone, remote: Path
) -> None:
    _push_todo(human)
    service = _service(boundaries, definition)
    human.push_file(BRANCH, f"{TODO}/notes.md", "# The human's notes\n")
    human_commit = remote_commit(remote, BRANCH)

    with pytest.raises(PushFailed) as raised:
        service.open("F0002")

    assert raised.value.outcome == "rejected"
    assert remote_commit(remote, BRANCH) == human_commit


@pytest.mark.parametrize("committed", [False, True], ids=["work-tree", "local-commit"])
def test_the_facts_are_read_from_main_on_the_remote_only(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone, committed: bool
) -> None:
    _push_todo(human)
    service = _service(boundaries, definition)
    write_files(boundaries.checkout, {f"{TODO}/done/F0002-S0005-e.md": "# E\n"})
    if committed:
        boundaries.git.commit("a story on the local main only")

    facts = service.facts("F0002")

    assert (facts.archived, facts.next_story) == (ARCHIVED, "F0002-S0003")


def test_the_cost_line_counts_the_records_of_the_archived_stories_only(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone
) -> None:
    _push_todo(human)
    archived = completed_records("F0002-S0001", 2)
    human.push_file("main", cost_records_path(ARCHIVED_PATHS[0]), sidecar_text(archived))
    backlog = f"{TODO}/backlog/F0002-S0003-c.md"
    human.push_file("main", backlog, "# C\n")
    human.push_file(
        "main", cost_records_path(backlog), sidecar_text(completed_records("F0002-S0003", 3))
    )
    other = f"{FEATURES}/F0001-example/done/F0001-S0002-other.md"
    human.push_file("main", other, "# Other\n")
    human.push_file(
        "main", cost_records_path(other), sidecar_text(completed_records("F0001-S0002", 4))
    )
    report = f"{TODO}/done/F0002-A0001-acceptance.md"
    state = AcceptanceState(stage="done", outcome="refused", stories=ARCHIVED)
    human.push_file("main", report, _report_text(state))
    human.push_file(
        "main", cost_records_path(report), sidecar_text(completed_records(ACCEPTANCE, 5))
    )

    facts = _service(boundaries, definition).facts("F0002")

    assert facts.cost_line == cost_line(bill(archived))


def test_the_facts_of_a_feature_without_a_directory_on_main_are_refused(
    boundaries: Boundaries, definition: PipelineDefinition
) -> None:
    with pytest.raises(ValueError, match="F0003"):
        _service(boundaries, definition).facts("F0003")


def test_the_reviewer_may_write_its_report_and_new_backlog_stories(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone
) -> None:
    stage_start = _claimed(boundaries, definition, human)

    write_paths = WritePathService(boundaries).at(stage_start, REPORT).write_paths

    assert is_writable(REPORT, write_paths)
    assert is_writable(f"{TODO}/backlog/F0002-S0005-new.md", write_paths)


@pytest.mark.parametrize(
    "path",
    [
        f"{TODO}/done/F0002-S0001-a.md",
        FEATURE_FILE,
        f"{FEATURES}/F0001-example/backlog/F0001-S0002-new.md",
        "README.md",
        "src/factory/x.py",
    ],
    ids=["archived-story", "feature-file", "other-feature", "readme", "source"],
)
def test_the_reviewer_may_write_nothing_else(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone, path: str
) -> None:
    stage_start = _claimed(boundaries, definition, human)

    write_paths = WritePathService(boundaries).at(stage_start, REPORT).write_paths

    assert not is_writable(path, write_paths)


@pytest.mark.parametrize(
    ("work_item", "count"),
    [("F0002-A0001", 1), ("F0002-A0002", 2), ("F0002-A0003", 0)],
    ids=["merged-report", "report-on-branch", "no-records"],
)
def test_each_acceptance_has_its_own_cost_line(
    boundaries: Boundaries, human: HumanClone, work_item: str, count: int
) -> None:
    _push_todo(human)
    human.push_file(
        "main",
        cost_records_path(ARCHIVED_PATHS[0]),
        sidecar_text(completed_records(ARCHIVED[0], 3)),
    )
    first = f"{TODO}/done/F0002-A0001-acceptance.md"
    done = AcceptanceState(stage="done", outcome="refused", stories=ARCHIVED)
    human.push_file("main", first, _report_text(done))
    human.push_file(
        "main", cost_records_path(first), sidecar_text(completed_records("F0002-A0001", 1))
    )
    second = f"{TODO}/in-progress/F0002-A0002-acceptance.md"
    running = AcceptanceState(stage="acceptance", stories=ARCHIVED)
    human.push_file("work-item/F0002-A0002", second, _report_text(running))
    human.push_file(
        "work-item/F0002-A0002",
        cost_records_path(second),
        sidecar_text(completed_records("F0002-A0002", 2)),
    )
    third = f"{TODO}/in-progress/F0002-A0003-acceptance.md"
    human.push_file("work-item/F0002-A0003", third, _report_text(running))
    boundaries.git.fetch()

    result = BillService(boundaries.git, boundaries.cost_reader).for_work_item(work_item)

    assert result is not None
    assert result.line == cost_line(bill(completed_records(work_item, count)))


@pytest.mark.parametrize(
    ("values", "accepted"),
    [
        ({}, True),
        ({"id": "F002-A0001"}, False),
        ({"commit": "a" * 39}, False),
        ({"unknown": 1}, False),
    ],
    ids=["valid", "malformed-id", "short-commit", "unknown-key"],
)
def test_the_opened_acceptance_is_closed_and_typed(
    values: dict[str, object], accepted: bool
) -> None:
    model: type[BaseModel] = OpenedAcceptance
    complete: dict[str, object] = {
        "id": ACCEPTANCE,
        "branch": BRANCH,
        "path": REPORT,
        "commit": "a" * 40,
        **values,
    }
    if accepted:
        model(**complete)
    else:
        with pytest.raises(ValidationError):
            model(**complete)


def test_the_opened_acceptance_refuses_an_assignment() -> None:
    opened = OpenedAcceptance(id=ACCEPTANCE, branch=BRANCH, path=REPORT, commit="a" * 40)
    field = "branch"

    with pytest.raises(ValidationError):
        setattr(opened, field, "work-item/F0002-A0002")
