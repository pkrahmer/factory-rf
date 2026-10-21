"""A walk of one feature's acceptances over real ticks, with the human's acts in between."""

from pathlib import Path

from bill_support import completed_records, sidecar_text
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.application.tick import Tick, TickOutcome
from factory.application.watcher import Watcher
from factory.domain.acceptance import AcceptanceState
from factory.domain.board import AcceptanceStatus
from factory.domain.cost_records import CostRecord
from factory.domain.events import Event, EventKind
from factory.domain.identifiers import FeatureId, branch_name
from factory.domain.journal import FACTORY, NewEntry, append_entry, entry_text
from factory.domain.paths import (
    LifecycleFolder,
    cost_records_path,
    feature_file_path,
    work_item_path,
)
from factory.domain.work_item import Blocked, WorkItemDocument
from factory.entry.wiring import handler_factory
from git_support import PIPELINE_YAML, install_agents, remote_commit
from human_clone import HumanClone
from stage_run_support import INSTANCE
from wiring_support import ENVIRONMENT

FEATURE = "F0002"
TODO = "F0002-todo"
REVIEWER = "acceptance-reviewer"
FIRST = "F0002-A0001"
SECOND = "F0002-A0002"
FIRST_RECORDS = completed_records(FIRST, 2)
SECOND_RECORDS = completed_records(SECOND, 1)
PROPOSED = work_item_path(TODO, "backlog", "F0002-S0003-c.md")
PROPOSED_TEXT = """\
# C

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal
"""
_STARTED = NewEntry(speaker=FACTORY, kind="started", text="started.")


def report_of(work_item: str, folder: LifecycleFolder = "in-progress") -> str:
    """The path of the report of `work_item` in `folder` of the feature."""
    return work_item_path(TODO, folder, f"{work_item}-acceptance.md")


def last_entry(document: WorkItemDocument) -> str:
    """The text of the last journal entry of `document`."""
    assert document.state is not None
    return entry_text(document, document.state.journal[-1].number)


class AcceptanceWalk:
    """Ticks of the whole factory over the test remote, each after an evaluation of its own.

    Every evaluation and every tick is kept, in order, so that a test can look at all of them.
    """

    def __init__(
        self,
        boundaries: Boundaries,
        *,
        remote: Path,
        human: HumanClone,
        hosting: FakeHostingService,
        agent_home: Path,
    ) -> None:
        """Install the agents of the test remote's roles and push the feature `F0002-todo`."""
        self.definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
        install_agents(agent_home, self.definition.roles)
        self._boundaries = boundaries
        self._remote = remote
        self._human = human
        self._hosting = hosting
        self.evaluations: list[Event] = []
        self.outcomes: list[TickOutcome] = []
        human.push_file("main", feature_file_path(TODO), "# Todo service\n")
        self.archive("F0002-S0001-a.md", "# A\n")
        self.archive("F0002-S0002-b.md", "# B\n")

    def archive(self, name: str, text: str) -> None:
        """Push the story file `name` into the feature's `done/` on main."""
        self._human.push_file("main", work_item_path(TODO, "done", name), text)

    def evaluate(self) -> Event:
        """Fetch and keep the event the watcher sees now."""
        self._boundaries.git.fetch()
        event = Watcher(self._boundaries, INSTANCE).evaluate(self.definition)
        self.evaluations.append(event)
        return event

    def tick(self) -> TickOutcome:
        """Evaluate, then run one tick of the production wiring; keep both."""
        self.evaluate()
        handlers = handler_factory(self._boundaries, INSTANCE, ENVIRONMENT)
        outcome = Tick(self._boundaries, INSTANCE, handlers).run()
        self.outcomes.append(outcome)
        return outcome

    def kinds(self) -> list[EventKind]:
        """The kinds of every evaluation and every tick's event so far."""
        ticked = [outcome.event.kind for outcome in self.outcomes if outcome.event is not None]
        return [event.kind for event in self.evaluations] + ticked

    def open(self, work_item: str) -> int:
        """Tick the due acceptance open and create its draft pull request; return its number."""
        outcome = self.tick()
        assert outcome.event is not None
        assert outcome.event.kind == "acceptance_due"
        title = f"{work_item}: acceptance"
        return self._hosting.create_pull_request(
            branch_name(work_item), title, "body", draft=True
        ).number

    def record(
        self,
        work_item: str,
        number: int,
        records: list[CostRecord],
        *,
        stage: str,
        blocked: Blocked | None = None,
        handed_over: str | None = None,
    ) -> WorkItemDocument:
        """Push the report's state on its branch, with its cost records; return the document."""
        branch = branch_name(work_item)
        path = report_of(work_item)
        self._boundaries.git.fetch()
        text = self._boundaries.git.show_file(f"origin/{branch}", path)
        assert text is not None
        opened = self._boundaries.work_item_reader.parse(text)
        state = opened.state
        assert isinstance(state, AcceptanceState)
        update = {
            "stage": stage,
            "pull_request": number,
            "blocked": blocked,
            "handed_over": handed_over,
        }
        document = append_entry(
            opened.model_copy(update={"state": state.model_copy(update=update)}), _STARTED
        )
        self._human.push_file(branch, path, self._boundaries.work_item_writer.render(document))
        self._human.push_file(branch, cost_records_path(path), sidecar_text(records))
        return document

    def propose(self, work_item: str) -> None:
        """Push the backlog story `F0002-S0003-c.md` to the acceptance's branch."""
        self._human.push_file(branch_name(work_item), PROPOSED, PROPOSED_TEXT)

    def merge(self, work_item: str, number: int) -> None:
        """Merge the acceptance's branch into main as the human, and its pull request with it."""
        self._human.merge(branch_name(work_item), "merge")
        main = remote_commit(self._remote, "main")
        assert main is not None
        self._hosting.merge_by_human(number, main)

    def close(self, number: int, comment: str | None = None) -> None:
        """Close the pull request as the human, after the comment when one is given."""
        if comment is not None:
            self._hosting.add_human_comment(number, comment)
        self._hosting.close_by_human(number)

    def booked(self, work_item: str) -> WorkItemDocument:
        """The report of `work_item` in `done/` on origin/main."""
        self._boundaries.git.fetch()
        text = self._boundaries.git.show_file("origin/main", report_of(work_item, "done"))
        assert text is not None
        return self._boundaries.work_item_reader.parse(text)

    def status(self) -> AcceptanceStatus:
        """The acceptance status of `F0002` as the last fetch shows it."""
        self._boundaries.git.fetch()
        reader = AcceptanceReader(self._boundaries, self.definition)
        return {entry.feature: entry.status for entry in reader.read()}[FEATURE]

    def due(self) -> list[FeatureId]:
        """The due features as the last fetch shows them."""
        self._boundaries.git.fetch()
        return AcceptanceReader(self._boundaries, self.definition).due_features()


def booked_state(document: WorkItemDocument) -> AcceptanceState:
    """The acceptance state of a booked report."""
    assert isinstance(document.state, AcceptanceState)
    return document.state
