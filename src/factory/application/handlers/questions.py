"""The ask handler: a question is recorded in the work item first, then posted once."""

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import (
    Target,
    WorkItemRecorder,
    commit_subject,
    require_pull_request,
    target_of,
)
from factory.domain.errors import CannotHandle
from factory.domain.events import Event
from factory.domain.hosting import PostKey
from factory.domain.journal import FACTORY, NewEntry, append_entry, entry_text, last_record
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import attempts_cap_question
from factory.domain.work_item import Blocked, WorkItemDocument, require_state

_KIND = "ask"


def _no_state() -> ValueError:
    return ValueError("a work item without a state has no question to ask")


class AskHandler(Handler):
    """Posts the question a work item waits on, recording the attempts-cap question first."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Record and post through the boundaries; the attempts cap comes from `definition`."""
        self._boundaries = boundaries
        self._definition = definition

    def handle(self, event: Event) -> None:
        """Post the recorded question, or record the attempts-cap question and then post it."""
        target = target_of(event)
        pull_request = require_pull_request(target, _KIND)
        blocked = target.state.blocked
        document = target.snapshot.document
        if blocked is None:
            if target.state.attempts < self._definition.attempts_cap:
                raise CannotHandle(_KIND, f"work item {target.snapshot.id} waits for no question")
            document = self._record_attempts_cap_question(target)
            blocked = "attempts_cap"
        self._post(target.snapshot.id, pull_request, document, blocked)

    def _record_attempts_cap_question(self, target: Target) -> WorkItemDocument:
        snapshot = target.snapshot
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(snapshot.branch)
        document = recorder.read(snapshot.path)
        stall = last_record(document, kind="stall")
        if stall is None:
            raise CannotHandle(_KIND, f"work item {snapshot.id} has no stall to ask about")
        state = require_state(document, _no_state())
        last_stall = entry_text(document, stall.number)
        text = attempts_cap_question(state.stage, state.attempts, last_stall)
        question = NewEntry(speaker=FACTORY, kind="question", text=text)
        appended = append_entry(
            document, question, at=self._boundaries.clock.now(), blocked="attempts_cap"
        )
        blocked = require_state(appended, _no_state()).model_copy(
            update={"blocked": "attempts_cap"}
        )
        recorded = appended.model_copy(update={"state": blocked})
        subject = commit_subject(snapshot.id, "attempts cap question recorded")
        recorder.record(snapshot.branch, snapshot.path, recorded, subject)
        return recorded

    def _post(
        self, work_item: str, pull_request: int, document: WorkItemDocument, blocked: Blocked
    ) -> None:
        # Comments recorded after the question keep the key on the question's own number.
        question = last_record(document, kind="question")
        if question is None:
            raise CannotHandle(_KIND, f"work item {work_item} has no recorded question")
        text = f"{question.speaker}: {entry_text(document, question.number)}"
        key = PostKey(work_item=work_item, kind=blocked, n=str(question.number))
        self._boundaries.hosting.post_comment(pull_request, text, key)
