"""The tick: check the disk, fetch, load, restore, publish the stops, preflight, dispatch."""

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NoReturn

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher, DispatchOutcome, Handler
from factory.application.pipeline_loading import PipelineLoader
from factory.application.preflight import Preflight
from factory.application.recovery import delete_stale_branches
from factory.application.stops import StopPublisher, StopService
from factory.application.watcher import Watcher
from factory.application.work_items import RemoteWorkItems
from factory.domain.disk import disk_low_detail
from factory.domain.errors import (
    AgentDefinitionInvalid,
    FetchFailed,
    GitError,
    PipelineDefinitionInvalid,
    PushFailed,
)
from factory.domain.events import Event, EventKind
from factory.domain.identifiers import Name, branch_name, work_item_of_branch
from factory.domain.paths import MAIN_BRANCH, REMOTE
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.stops import RepositoryStop, RepositoryStopReason, StopScope
from factory.domain.tick_status import TickStatus

HandlerFactory = Callable[[PipelineDefinition], Mapping[EventKind, Handler]]

_MAIN_REF = f"{REMOTE}/{MAIN_BRANCH}"


class TickOutcome(BaseModel):
    """How one tick ended: at a repository stop, or with the event it dispatched."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stopped: RepositoryStopReason | None = None
    event: Event | None = None
    dispatch: DispatchOutcome | None = None


class IdleHandler(Handler):
    """The handler of an idle remote: there is nothing to do."""

    def handle(self, event: Event) -> None:
        """Do nothing."""


class _Stopped(Exception):
    """Ends the tick at a repository stop that has already been reported."""

    def __init__(self, reason: RepositoryStopReason) -> None:
        super().__init__(reason)
        self.reason = reason


class Tick:
    """One pass over the remote, the only truth of the work items; the checkout is disposable.

    The tick status is kept from one run to the next. Beyond the remote, it reads only the
    agent files in the agent's home and the instance's state directory (the health file and
    the records), never what an earlier tick left in the checkout.
    """

    def __init__(
        self,
        boundaries: Boundaries,
        instance: Name,
        handlers: HandlerFactory,
        status: TickStatus | None = None,
        preflight: Preflight | None = None,
    ) -> None:
        """Work through `boundaries` as `instance`, building the handlers per loaded definition.

        A given `preflight` runs on the restored checkout; a stop it reports ends the tick.
        """
        self._boundaries = boundaries
        self._instance = instance
        self._handlers = handlers
        self._status = TickStatus() if status is None else status
        self._stops = StopService(boundaries)
        self._preflight = preflight

    @property
    def status(self) -> TickStatus:
        """The counts after the last dispatch."""
        return self._status

    def run(self) -> TickOutcome:
        """Check the disk, fetch, load, restore, publish the stop records, preflight, dispatch.

        Before the dispatch, the stale branches are deleted and the remote is evaluated. A stop
        ends the tick.

        Raises `WorkItemFormatError`, `ValueError` from the evaluation, and `GitError`
        outside the fetch and the restore: no stop exists for them.
        """
        try:
            self._check_disk()
            self._fetch()
            definition = self._load()
            self._restore()
            self._publish_stop_records()
            self._run_preflight()
        except _Stopped as stopped:
            return TickOutcome(stopped=stopped.reason)
        delete_stale_branches(self._boundaries)
        event = Watcher(self._boundaries, self._instance).evaluate(definition)
        dispatcher = Dispatcher(
            self._handlers(definition), self._status, self._stops, self._boundaries.log
        )
        outcome = dispatcher.dispatch(event)
        self._status = dispatcher.status
        return TickOutcome(event=event, dispatch=outcome)

    def _check_disk(self) -> None:
        # Before the fetch, so that no write of the tick meets a full disk and hangs.
        disk = self._boundaries.disk
        settings = self._boundaries.settings
        free: dict[Path, int] = {}
        for path in (settings.checkout.parent, settings.state_directory):
            try:
                free[path] = disk.free_bytes(path)
            except OSError as error:
                # An unknown free space is no proof of room.
                self._stop(
                    "disk_low", f"cannot read the free space of {path}: {error}", scope="machine"
                )
        detail = disk_low_detail(free, settings.min_free_gb)
        if detail is not None:
            self._stop("disk_low", detail, scope="machine")
        self._stops.clear_stop("disk_low")

    def _fetch(self) -> None:
        try:
            self._boundaries.git.fetch()
        except FetchFailed as error:
            self._stop("fetch_failed", str(error))
        self._stops.clear_stop("fetch_failed")

    def _load(self) -> PipelineDefinition:
        # The loader raises and clears the definition's stops itself.
        try:
            return PipelineLoader(self._boundaries).load()
        except PipelineDefinitionInvalid as error:
            raise _Stopped("pipeline_definition_invalid") from error
        except AgentDefinitionInvalid as error:
            raise _Stopped("agent_definition_invalid") from error

    def _restore(self) -> None:
        try:
            self._restore_checkout()
        except GitError as error:
            self._stop("checkout_restore_failed", str(error))
        self._stops.clear_stop("checkout_restore_failed")

    def _publish_stop_records(self) -> None:
        # After the restore, which logs what a killed stage left behind before the
        # publisher's checkout could discard it. A failure keeps the records for the next tick.
        try:
            StopPublisher(self._boundaries).publish()
        except (GitError, PushFailed, OSError) as error:
            self._boundaries.log.line(f"cannot publish the stop records: {error}")

    def _run_preflight(self) -> None:
        # The preflight raises and clears its stops itself.
        if self._preflight is None:
            return
        reason = self._preflight.run()
        if reason is not None:
            raise _Stopped(reason)

    def _restore_checkout(self) -> None:
        git = self._boundaries.git
        changes = [change.path for change in git.status().changes]
        if changes:
            self._boundaries.log.line(f"discarded uncommitted changes: {', '.join(changes)}")
        # Cleaning in place first, so that the switch to main never meets a local change.
        git.reset_to("HEAD")
        # Before the switch, while the branch's own `.gitignore` files still name what they hid.
        git.remove_ignored()
        git.checkout(MAIN_BRANCH, start_point=_MAIN_REF)
        # A local branch of a work item may hold a rejected push; the next stage starts
        # from the remote's branch instead.
        for work_item in self._work_items_with_branches():
            git.delete_branch(branch_name(work_item))

    def _work_items_with_branches(self) -> list[str]:
        git = self._boundaries.git
        on_remote = [work_item_of_branch(branch.name) for branch in git.remote_branches()]
        stories = RemoteWorkItems(git, self._boundaries.work_item_reader).list_stories(
            "in-progress"
        )
        started = [story.id for story in stories]
        return sorted({work_item for work_item in [*on_remote, *started] if work_item is not None})

    def _stop(
        self, reason: RepositoryStopReason, detail: str, scope: StopScope = "repository"
    ) -> NoReturn:
        stop = RepositoryStop(
            scope=scope, reason=reason, detail=detail, at=self._boundaries.clock.now()
        )
        self._stops.raise_stop(stop)
        raise _Stopped(reason)
