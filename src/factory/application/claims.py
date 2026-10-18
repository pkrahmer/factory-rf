"""The claim: the stage-start commit that records an instance's hold on a work item."""

import re
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.application.handlers.recording import commit_subject
from factory.domain.errors import PushFailed
from factory.domain.git import CommitId
from factory.domain.identifiers import WorkItemId, branch_name, parse_work_item_file_name
from factory.domain.journal import NewEntry, append_entry
from factory.domain.lease import ClaimStatus, claim_status
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState, require_state

_INSTANCE_NAME = re.compile(r"[a-z][a-z0-9-]*")


class StageStart(BaseModel):
    """The pushed stage-start commit and the claim it holds."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    commit: CommitId
    claim: Claim


def started_text(stage: str, instance: str) -> str:
    """The text of the journal entry that says an instance started a stage."""
    return f"started {stage} as {instance}."


class ClaimService:
    """Claims, judges and releases the stage claims of work items for one instance."""

    def __init__(
        self, boundaries: Boundaries, instance: str, definition: PipelineDefinition
    ) -> None:
        """Claim as `instance`, with the leases of `definition`; `ValueError` for a bad name."""
        if _INSTANCE_NAME.fullmatch(instance) is None:
            raise ValueError(f"not an instance name: {instance!r}")
        self._boundaries = boundaries
        self._instance = instance
        self._definition = definition

    def claim(self, branch: str, path: str, document: WorkItemDocument, stage: str) -> StageStart:
        """Write the claim and its "started" entry, commit them and push the commit.

        The push is the claim. Raises `ValueError` before writing anything when the work item
        cannot be claimed here, and `PushFailed` when the push does not reach the remote.
        """
        state = require_state(document, _no_state())
        lease_duration = self._check_preconditions(branch, path, state, stage)
        claim = Claim(
            instance=self._instance,
            stage=stage,
            started_at=self._boundaries.clock.now(),
            lease_duration=lease_duration,
        )
        claimed = self._with_claim(document, state, claim)
        self._boundaries.work_item_writer.write(self._boundaries.checkout / path, claimed)
        git = self._boundaries.git
        commit = git.commit(
            commit_subject(_work_item_id(path), f"{stage} starts as {self._instance}")
        )
        outcome = git.push(branch)
        if outcome != "pushed":
            raise PushFailed(branch, outcome)
        return StageStart(commit=commit, claim=claim)

    def status(self, state: WorkItemState) -> ClaimStatus:
        """The status of the state's claim for this instance, by the claim's own lease."""
        return claim_status(state.claim, instance=self._instance, now=self._boundaries.clock.now())

    def release(self, document: WorkItemDocument) -> WorkItemDocument:
        """Return the document with its claim cleared; `ValueError` when it has no state."""
        state = require_state(document, ValueError("the work item has no state to release"))
        released_state = state.model_copy(update={"claim": None})
        return document.model_copy(update={"state": released_state})

    def _check_preconditions(self, branch: str, path: str, state: WorkItemState, stage: str) -> int:
        if stage != state.stage:
            raise ValueError(f"the work item is in stage {state.stage}, not {stage}")
        lease_duration = self._lease_duration_of(stage)
        own_branch = _own_branch(path)
        if branch != own_branch:
            raise ValueError(f"{branch} is not the work item's branch {own_branch}")
        checked_out = self._boundaries.git.status().branch
        if checked_out != branch:
            raise ValueError(f"the checkout is on {checked_out}, not on {branch}")
        return lease_duration

    def _lease_duration_of(self, stage: str) -> int:
        if stage not in self._definition.stages:
            raise ValueError(f"{stage} is not a stage of the pipeline definition")
        role = self._definition.role_of(stage)
        if role is None:
            raise ValueError(f"stage {stage} has no role to claim it for")
        return role.lease_duration

    def _with_claim(
        self, document: WorkItemDocument, state: WorkItemState, claim: Claim
    ) -> WorkItemDocument:
        claimed_state = state.model_copy(update={"claim": claim})
        entry = NewEntry(
            speaker="factory", kind="started", text=started_text(claim.stage, self._instance)
        )
        claimed = document.model_copy(update={"state": claimed_state})
        return append_entry(claimed, entry, at=claim.started_at)


def _no_state() -> ValueError:
    return ValueError("the work item has no state to claim")


def _own_branch(path: str) -> str:
    return branch_name(_work_item_id(path))


def _work_item_id(path: str) -> WorkItemId:
    file_name = parse_work_item_file_name(PurePosixPath(path).name)
    if file_name is None:
        raise ValueError(f"{path} is not a work item's file")
    return file_name.id
