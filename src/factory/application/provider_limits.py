"""Patient runs: a run the provider's spend limit stopped waits it out and resumes, to a ceiling."""

from datetime import timedelta
from decimal import Decimal

from factory.application.boundaries import Boundaries
from factory.application.machine import Waiter
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult, EndReason, resumed_result

CONTINUE_PROMPT = (
    "The provider's spend limit stopped your run. Continue the work where you stopped, "
    "then end as your instructions say."
)


class PatientRuns:
    """Runs a stage's agent and waits out the provider's spend limit, resuming after each wait."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Run through the boundaries' runtime, and wait with their waiter."""
        self._boundaries = boundaries
        self._limit = boundaries.settings.provider_limit

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run `request`; after a `provider_limit`, wait and resume with what is left.

        The run ends `budget` or `time_limit` when nothing of either is left after a limit, and
        `provider_limit` when the waits reach the ceiling. The waits count toward neither.
        """
        result = self._boundaries.agent_runtime.run(request)
        waiter = self._boundaries.waiter
        waited = timedelta(0)
        while result.end_reason == "provider_limit":
            budget_left = request.agent.budget_usd - (result.cost_usd or Decimal(0))
            time_left = request.time_limit - result.duration
            if budget_left <= 0:
                return _ended(result, "budget")
            if time_left <= timedelta(0):
                return _ended(result, "time_limit")
            if waited >= self._limit.ceiling:
                self._log_ceiling(request, waited)
                return result
            waited += self._wait(waiter, request, result, waited)
            resumed = self._boundaries.agent_runtime.run(
                _resumed_request(request, result.session, budget_left, time_left)
            )
            result = resumed_result(result, resumed)
        return result

    def _wait(
        self,
        waiter: Waiter,
        request: AgentRunRequest,
        result: AgentRunResult,
        waited: timedelta,
    ) -> timedelta:
        wanted = result.limit_wait or self._limit.cooldown
        wait = min(wanted, self._limit.ceiling - waited)
        resumes = result.session or "a new run"
        self._boundaries.log.line(
            f"provider limit: {request.agent.name} waits {_seconds(wait)} s "
            f"before it resumes {resumes}"
        )
        waiter.wait(wait)
        return wait

    def _log_ceiling(self, request: AgentRunRequest, waited: timedelta) -> None:
        self._boundaries.log.line(
            f"provider limit: {request.agent.name} waited {_seconds(waited)} s, "
            f"the ceiling of {_seconds(self._limit.ceiling)} s; the run ends provider_limit"
        )


def _resumed_request(
    request: AgentRunRequest, session: str | None, budget_left: Decimal, time_left: timedelta
) -> AgentRunRequest:
    agent = request.agent.model_copy(update={"budget_usd": budget_left})
    update: dict[str, object] = {"agent": agent, "time_limit": time_left}
    # Without a session there is nothing to continue; the stage's own prompt starts it afresh.
    if session is not None:
        update |= {"prompt": CONTINUE_PROMPT, "resume_session": session}
    return request.model_copy(update=update)


def _ended(result: AgentRunResult, end_reason: EndReason) -> AgentRunResult:
    return result.model_copy(update={"end_reason": end_reason, "limit_wait": None})


def _seconds(duration: timedelta) -> int:
    return int(duration.total_seconds())
