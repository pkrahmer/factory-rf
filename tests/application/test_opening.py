"""Opening a started work item: its branch from `origin/main`, its first document, its draft PR."""

from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.opening import WorkItemOpening
from factory.domain.errors import HostingServiceError, WorkItemFormatError
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord
from factory.domain.story_form import check_story_form
from factory.domain.work_item import WorkItemDocument, WorkItemState, initial_state
from git_support import PIPELINE_YAML, STORY_FORM, remote_commit
from human_clone import HumanClone
from stage_run_support import NOTES

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
SEEDED_BODY = "# First story\n"
BODY_WITH_JOURNAL = "# First story\n\n## Description\n\nOriginal.\n\n## Journal\n"
CREATED = JournalRecord(number=1, speaker="human", kind="created")
BRANCH_BODY = BODY_WITH_JOURNAL + "\n1. 2026-10-12 human: created.\n"


def _new_created(clock: ManualClock) -> JournalRecord:
    """The created record the opening writes: stamped with the clock and the first stage."""
    return CREATED.model_copy(update={"at": clock.now(), "stage": "intake"})


def _opening(boundaries: Boundaries) -> WorkItemOpening:
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    return WorkItemOpening(boundaries, definition)


def _start(human: HumanClone, checkout: GitCli, text: str = BODY_WITH_JOURNAL) -> None:
    """Write the backlog story on `main` (unless the seed holds it), start it and fetch."""
    if text != SEEDED_BODY:
        human.push_file("main", BACKLOG_PATH, text)
    human.start(BACKLOG_PATH)
    checkout.fetch()


def _branch_state(stage: str = "doing", round_: int = 1) -> WorkItemState:
    return WorkItemState(stage=stage, round=round_, journal=[CREATED])


def _push_branch(boundaries: Boundaries, human: HumanClone, state: WorkItemState) -> None:
    """Open the work item's branch on the remote with a document in `state`."""
    document = WorkItemDocument(state=state, body=BRANCH_BODY)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))


def _document(pull_request: int | None = None, body: str = BRANCH_BODY) -> WorkItemDocument:
    state = initial_state("intake").model_copy(
        update={"journal": [CREATED], "pull_request": pull_request}
    )
    return WorkItemDocument(state=state, body=body)


def test_new_work_item_is_branched_from_origin_main_without_pushing(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone, remote: Path
) -> None:
    _start(human, checkout)

    prepared = _opening(boundaries).prepare(WORK_ITEM, PATH)

    status = checkout.status()
    assert prepared.branch == BRANCH
    assert prepared.path == PATH
    assert prepared.work_item == WORK_ITEM
    assert status.branch == BRANCH
    assert status.head == checkout.resolve("origin/main")
    assert status.changes == []
    assert prepared.branch_existed is False
    assert prepared.merge_conflict is False
    assert remote_commit(remote, BRANCH) is None
    assert checkout.resolve(f"origin/{BRANCH}") is None


def test_new_document_starts_at_the_first_stage(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone, clock: ManualClock
) -> None:
    _start(human, checkout)
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)

    prepared = _opening(boundaries).prepare(WORK_ITEM, PATH)

    first_stage = next(iter(definition.stages))
    created = CREATED.model_copy(update={"at": clock.now(), "stage": first_stage})
    expected = initial_state(first_stage).model_copy(update={"journal": [created]})
    assert prepared.document.state == expected


def test_backlog_front_matter_is_dropped(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone, clock: ManualClock
) -> None:
    text = (
        "---\n"
        "stage: doing\n"
        "attempts: 1\n"
        "blocked: question\n"
        "journal:\n"
        "- {number: 1, speaker: human, kind: created}\n"
        "- {number: 2, speaker: intake, kind: accepted}\n"
        "---\n" + BODY_WITH_JOURNAL
    )
    _start(human, checkout, text)

    prepared = _opening(boundaries).prepare(WORK_ITEM, PATH)

    state = prepared.document.state
    assert state is not None
    assert state.model_copy(update={"journal": []}) == initial_state("intake")
    assert state.journal == [_new_created(clock)]
    rendered = boundaries.work_item_writer.render(prepared.document)
    assert "stage: doing" not in rendered
    assert "attempts: 1" not in rendered
    assert "blocked: question" not in rendered


def test_new_document_journal_holds_the_created_entry(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone, clock: ManualClock
) -> None:
    _start(human, checkout)

    prepared = _opening(boundaries).prepare(WORK_ITEM, PATH)

    state = prepared.document.state
    assert state is not None
    assert state.journal == [_new_created(clock)]
    rendered = boundaries.work_item_writer.render(prepared.document)
    assert "## Journal\n\n1. 2026-10-12 human: created.\n" in rendered
    assert rendered.count("## Journal") == 1


def test_story_without_journal_section_gets_one(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone
) -> None:
    _start(human, checkout, SEEDED_BODY)

    prepared = _opening(boundaries).prepare(WORK_ITEM, PATH)

    expected = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
    assert prepared.document.body == expected


def test_journal_entries_already_in_the_story_are_left_for_the_form_check(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone
) -> None:
    _start(human, checkout, BODY_WITH_JOURNAL + "\n1. 2026-10-10 human: created.\n")

    prepared = _opening(boundaries).prepare(WORK_ITEM, PATH)

    state = prepared.document.state
    assert state is not None
    assert len(state.journal) == 1
    findings = check_story_form(prepared.document, STORY_FORM, folder="in-progress")
    messages = [finding.message for finding in findings]
    assert "the journal data lists 1 entries but the text shows 2" in messages


def test_absent_work_item_file_is_a_format_error(boundaries: Boundaries, checkout: GitCli) -> None:
    checkout.fetch()

    with pytest.raises(WorkItemFormatError) as raised:
        _opening(boundaries).prepare(WORK_ITEM, PATH)

    assert raised.value.path == PATH


def test_existing_branch_gives_the_branch_document(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone
) -> None:
    _start(human, checkout)
    _push_branch(boundaries, human, _branch_state())
    checkout.fetch()

    prepared = _opening(boundaries).prepare(WORK_ITEM, PATH)

    assert prepared.branch_existed is True
    assert prepared.merge_conflict is False
    assert prepared.document.state == _branch_state()


def test_stale_local_branch_is_reset_to_the_remote(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone
) -> None:
    _start(human, checkout)
    _push_branch(boundaries, human, _branch_state())
    checkout.fetch()
    opening = _opening(boundaries)
    opening.prepare(WORK_ITEM, PATH)
    (boundaries.checkout / "local-only.md").write_text("local\n", encoding="utf-8")
    checkout.commit("a commit only the local branch has")
    human.push_file(BRANCH, "later.md", "later\n")
    checkout.fetch()

    opening.prepare(WORK_ITEM, PATH)

    assert not (boundaries.checkout / "local-only.md").exists()
    assert (boundaries.checkout / "later.md").read_text(encoding="utf-8") == "later\n"
    assert checkout.status().head == checkout.resolve(f"origin/{BRANCH}")


def test_origin_main_is_merged_into_the_branch(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone
) -> None:
    _start(human, checkout)
    _push_branch(boundaries, human, _branch_state())
    human.push_file("main", NOTES, "added on main\n")
    checkout.fetch()

    prepared = _opening(boundaries).prepare(WORK_ITEM, PATH)

    assert (boundaries.checkout / NOTES).read_text(encoding="utf-8") == "added on main\n"
    assert prepared.merge_conflict is False
    assert checkout.status().changes == []


def test_merge_conflict_is_aborted_and_reported(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone
) -> None:
    human.push_file("main", NOTES, "base\n")
    _start(human, checkout)
    _push_branch(boundaries, human, _branch_state())
    human.push_file(BRANCH, NOTES, "branch\n")
    human.push_file("main", NOTES, "main\n")
    checkout.fetch()

    prepared = _opening(boundaries).prepare(WORK_ITEM, PATH)

    status = checkout.status()
    assert prepared.merge_conflict is True
    assert prepared.branch_existed is True
    assert status.changes == []
    assert status.branch == BRANCH
    assert status.head == checkout.resolve(f"origin/{BRANCH}")
    assert prepared.document.state == _branch_state()


def test_prepare_never_fetches(boundaries: Boundaries, checkout: GitCli, human: HumanClone) -> None:
    _start(human, checkout)
    fetched_main = checkout.resolve("origin/main")
    human.push_file("main", NOTES, "pushed after the fetch\n")

    _opening(boundaries).prepare(WORK_ITEM, PATH)

    assert not (boundaries.checkout / NOTES).exists()
    assert checkout.resolve("origin/main") == fetched_main


def test_new_draft_pull_request_is_created(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    document = _document()

    pull = _opening(boundaries).ensure_pull_request(WORK_ITEM, document)

    assert hosting.pull_requests() == [pull]
    assert pull.draft is True
    assert pull.state == "open"
    assert pull.branch == BRANCH
    assert pull.title == f"{WORK_ITEM}: First story"
    assert hosting.description(pull.number) == document.body


def test_open_pull_request_of_the_branch_is_reused(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    existing = hosting.create_pull_request(BRANCH, "earlier", "earlier body", draft=True)

    pull = _opening(boundaries).ensure_pull_request(WORK_ITEM, _document())

    assert pull == existing
    assert len(hosting.pull_requests()) == 1


def test_open_pull_request_of_the_state_is_reused(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    hosting.create_pull_request(BRANCH, "first", "first body", draft=True)
    recorded = hosting.create_pull_request(BRANCH, "second", "second body", draft=True)

    pull = _opening(boundaries).ensure_pull_request(WORK_ITEM, _document(recorded.number))

    assert pull == recorded
    assert len(hosting.pull_requests()) == 2


@pytest.mark.parametrize("ending", ["closed", "merged"])
def test_closed_or_merged_pull_request_is_not_reused(
    boundaries: Boundaries, hosting: FakeHostingService, ending: str
) -> None:
    old = hosting.create_pull_request(BRANCH, "old", "old body", draft=True)
    if ending == "closed":
        hosting.close_by_human(old.number)
    else:
        hosting.merge_by_human(old.number, "a" * 40)

    pull = _opening(boundaries).ensure_pull_request(WORK_ITEM, _document(old.number))

    assert pull.number != old.number
    assert pull.draft is True
    assert pull.state == "open"
    assert len(hosting.pull_requests()) == 2


def test_body_without_title_line_is_refused(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    document = _document(body="## Journal\n\n1. 2026-10-12 human: created.\n")

    with pytest.raises(WorkItemFormatError) as raised:
        _opening(boundaries).ensure_pull_request(WORK_ITEM, document)

    assert raised.value.fault == "the work item has no title line"
    assert hosting.pull_requests() == []


def test_hosting_service_error_propagates(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    hosting.fail_next("create_pull_request")

    with pytest.raises(HostingServiceError) as raised:
        _opening(boundaries).ensure_pull_request(WORK_ITEM, _document())

    assert raised.value.operation == "create_pull_request"
    assert raised.value.detail == "injected failure"


def test_ensuring_the_pull_request_changes_no_file(
    boundaries: Boundaries, checkout: GitCli, human: HumanClone
) -> None:
    _start(human, checkout)
    opening = _opening(boundaries)
    prepared = opening.prepare(WORK_ITEM, PATH)
    before = (boundaries.checkout / PATH).read_bytes()

    opening.ensure_pull_request(WORK_ITEM, prepared.document)

    assert checkout.status().changes == []
    assert (boundaries.checkout / PATH).read_bytes() == before
