"""The feature acceptance as data: its id, report, state, status and the reviewer's facts."""

from collections.abc import Iterable, Sequence
from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from factory.domain.bills import Bill, cost_line
from factory.domain.board import AcceptanceStatus
from factory.domain.identifiers import (
    FeatureId,
    WorkItemId,
    feature_of,
    is_acceptance,
    parse_work_item_file_name,
)
from factory.domain.journal import FACTORY, HUMAN, NewEntry, append_entry, entry_text, last_record
from factory.domain.paths import LifecycleFolder
from factory.domain.pipeline_definition import DONE_STAGE, PipelineDefinition
from factory.domain.post_texts import done_entry_text
from factory.domain.sections import (
    JOURNAL,
    first_section,
    insert_paragraph,
    section_text,
    split_lines,
)
from factory.domain.work_item import WorkItemDocument, WorkItemState, initial_state

ACCEPTANCE_SLUG = "acceptance"
AcceptanceOutcome = Literal["accepted", "refused"]

RECOMMENDATION = "Recommendation"
FINDINGS_IN_SHORT = "Findings in short"
PROPOSED_STORIES = "Proposed stories"
NONE_TEXT = "none"
NO_REASON = "no reason given"
_CLOSED_ENTRY_PREFIX = "done (pull request closed by the human); cost: "
_MERGED_BEFORE_APPROVAL_PREFIX = "done (pull request merged before approval); cost: "
# Names no merge method: every method the hosting service offers is handled the same way.
ACCEPTANCE_CLOSING = (
    "Merge to accept the report and take the proposed stories into the feature's backlog, "
    "where you refine them before starting any. "
    "Close, with a comment saying why, to refuse: the report stays on the main branch as refused "
    "with your comment, the proposed stories are discarded, and the feature counts as not "
    "accepted until another story is archived and a new acceptance runs. "
    "Nobody answers comments while the acceptance waits here; they go into the report's journal."
)

_FIRST_NUMBER = 1
_LAST_NUMBER = 9999


class AcceptanceState(WorkItemState):
    """The state of a feature acceptance: a work item's, the stories it covers and its outcome."""

    stories: list[WorkItemId] = []
    outcome: AcceptanceOutcome | None = None

    @field_validator("stories")
    @classmethod
    def _stories_only_strictly_ascending(cls, stories: list[str]) -> list[str]:
        acceptances = [story for story in stories if is_acceptance(story)]
        if acceptances:
            raise ValueError(f"stories must hold story ids only, got {acceptances}")
        if stories != sorted(set(stories)):
            raise ValueError(f"stories must ascend without repeats, got {stories}")
        return stories

    @model_validator(mode="after")
    def _outcome_exactly_when_done(self) -> Self:
        if self.stage == DONE_STAGE and self.outcome is None:
            raise ValueError(f"an acceptance at {DONE_STAGE!r} needs an outcome")
        if self.stage != DONE_STAGE and self.outcome is not None:
            raise ValueError(f"an acceptance at {self.stage!r} has no outcome yet")
        return self


def acceptance_id(feature: FeatureId, number: int) -> WorkItemId:
    """Return the id of the feature's acceptance with the given number, 1 to 9999."""
    if not _FIRST_NUMBER <= number <= _LAST_NUMBER:
        raise ValueError(
            f"an acceptance number runs from {_FIRST_NUMBER} to {_LAST_NUMBER}, got {number}"
        )
    return f"{feature}-A{number:04d}"


def _acceptance_number(work_item: WorkItemId) -> int:
    return int(work_item.split("-A")[1])


def _story_number(story: WorkItemId) -> int:
    return int(story.split("-S")[1])


def next_acceptance_id(feature: FeatureId, existing: Iterable[WorkItemId]) -> WorkItemId:
    """Return the id after the feature's highest acceptance among `existing`; a gap stays open."""
    numbers = [
        _acceptance_number(work_item)
        for work_item in existing
        if is_acceptance(work_item) and feature_of(work_item) == feature
    ]
    return acceptance_id(feature, max(numbers, default=0) + 1)


def acceptance_file_name(work_item: WorkItemId) -> str:
    """Return the file name of the acceptance's report."""
    if not is_acceptance(work_item):
        raise ValueError(f"not an acceptance id: {work_item!r}")
    return f"{work_item}-{ACCEPTANCE_SLUG}.md"


class FeatureFiles(BaseModel):
    """The file names directly in a feature's three lifecycle folders."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    feature: FeatureId
    backlog: list[str] = []
    in_progress: list[str] = []
    done: list[str] = []


class ReportFacts(BaseModel):
    """One acceptance report as read: its id, folder, state and whether it is on its branch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: WorkItemId
    folder: LifecycleFolder
    state: AcceptanceState
    on_branch: bool


class FeatureAcceptance(BaseModel):
    """A feature's acceptance as the remote shows it: its status and what comes next."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    feature: FeatureId
    directory: str
    status: AcceptanceStatus
    archived: list[WorkItemId]
    next_acceptance: WorkItemId


def story_file_ids(names: Iterable[str]) -> list[WorkItemId]:
    """The ids of the story files among `names`, ascending without repeats; others are ignored."""
    ids: set[WorkItemId] = set()
    for name in names:
        parsed = parse_work_item_file_name(name)
        if parsed is not None and not is_acceptance(parsed.id):
            ids.add(parsed.id)
    return sorted(ids)


def acceptance_status(files: FeatureFiles, reports: Sequence[ReportFacts]) -> AcceptanceStatus:
    """The status of the feature's acceptance from its folders and every report of it."""
    on_main = [report for report in reports if not report.on_branch]
    merged_ids = {report.id for report in on_main}
    if any(report.on_branch and report.id not in merged_ids for report in reports):
        return "in_flight"
    if any(report.state.stage != DONE_STAGE for report in on_main):
        return "merged_unrecorded"
    archived = story_file_ids(files.done)
    if not archived or story_file_ids(files.backlog) or story_file_ids(files.in_progress):
        return "incomplete"
    return _recorded_outcome(on_main, archived) or "due"


def _recorded_outcome(
    on_main: Sequence[ReportFacts], archived: list[WorkItemId]
) -> AcceptanceOutcome | None:
    covering = [
        report
        for report in on_main
        if set(report.state.stories) == set(archived) and report.state.outcome is not None
    ]
    if not covering:
        return None
    return max(covering, key=lambda report: report.id).state.outcome


class AcceptanceFacts(BaseModel):
    """What the acceptance reviewer is told: the archived stories, the next number, the cost."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    archived: list[WorkItemId]
    next_story: WorkItemId
    cost_line: str

    @field_validator("next_story")
    @classmethod
    def _next_story_is_a_story(cls, next_story: str) -> str:
        if is_acceptance(next_story):
            raise ValueError(f"the next story must be a story id, got {next_story!r}")
        return next_story

    def lines(self) -> list[str]:
        """The three lines of the facts, as the reviewer's prompt holds them."""
        return [
            f"Archived stories: {', '.join(self.archived)}",
            f"Next free story number: {self.next_story}",
            f"Cost of the stories: {self.cost_line}",
        ]


def acceptance_facts(files: FeatureFiles, cost_line: str) -> AcceptanceFacts:
    """The facts of the feature's files; `ValueError` when story number 9999 is taken."""
    stories = story_file_ids([*files.backlog, *files.in_progress, *files.done])
    number = max((_story_number(story) for story in stories), default=0) + 1
    if number > _LAST_NUMBER:
        raise ValueError(f"feature {files.feature} has no free story number after {_LAST_NUMBER}")
    return AcceptanceFacts(
        archived=story_file_ids(files.done),
        next_story=f"{files.feature}-S{number:04d}",
        cost_line=cost_line,
    )


def acceptance_prompt(base: str, facts: AcceptanceFacts) -> str:
    """The reviewer's prompt: `base`, an empty line and the facts."""
    return "\n".join([base, "", *facts.lines()])


def acceptance_head(
    feature_title: str, stage: str, stories: Sequence[WorkItemId]
) -> WorkItemDocument:
    """The report a new acceptance starts with: an initial state, a title and an empty journal."""
    state = AcceptanceState(**initial_state(stage).model_dump(), stories=list(stories))
    body = f"# Acceptance of {feature_title}\n\n## {JOURNAL}\n"
    return WorkItemDocument(state=state, body=body)


def _description_part(heading: str, text: str | None) -> str:
    stripped = (text or "").strip()
    return f"## {heading}\n\n{stripped or NONE_TEXT}"


def _findings(document: WorkItemDocument, role: str) -> str | None:
    # The speaker comes from the record, never from the visible line, which anyone can write.
    record = last_record(document, speaker=role, kind="result")
    return None if record is None else entry_text(document, record.number)


def acceptance_description(document: WorkItemDocument, role: str) -> str:
    """The pull request description at the approval: the reviewer's report and the closing."""
    parts = [
        _description_part(RECOMMENDATION, section_text(document.body, RECOMMENDATION)),
        _description_part(FINDINGS_IN_SHORT, _findings(document, role)),
        _description_part(PROPOSED_STORIES, section_text(document.body, PROPOSED_STORIES)),
        ACCEPTANCE_CLOSING,
    ]
    return "\n\n".join(parts)


def _acceptance_state(document: WorkItemDocument) -> AcceptanceState:
    if not isinstance(document.state, AcceptanceState):
        raise ValueError("the document's state is not an acceptance's")
    return document.state


def _booked(
    document: WorkItemDocument, outcome: AcceptanceOutcome, done_text: str
) -> WorkItemDocument:
    state = _acceptance_state(document)
    # The human's act ends the acceptance, whoever held it and whatever it waited for.
    done = state.model_copy(
        update={"stage": DONE_STAGE, "outcome": outcome, "claim": None, "blocked": None}
    )
    entry = NewEntry(speaker=FACTORY, kind="done", text=done_text)
    return append_entry(document.model_copy(update={"state": done}), entry)


def is_before_approval(definition: PipelineDefinition, stage: str) -> bool:
    """Whether `stage` lies before the definition's first approval stage."""
    if stage not in definition.stages:
        raise KeyError(stage)
    approvals = [name for name, entry in definition.stages.items() if entry.approval]
    if not approvals:
        raise ValueError("the pipeline definition has no approval stage")
    return definition.position(stage) < definition.position(approvals[0])


def book_merge(
    document: WorkItemDocument, bill: Bill, *, before_approval: bool = False
) -> WorkItemDocument:
    """The acceptance booked `accepted` at `done`, with a `done` entry carrying its bill.

    A merge `before_approval` says so in its entry: the human's merge decides all the same.
    """
    if before_approval:
        return _booked(document, "accepted", _MERGED_BEFORE_APPROVAL_PREFIX + cost_line(bill))
    return _booked(document, "accepted", done_entry_text(bill))


def refusal_reason(document: WorkItemDocument, role: str) -> str:
    """The human's comments after the last result, stripped, copied, never interpreted."""
    last_result = last_record(document, speaker=role, kind="result")
    after = 0 if last_result is None else last_result.number
    journal = [] if document.state is None else document.state.journal
    texts = [
        entry_text(document, record.number).strip()
        for record in journal
        if record.number > after and record.speaker == HUMAN and record.kind == "comment"
    ]
    return " ".join(text for text in texts if text) or NO_REASON


def _with_recommendation(body: str, paragraph: str) -> str:
    if first_section(body, RECOMMENDATION) is not None:
        return insert_paragraph(body, RECOMMENDATION, paragraph)
    added = [f"## {RECOMMENDATION}", "", paragraph]
    lines = split_lines(body)
    journal = first_section(body, JOURNAL)
    if journal is None:
        while lines and not lines[-1].strip():
            lines.pop()
        # The done entry needs a journal to land in; the report's own one is missing.
        return "\n".join([*lines, "", *added, "", f"## {JOURNAL}"]) + "\n"
    return "\n".join([*lines[: journal.start], *added, "", *lines[journal.start :]]) + "\n"


def book_refusal(
    document: WorkItemDocument, *, role: str, on: date, bill: Bill
) -> WorkItemDocument:
    """The acceptance booked `refused` at `done`, the human's reason heading its recommendation."""
    # Checked first, so a plain state is refused before its body is read.
    _acceptance_state(document)
    paragraph = f"Refused by the human on {on.isoformat()}: {refusal_reason(document, role)}"
    body = _with_recommendation(document.body, paragraph)
    refused = document.model_copy(update={"body": body})
    return _booked(refused, "refused", _CLOSED_ENTRY_PREFIX + cost_line(bill))
