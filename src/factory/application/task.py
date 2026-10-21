"""What a stage prepares before its agent runs: the agent, the request and the story form check."""

from collections.abc import Mapping
from datetime import timedelta

from pydantic import BaseModel, ConfigDict, PositiveInt

from factory.application.acceptance import AcceptanceService
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceState, acceptance_prompt
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, GuardSettings
from factory.domain.errors import WorkItemFormatError
from factory.domain.identifiers import Name, WorkItemId, feature_of, is_acceptance
from factory.domain.journal import last_record
from factory.domain.paths import MAIN_BRANCH, REMOTE, STORY_FORM_FILE
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition
from factory.domain.prompts import (
    CODER_ROLE,
    TESTER_ROLE,
    PromptFacts,
    allowed_decisions,
    compose_prompt,
)
from factory.domain.story_form import FormFinding, check_story_form
from factory.domain.work_item import WorkItemDocument, require_state

# The form is read where only the human's merge changes it, never from the work tree an agent
# writes in.
FORM_REF = f"{REMOTE}/{MAIN_BRANCH}"


class TaskContext(BaseModel):
    """The work item a stage runs on: its place, document, branch, form findings and guard."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_item: WorkItemId
    path: str
    stage: Name
    document: WorkItemDocument
    branch: str
    pull_request: PositiveInt
    findings: list[FormFinding]
    guard: GuardSettings


class StoryFormChecker:
    """Checks a story against the project's form as it stands at `FORM_REF`."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Read the form through the git of `boundaries`."""
        self._boundaries = boundaries

    def findings(self, document: WorkItemDocument) -> list[FormFinding]:
        """The findings against the form; `WorkItemFormatError` when the form is absent.

        An acceptance's report is no story, so it has no form to meet and gets no findings.
        """
        if isinstance(document.state, AcceptanceState):
            return []
        form = self._boundaries.git.show_file(FORM_REF, STORY_FORM_FILE)
        if form is None:
            raise WorkItemFormatError(f"the story form is missing at {FORM_REF}", STORY_FORM_FILE)
        return check_story_form(document, form, folder="in-progress")


class TaskComposer:
    """Picks a stage's agent and composes the request for its run from the pipeline definition."""

    def __init__(
        self,
        boundaries: Boundaries,
        definition: PipelineDefinition,
        environment: Mapping[str, str],
    ) -> None:
        """Compose for `definition`; every request carries a copy of `environment` as given."""
        self._boundaries = boundaries
        self._definition = definition
        self._environment = environment

    def agent(self, stage: str) -> AgentDefinition:
        """The agent definition of the role that works in `stage`.

        `ValueError` for a stage without a role; `AgentDefinitionMissing` propagates.
        """
        return self._boundaries.agent_definitions.read(self._role_name(stage))

    def compose(self, context: TaskContext, agent: AgentDefinition) -> AgentRunRequest:
        """The request for `agent`'s run on `context`, its decisions shared with its prompt."""
        decisions = allowed_decisions(self._definition.stages[context.stage].next)
        facts = PromptFacts(
            work_item=context.work_item,
            path=context.path,
            stage=context.stage,
            allowed_decisions=decisions,
            branch=context.branch,
            pull_request=context.pull_request,
            round=self._round(context),
            test_change_entry=self._test_change_entry(context),
            findings=self._findings(context),
        )
        return AgentRunRequest(
            agent=agent,
            prompt=self._prompt(context, facts),
            allowed_decisions=decisions,
            time_limit=timedelta(minutes=self._role(context.stage).time_limit),
            working_directory=self._boundaries.checkout,
            environment=dict(self._environment),
            guard=context.guard,
            os_user=self._boundaries.settings.agent_user,
        )

    def _prompt(self, context: TaskContext, facts: PromptFacts) -> str:
        prompt = compose_prompt(facts)
        if not self._is_acceptance_run(context):
            return prompt
        service = AcceptanceService(self._boundaries, self._definition)
        return acceptance_prompt(prompt, service.facts(feature_of(context.work_item)))

    def _is_acceptance_run(self, context: TaskContext) -> bool:
        at_acceptance_stage = context.stage == self._definition.acceptance_stage
        return at_acceptance_stage and is_acceptance(context.work_item)

    def _role_name(self, stage: str) -> str:
        if stage not in self._definition.stages:
            raise ValueError(f"{stage} is not a stage of the pipeline definition")
        role = self._definition.stages[stage].role
        if role is None:
            raise ValueError(f"stage {stage} has no role, so no agent runs there")
        return role

    def _role(self, stage: str) -> RoleDefinition:
        return self._definition.roles[self._role_name(stage)]

    def _round(self, context: TaskContext) -> int:
        error = WorkItemFormatError("the document has no state", context.path)
        return require_state(context.document, error).round

    def _findings(self, context: TaskContext) -> list[FormFinding] | None:
        if context.stage != self._definition.first_stage():
            return None
        return context.findings

    def _test_change_entry(self, context: TaskContext) -> int | None:
        if self._definition.stages[context.stage].role != TESTER_ROLE:
            return None
        # The last result, not the last record: a stall or a copied comment after the coder's
        # result must not hide the approved test change from the tester's next attempt.
        result = last_record(context.document, kind="result")
        if result is None or result.speaker != CODER_ROLE:
            return None
        return result.number
