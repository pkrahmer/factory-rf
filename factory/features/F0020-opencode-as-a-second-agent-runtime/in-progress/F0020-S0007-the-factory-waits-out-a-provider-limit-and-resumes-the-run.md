---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 259
comments_read: [6265170554, 6265355420]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T10:30:35.107104Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T10:30:35.112035Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-19T10:30:57.474997Z'
  stage: intake
  run: dfd6d87e07b840e3a9d9ef5ad76e72d9
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-19T10:31:43.478001Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-19T10:32:06.284441Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-19T10:32:29.572034Z'
  stage: intake
  run: af491629e30f465888a9f8628f122908
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-19T10:32:50.565965Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-19T10:38:45.575529Z'
  stage: tests
  run: 85de9328a509459c9a424472213a5ac1
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-19T10:39:06.124824Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-10-19T10:41:40.684349Z'
  stage: doing
  run: d9a14394ec744c159466958d48395923
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-10-19T10:42:56.928106Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T10:43:14.681817Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-19T10:43:29.881559Z'
  stage: doing
  run: 929ed80a18a84b8f954271f9ba989fd8
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T10:43:50.332898Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-10-19T10:45:25.927757Z'
  stage: tests
  run: 505d9d0240d1462eb103fbd415307583
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-19T10:45:46.669260Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-10-19T10:47:36.211318Z'
  stage: doing
  run: 4f6b0d7be5fb4d518f01eee69dc06ab8
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-19T10:47:56.799760Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-10-19T10:49:01.372614Z'
  stage: review
  run: 8748505153d444448db07be10fb3efcb
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-19T10:49:21.707926Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-10-19T10:49:52.735479Z'
  stage: doing
  run: 16f277d025334f0b8d5e4b8f7a78eb6c
- number: 22
  speaker: factory
  kind: started
  at: '2026-10-19T10:50:13.244609Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-10-19T10:51:57.785406Z'
  stage: tests
  run: 7adeae54c08f4358a247951eba8612ef
- number: 24
  speaker: factory
  kind: started
  at: '2026-10-19T10:52:18.126772Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-10-19T10:54:03.259301Z'
  stage: doing
  run: f557cc852f274181893aadc009ca517c
---

# The factory waits out a provider limit and resumes the run

## Description

After S0005 and S0006, a run that meets the provider's spend limit ends `provider_limit` with its session kept, on either runtime, but the stage still stalls it, counts an attempt, and asks the human at the cap. At the human's work the limit passes by itself within minutes, and the factory must run unattended around the clock. This story adds the shared part, in the application layer behind the agent-runtime interface: `PatientRuns` runs a stage's agent and, after a `provider_limit`, waits out a cool-down (an operator setting, default 10 minutes, or the wait the provider's message names), with no agent process running and without asking anyone, then resumes the same session with a short continue prompt, the budget that is left and the time limit that is left. Repeated limits keep waiting; the waits count toward neither the stage's `time_limit` nor its attempts. Only when the waits reach a long ceiling (an operator setting, default 2 hours) does the run end `provider_limit`, and the stage stalls it with its note on the pull request, which reaches the human. Each runtime only maps its own signal to the end reason (S0005, S0006); the waiting is the same for both. The waiting itself is an interface, `Waiter`, so that tests advance a manual clock instead of sleeping. The preflight's probe does not wait: a limit there is a failed probe, as today.

## Interface

`factory.application.machine` (`application`):

```python
class Waiter(ABC):
    """Waits for a time without holding anything; the factory has no sleep of its own."""

    @abstractmethod
    def wait(self, duration: timedelta) -> None:
        """Return after `duration`; a negative one raises `ValueError`."""
```

`factory.adapters.clock` (`adapters`):

```python
class SleepingWaiter(Waiter): ...                      # time.sleep
class ManualWaiter(Waiter):
    def __init__(self, clock: ManualClock) -> None: ...
    @property
    def waits(self) -> list[timedelta]: ...
```

- `SleepingWaiter.wait` sleeps for the duration; `ManualWaiter.wait` advances its clock by it and records it, returning at once. Both raise `ValueError` for a negative duration; zero returns at once.

`factory.application.boundaries` (`application`):

- `Boundaries` gains `waiter: Waiter | None = None`, last.

`factory.domain.provider_limits` (`domain`):

```python
DEFAULT_COOLDOWN = timedelta(minutes=10)
DEFAULT_CEILING = timedelta(minutes=120)

class ProviderLimit(BaseModel):
    ...                                   # S0005's status and message
    cooldown: timedelta = DEFAULT_COOLDOWN
    ceiling: timedelta = DEFAULT_CEILING
```

- `cooldown` is at least one minute; `ceiling` is at least the `cooldown` (`the ceiling is shorter than the cool-down` otherwise).

`factory.domain.settings` (`domain`):

```python
PROVIDER_LIMIT_COOLDOWN_VARIABLE = "FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES"
PROVIDER_LIMIT_CEILING_VARIABLE = "FACTORY_PROVIDER_LIMIT_CEILING_MINUTES"
```

- `read_settings`: each, unset or blank, gives its default; a whole number of minutes of at least 1 in ASCII digits gives that; any other raises `SettingsInvalid` naming the variable with `is not a whole number of minutes of at least 1`. A ceiling below the cool-down raises `SettingsInvalid` naming the ceiling's variable with `is shorter than the cool-down`.

`factory.application.provider_limits` (`application`, new):

```python
CONTINUE_PROMPT = (
    "The provider's spend limit stopped your run. Continue the work where you stopped, "
    "then end as your instructions say."
)

class PatientRuns:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
```

- `run` calls `boundaries.agent_runtime.run(request)` and returns a result whose end reason is not `provider_limit` as it is.
- Without a waiter (`boundaries.waiter` is `None`), a `provider_limit` result is returned as it is, after one call.
- The limit's settings are `boundaries.settings.provider_limit`, or `ProviderLimit()` without settings.
- After a `provider_limit`, in this order:
  1. The budget left is the agent's `budget_usd` less the run's cost so far (`None` counts 0); at or below zero, the run ends `budget` (the result so far with that end reason and no `limit_wait`), without a wait.
  2. The time left is the request's `time_limit` less the sum of the calls' durations so far (the waits do not count); at or below zero, the run ends `time_limit` in the same way.
  3. The waits so far reach the ceiling: the run ends `provider_limit`, and the factory log gets `provider limit: <agent> waited <s> s, the ceiling of <c> s; the run ends provider_limit`.
  4. Otherwise it waits the result's `limit_wait`, or the cool-down without one, at most what is left of the ceiling; the factory log gets `provider limit: <agent> waits <w> s before it resumes <session>` (`a new run` when the result has no session) before the wait.
  5. It calls the runtime again with `request.model_copy(update=...)`: with a session, `prompt` `CONTINUE_PROMPT` and `resume_session` the session; without one, the request's own prompt and no `resume_session`; in both, the agent's `budget_usd` the budget left and `time_limit` the time left.
  6. The run so far and the new call are joined by `resumed_result` (S0002, S0005): the costs, turns, tokens and durations summed, the new call's end, session and wait.
- Seconds in the log lines are whole seconds (`int(...)`).
- It builds no `AgentRunRequest` of its own (`tests/test_agent_run_request_search.py` passes unchanged): every resumed request is a `model_copy` of the stage's.

`factory.application.sealed_runs` (`application`):

```python
def run_sealed(boundaries: Boundaries, request: AgentRunRequest, *,
               run: Callable[[AgentRunRequest], AgentRunResult] | None = None) -> SealedRun: ...
```

- With `run`, the sealed run calls it instead of `boundaries.agent_runtime.run`; the seal, its check and the removal of nested repositories are unchanged.

`factory.application.stage` (`application`):

- `StageLauncher.launch` runs the agent through `run_sealed(..., run=PatientRuns(boundaries).run)`; its cost record is begun before and completed after the whole patient run, so a run resumed after a limit is one record. A run that ends `provider_limit` stalls with that reason (S0005's sentence), one attempt counted, as every early end does.
- The preflight's probe keeps `run_sealed` without `run`.

`factory.entry.wiring` (`entry`):

- `build_boundaries` gives the boundaries a `SleepingWaiter()`.

Tests (the tester writes them): `tests/adapters/test_waiters.py`, `tests/domain/test_provider_limit_wait.py`, `tests/domain/test_settings_provider_limit_wait.py`, `tests/application/test_patient_runs.py` (with `FakeAgentRuntime`, `ManualClock` and `ManualWaiter`, the boundaries fixture of `tests/conftest.py` given a waiter and settings by `dataclasses.replace`), `tests/application/test_sealed_runs_runner.py`, `tests/application/test_stage_provider_limit.py` (a stage launched and processed as `tests/application/test_stage_launch.py` and `tests/application/test_stalls.py` do, their helpers imported, not copied), `tests/entry/test_wiring_waiter.py`. No earlier test changes.

## Acceptance criteria

1. `ManualWaiter.wait(timedelta(minutes=10))` advances its clock by ten minutes and records the wait; `SleepingWaiter` and `ManualWaiter` return at once for zero and raise `ValueError` for minus one second (rows).
2. `ProviderLimit` takes the defaults of 10 and 120 minutes, accepts a cool-down of one minute and a ceiling equal to it, and refuses a cool-down of 59 seconds and a ceiling below the cool-down (rows).
3. `read_settings` gives 10 and 120 minutes without the variables or with blank ones, 5 and 60 for `5` and `60`; it raises `SettingsInvalid` naming the variable for `0`, `-1`, `abc` and `1.5`, and naming the ceiling's variable for a cool-down of 30 and a ceiling of 20 (rows).
4. A completed result, and a `died` one, come back as the runtime gave them, after one call and no wait (rows).
5. A `provider_limit` result with session `ses_a`, cost 0.20, duration 5 seconds and no `limit_wait`, then a completed one of cost 0.30 and 5 seconds, under a budget of 1 and a time limit of 60 seconds: one wait of 600 seconds; the second request has the prompt `CONTINUE_PROMPT`, `resume_session` `ses_a`, a budget of 0.80 and a time limit of 55 seconds, and keeps every other field of the first; the result is `completed` with cost 0.50, a duration of 10 seconds and the second call's decision and entry.
6. A `limit_wait` of 420 seconds is waited instead of the cool-down; one of 3 hours is cut to the ceiling of 2 hours (rows).
7. Under a cool-down of 10 and a ceiling of 30 minutes, a runtime that ends `provider_limit` on every call is called four times with three waits of 600 seconds, and the run ends `provider_limit`; the factory log holds three wait lines and then `provider limit: coder waited 1800 s, the ceiling of 1800 s; the run ends provider_limit`.
8. A limit with a named wait of 25 minutes under a ceiling of 30 minutes waits 1500 seconds, then 300 seconds after a second limit, then ends at the third (rows of waits recorded).
9. A `provider_limit` result without a session is followed by a call with the request's own prompt and no `resume_session`, and the log line ends `before it resumes a new run`; the second request also carries a budget of 0.80 and a time limit of 55 seconds, as in criterion 5.
10. A `provider_limit` result whose cost is 1.00 or more under a budget of 1 ends the run `budget`, one whose duration has used the whole time limit ends it `time_limit`, and one that has used up both ends it `budget`, each without a wait and after one call, with no `limit_wait` (rows).
11. Without a waiter, a `provider_limit` result comes back after one call; without settings, the defaults of 600 and 7200 seconds apply (rows).
12. `run_sealed` with `run` calls it and not the runtime, and seals and checks as without it (rows).
13. A stage whose fake runtime gives a `provider_limit` and then a completed run with the decision `doing` moves on as for a completed run: the work item's attempts are unchanged, its sidecar holds one completed cost record with both calls' costs, and the waiter recorded 600 seconds.
14. A stage under a cool-down and a ceiling of one minute whose runtime ends `provider_limit` twice stalls with the reason `provider_limit`: attempt 1 of 2, the note `Stalled (attempt 1 of 2): the provider's spend limit lasted past the waiting ceiling. Retrying on the next tick.` on the pull request.
15. The preflight's probe whose fake run ends `provider_limit` fails `agent-run-probe` after one call, with no wait (`the probe run ended provider_limit; ...`).
16. `build_boundaries` gives a `SleepingWaiter`.
17. A `limit_wait` of 90.9 seconds gives the log line `provider limit: coder waits 90 s before it resumes ses_a` and `ManualWaiter.waits` records the wait of 90.9 seconds; a ceiling reached after waits that sum to 1800.7 seconds gives the log line `provider limit: coder waited 1800 s, the ceiling of <c> s; the run ends provider_limit` with whole seconds (rows).
18. `read_settings` accepts the lower bound of each rule: a cool-down of `1` and a ceiling of `1` give one minute each (the least whole number of minutes, and a ceiling equal to the cool-down), and a cool-down of `30` and a ceiling of `30` give 30 minutes each (a row beside criterion 3's `5` and `60`).
19. `make check` stays green.
20. docs: `docs/operator-guide.md`: a section *A provider's spend limit*: what a limit is (HTTP 428 behind a gateway, or the operator's pattern), that the factory waits the named wait or `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` (default 10) and resumes the same session with what is left of the budget and the time limit, without counting an attempt; that it stalls after `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` (default 120) of waiting, and what to do then; the two log lines; that the claim stays held while waiting, so that a stage may hold it past its `lease_duration`, which only another instance on the same repository would act on (run one instance per repository); that a stop or restart during a wait reruns the stage as a crash. The configuration table gets both variables, and the stall reasons `provider_limit` gets what to do. `docs/project-guide/stages.md`, *Starting a stage*: `PatientRuns`, the `Waiter` interface and its two implementations. `docs/project-guide/watching.md`, *Boundaries* in *Stops, the clock and the factory log*: `run_sealed`'s `run`. `docs/decisions.md`: an entry *The factory waits out a provider limit around a stage's run*, dated with the story, with the reasons of the feature's decision 14.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/work"
uv run -q python - "$d" <<'EOF'
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.clock import ManualClock, ManualWaiter
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.machine import FactoryLog
from factory.application.provider_limits import CONTINUE_PROMPT, PatientRuns
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, AgentRunResult


class Lines(FactoryLog):
    def __init__(self) -> None:
        self.lines: list[str] = []

    def line(self, text: str) -> None:
        self.lines.append(text)


d = Path(sys.argv[1])
clock = ManualClock(datetime(2026, 10, 18, tzinfo=UTC))
runtime = FakeAgentRuntime()
second = timedelta(seconds=5)
runtime.queue(ScriptedRun(result=AgentRunResult(end_reason="provider_limit", duration=second, cost_usd=Decimal("0.2"), session="ses_smoke", limit_wait=timedelta(minutes=7))))
runtime.queue(ScriptedRun(result=AgentRunResult(end_reason="provider_limit", duration=second, cost_usd=Decimal("0.1"), session="ses_smoke")))
runtime.queue(ScriptedRun(result=AgentRunResult(end_reason="completed", decision="question", entry="Done.", duration=second, cost_usd=Decimal("0.3"), session="ses_smoke")))
waiter = ManualWaiter(clock)
log = Lines()
unused = None
boundaries = Boundaries(git=unused, hosting=unused, agent_runtime=runtime, project_commands=unused, work_item_reader=unused, work_item_writer=unused, cost_reader=unused, cost_writer=unused, pipeline_reader=unused, agent_definitions=unused, clock=clock, log=log, health=unused, checkout=d, waiter=waiter)
agent = AgentDefinition(name="coder", model="sonnet", tools=["Read"], budget_usd=Decimal("1"), instructions="Smoke.")
request = AgentRunRequest(agent=agent, prompt="Smoke.", allowed_decisions=["question"], time_limit=timedelta(seconds=60), working_directory=d / "work")
result = PatientRuns(boundaries).run(request)
print(result.end_reason, result.cost_usd, result.duration.total_seconds())
print([wait.total_seconds() for wait in waiter.waits], clock.now().isoformat())
resumed = runtime.requests()[1]
print(resumed.prompt == CONTINUE_PROMPT, resumed.resume_session, resumed.agent.budget_usd, resumed.time_limit.total_seconds())
print(log.lines[0])
EOF
```
Expect: four lines, `completed 0.6 15.0`, `[420.0, 600.0] 2026-10-18T00:17:00+00:00`, `True ses_smoke 0.8 55.0`, `provider limit: coder waits 420 s before it resumes ses_smoke`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: 1. The Interface says "Seconds in the log lines are whole seconds (`int(...)`)", and no criterion tests it. Every wait in criteria 5–9 is a whole number of seconds, so a coder who rounds, or who prints `600.0`, would pass. Proposed new criterion, placed before the two closing ones: a `limit_wait` of 90.9 seconds (the same input would also fix what `ManualWaiter.waits` records) gives the log line `provider limit: coder waits 90 s before it resumes ses_a`, and a ceiling reached after waits that sum to 1800.7 seconds gives `waited 1800 s`. I would choose this criterion. Alternative: drop the sentence from the Interface.

   2. Criterion 9 checks only the prompt, `resume_session` and the log line for a limit without a session. Interface step 5 says the budget left and the time left apply in both cases. Proposed addition to criterion 9: the second request also carries a budget of 0.80 and a time limit of 55 seconds, as in criterion 5. I would choose this addition.

   Checks that passed:
   - The Interface names concrete modules and signatures, and `Boundaries.settings`, `FakeAgentRuntime.queue` and `requests`, `ManualClock` and `FactoryLog` exist.
   - The smoke test is runnable and its numbers add up (cost 0.6, duration 15, waits 420 and 600 for 17 minutes, budget 0.8, time 55). Its `Expect:` lines are checkable.
   - The architecture is right: the `Waiter` interface sits in `application`, the adapters in `adapters`, the limits in `domain`, and wiring in `entry`.
   - The story is inside the feature's scope for S0007 and touches no "Out of scope" item.
   - The rules each have a failing-side criterion, except the two gaps above.
4. 2026-10-19 human: 1. Yes, add the criterion as you propose, before the two closing ones: a `limit_wait` of 90.9 seconds gives the log line `provider limit: coder waits 90 s before it resumes ses_a` (and `ManualWaiter.waits` records what the Interface says it records), and a ceiling reached after waits summing to 1800.7 seconds gives `waited 1800 s`. Keep the Interface sentence.
   2. Yes, extend criterion 9 as you propose: the second request also carries a budget of 0.80 and a time limit of 55 seconds, as in criterion 5.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete modules and signatures (`Waiter`, `SleepingWaiter`, `ManualWaiter`, `Boundaries.waiter`, `ProviderLimit` fields, the two settings variables, `PatientRuns`, `run_sealed(run=)`). The step-by-step order of `PatientRuns.run` is fully stated. Every behaviour has a criterion. This includes the whole-second log lines, which journal entry 4 added as criterion 17.
   - Criteria: each is testable by one parametrized test. Every rule has its failing side: negative duration (1), cool-down under one minute and ceiling below the cool-down (2), invalid settings values and ceiling below cool-down (3), budget and time-limit exhaustion with no wait (10), no waiter (11), probe without wait (15). The ceiling cut, the named wait, the session-less resume and the whole-second logging each have their own criterion (6, 8, 9, 17). Edits carried in from the human's answer (journal entry 4): criterion 9 now also names the second request's budget of 0.80 and time limit of 55 seconds; the new criterion 17 (whole seconds, `ManualWaiter.waits` recording 90.9) sits before the two closing ones, which are now 18 (`make check`) and 19 (`docs:`).
   - Smoke test: runnable, and its numbers add up (cost 0.6, duration 15 s, waits 420 and 600 s, clock 00:17:00, budget 0.8, time limit 55 s). Its `Expect:` line is checkable.
   - Architecture: the `Waiter` interface lives in `application`, its implementations in `adapters`, the limit values in `domain`, and the wiring in `entry`. The layering holds, and no `AgentRunRequest` is built outside `model_copy`.
   - Scope: within S0007's part of F0020's Scope. It touches no "Out of scope" item and changes no earlier test.
7. factory: started tests as self.
8. tester: Wrote the tests for criteria 1–17. `make lint` is green. `make test` fails as intended: the test modules cannot be imported because the modules and names under test don't exist yet.

   Criterion → test:
   - criterion 1: tests/adapters/test_waiters.py::test_a_manual_wait_advances_the_clock_and_is_recorded, and tests/adapters/test_waiters.py::test_a_wait_of_zero_returns_and_a_negative_one_is_refused (rows: sleeping and manual waiter × zero and minus one second)
   - criterion 2: tests/domain/test_provider_limit_wait.py::test_the_limit_waits_ten_minutes_up_to_two_hours_by_default, and tests/domain/test_provider_limit_wait.py::test_the_cooldown_is_a_minute_or_more_and_the_ceiling_no_shorter (rows: 1 min/1 min, 59 s cool-down, ceiling one second below the cool-down)
   - criterion 3: tests/domain/test_settings_provider_limit_wait.py::test_the_variables_have_their_names, ::test_the_cooldown_and_ceiling_are_read_in_minutes, ::test_a_value_that_is_not_whole_minutes_of_at_least_one_is_refused, ::test_a_ceiling_below_the_cooldown_is_refused_naming_the_ceiling
   - criterion 4: tests/application/test_patient_runs.py::test_a_run_not_stopped_by_a_limit_comes_back_as_it_is
   - criterion 5: tests/application/test_patient_runs.py::test_a_limited_run_waits_the_cooldown_and_resumes_its_session_with_what_is_left
   - criterion 6: tests/application/test_patient_runs.py::test_a_named_wait_is_waited_instead_of_the_cooldown_within_the_ceiling
   - criterion 7: tests/application/test_patient_runs.py::test_a_limit_that_lasts_ends_the_run_at_the_ceiling
   - criterion 8: tests/application/test_patient_runs.py::test_a_named_wait_is_cut_to_what_is_left_of_the_ceiling (rows: second limit names 25 min, or names nothing)
   - criterion 9: tests/application/test_patient_runs.py::test_a_limited_run_without_a_session_starts_a_new_run_with_what_is_left
   - criterion 10: tests/application/test_patient_runs.py::test_a_limited_run_with_nothing_left_ends_without_a_wait (rows on both sides of each bound: cost 1.00, 1.20 and 0.99; duration 60 s and 59 s; both used up)
   - criterion 11: tests/application/test_patient_runs.py::test_without_a_waiter_a_limited_run_comes_back_after_one_call, and ::test_without_settings_the_default_limit_applies
   - criterion 12: tests/application/test_sealed_runs_runner.py::test_a_sealed_run_calls_its_runner_instead_of_the_runtime (rows: git folder left sealed, git folder swapped)
   - criterion 13: tests/application/test_stage_provider_limit.py::test_a_stage_that_waits_out_a_limit_moves_on_as_a_completed_run
   - criterion 14: tests/application/test_stage_provider_limit.py::test_a_stage_whose_limit_outlasts_the_ceiling_stalls_with_its_note
   - criterion 15: tests/application/test_sealed_runs_runner.py::test_the_probe_does_not_wait_out_a_provider_limit
   - criterion 16: tests/entry/test_wiring_waiter.py::test_the_built_boundaries_wait_by_sleeping
   - criterion 17: tests/application/test_patient_runs.py::test_the_log_lines_give_whole_seconds_and_the_waits_are_kept_whole (rows: a 90.9 s named wait; a ceiling of 1800.7 s reached after waits of 600, 600 and 600.7 s)

   Files created:
   - tests/adapters/test_waiters.py
   - tests/domain/test_provider_limit_wait.py
   - tests/domain/test_settings_provider_limit_wait.py
   - tests/application/test_patient_runs.py
   - tests/application/test_sealed_runs_runner.py
   - tests/application/test_stage_provider_limit.py
   - tests/entry/test_wiring_waiter.py

   No earlier test was changed.

   Decisions worth knowing:
   - The stage tests (13, 14) use the shared helpers in `tests/stage_run_support.py` (`open_story`, `run_stage`, `pushed_state`, `branch_head`). This is the shared form of what test_stage_launch and test_stalls do, so nothing is copied.
   - The sealed-run tests import `_request`, `_swap_for_folder` and the constants from `application.test_sealed_runs`.
   - The probe test (15) is in test_sealed_runs_runner.py, because the Interface names no file for it.
   - For criterion 17's second row, the 1800.7 s total is only reachable with a ceiling of exactly 1800.7 s. The waits are cut at the ceiling, so they can never add up to more than it. The expected line is therefore `waited 1800 s, the ceiling of 1800 s`.

   Modules the test run could not import (the cause of the collection errors):
   - factory.adapters.clock: ManualWaiter, SleepingWaiter
   - factory.application.machine: Waiter
   - factory.application.provider_limits
   - factory.domain.provider_limits: DEFAULT_COOLDOWN, DEFAULT_CEILING
   - factory.domain.settings: PROVIDER_LIMIT_COOLDOWN_VARIABLE, PROVIDER_LIMIT_CEILING_VARIABLE

   `Boundaries.waiter` and `run_sealed(..., run=)` don't exist yet either.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/entry/test_wiring_waiter.py - ImportError while importing test mo...
9. factory: started doing as self.
10. coder: I stopped at one failing test row: `tests/application/test_patient_runs.py::test_the_log_lines_give_whole_seconds_and_the_waits_are_kept_whole[ceiling]`. It contradicts the Interface. Everything else is built and passes. In `make check`, lint, types, layers, sast, secrets and licenses are green, and every test passes except this row.

    **The contradiction.** The row sets a cool-down of 10 minutes and a ceiling of 1800.7 s. Every call ends `provider_limit` with no `limit_wait`. It expects the waits `[600, 600, 600.7]`. Interface step 4 says the run waits "the result's `limit_wait`, or the cool-down without one, at most what is left of the ceiling". So the third wait is min(600, 600.7) = 600 s, not 600.7 s. The waits then total 1800 s, which is still below the ceiling, so step 3 does not end the run: a fourth wait of 0.7 s follows. The waits are `[600, 600, 600, 0.7]`. After that the line `waited 1800 s, the ceiling of 1800 s; the run ends provider_limit` matches what the row expects. Only the `waiter.waits` assertion fails. The tester's entry assumes the waits are cut at the ceiling, which is right, but the third wait is the cool-down and the cut leaves it at 600 s.

    **Options:**
    - (a) Change the row's expected waits to `[timedelta(seconds=600)] * 3 + [timedelta(seconds=0.7)]`. The log line stays as it is, so it still checks whole seconds on the ceiling line. **I would choose (a).**
    - (b) Keep the row's waits and change the Interface so that the last wait takes up a remainder of the ceiling shorter than the cool-down. That adds a rule no criterion asks for.
    - (c) Use data that reaches 1800.7 s exactly, such as named waits of 600, 600 and 600.7 s under a ceiling of 1800.7 s. This also fixes the test, but changes its inputs more than (a).

    **What I built:**
    - `src/factory/application/machine.py`: the `Waiter` interface.
    - `src/factory/adapters/clock.py`: `SleepingWaiter` and `ManualWaiter`. Both refuse a negative wait through one shared private check.
    - `src/factory/application/boundaries.py`: `waiter`, added last.
    - `src/factory/domain/provider_limits.py`: `DEFAULT_COOLDOWN`, `DEFAULT_CEILING`, and `cooldown` and `ceiling` on `ProviderLimit`. The cool-down must be at least a minute. A model validator raises "the ceiling is shorter than the cool-down".
    - `src/factory/domain/settings.py`: the two variables, read by `_provider_limit` and `_minutes`. I extracted `_whole_number(environ, variable, unit)` and both `_min_free_gb` and `_minutes` now use it, so the ASCII-digit check is not copied a second time.
    - `src/factory/application/provider_limits.py` (new): `CONTINUE_PROMPT` and `PatientRuns`, a loop that follows steps 1–6 in order. Resumed requests are built only with `model_copy`, and the calls are joined with `resumed_result`.
    - `src/factory/application/sealed_runs.py`: `run_sealed(..., run=)`.
    - `src/factory/application/stage.py`: `launch` passes `run=PatientRuns(boundaries).run`, so one cost record covers the whole patient run. The preflight is unchanged.
    - `src/factory/entry/wiring.py`: `waiter=SleepingWaiter()`.

    **Main choice:** `PatientRuns` is one loop that keeps the joined result and the total of the waits so far, so the budget and time left are worked out from the joined cost and duration. I rejected a recursive resume, which would need the waits passed down through each call.

    **Noticed, not touched:** None of the models I changed appear in the records contract, so no schemas were regenerated. I did not run `make duplicates`.
11. 2026-10-19 human: (a). Change the row's expected waits to `[timedelta(seconds=600)] * 3 + [timedelta(seconds=0.7)]`, as the Interface's steps 3 and 4 give them; the log line stays `waited 1800 s, the ceiling of 1800 s; the run ends provider_limit`, so the row still checks whole seconds on the ceiling line (the waits sum to 1800.7 s). The Interface stays as it is. The tester makes the change in this story's own test.
12. factory: started doing as self.
13. coder: The human's answer (entry 11, option a) asks for a test change, so this goes to the tester. I changed no code and no test. One change is needed: in `tests/application/test_patient_runs.py::test_the_log_lines_give_whole_seconds_and_the_waits_are_kept_whole[ceiling]` (line 314), replace the expected waits `[timedelta(seconds=600)] * 2 + [timedelta(seconds=600.7)]` with `[timedelta(seconds=600)] * 3 + [timedelta(seconds=0.7)]`. Keep the row's ceiling of 1800.7 s and its log line `provider limit: coder waited 1800 s, the ceiling of 1800 s; the run ends provider_limit` as they are.

    The code for this story was built and committed in the previous doing run (entry 10). It lives in `src/factory/application/{machine,provider_limits,sealed_runs,stage,boundaries}.py`, `src/factory/adapters/clock.py`, `src/factory/domain/{provider_limits,settings}.py` and `src/factory/entry/wiring.py`. With the code as it is, this row produces exactly the waits the answer names, so no code change is expected.

    The answer does not change the meaning of the task. The Interface stays as it is, so the Description is not rewritten.
14. factory: started tests as self.
15. tester: I made the one test change the human approved (entry 11, option a), as the coder named it in entry 13.

    The change is in the `ceiling` row of `tests/application/test_patient_runs.py::test_the_log_lines_give_whole_seconds_and_the_waits_are_kept_whole` (line 314). The expected waits were `[timedelta(seconds=600)] * 2 + [timedelta(seconds=600.7)]` and are now `[timedelta(seconds=600)] * 3 + [timedelta(seconds=0.7)]`. These are the waits that Interface steps 3 and 4 give: each wait is the cool-down, cut to what is left of the ceiling.

    These parts of the row are unchanged:
    - the ceiling of 1800.7 s
    - the five limited results, which are enough calls for four waits
    - the expected log line `provider limit: coder waited 1800 s, the ceiling of 1800 s; the run ends provider_limit`

    Because the log line is unchanged, the row still checks that the ceiling line gives whole seconds.

    No other test was changed. Files changed: tests/application/test_patient_runs.py.

    `make test` ran once and ended `test: green (38.9 s)`. Every module imported.

    `lint`: lint: green (0.0 s)
    `test`: test: green (37.8 s)
16. factory: started doing as self.
17. coder: The code was already built in an earlier doing run (entry 10). The tester then changed the `ceiling` row as the human answered (entries 11 and 15). In this run I changed no code and no test. `make check` is green, ending with `check: green`; `make test` reached 99.05 % coverage.

    What I built (in the earlier run, now complete):
    - `src/factory/application/machine.py`: the `Waiter` interface.
    - `src/factory/adapters/clock.py`: `SleepingWaiter` and `ManualWaiter`. They share one private check, `_refuse_negative`.
    - `src/factory/application/boundaries.py`: `waiter: Waiter | None = None`, added last.
    - `src/factory/domain/provider_limits.py`:
      - the constants `DEFAULT_COOLDOWN`, `DEFAULT_CEILING` and `SHORTEST_COOLDOWN`
      - `ProviderLimit.cooldown`, which must be at least one minute (`ge=`)
      - `ProviderLimit.ceiling`, checked by a model validator that raises "the ceiling is shorter than the cool-down"
    - `src/factory/domain/settings.py`: the two `..._MINUTES` variables, read by `_provider_limit` and `_minutes`. The ASCII-digit check now lives in one helper, `_whole_number(environ, variable, unit)`. `_min_free_gb` and `_minutes` both use it, so the check is not copied.
    - `src/factory/application/provider_limits.py` (new): `CONTINUE_PROMPT` and `PatientRuns`. They follow the Interface's steps 1–6 in order. Each resumed request is a `model_copy` of the stage's request, and the calls are joined with `resumed_result`.
    - `src/factory/application/sealed_runs.py`: `run_sealed(..., *, run=None)`.
    - `src/factory/application/stage.py`: `StageLauncher.launch` passes `run=PatientRuns(boundaries).run`, so one cost record covers the whole patient run. The preflight's probe is unchanged.
    - `src/factory/entry/wiring.py`: `waiter=SleepingWaiter()`.

    Main choice: `PatientRuns.run` is a single loop. It keeps the joined result and the total waited so far. Because the joined result's cost and duration are already sums over the calls, the budget left and the time left come straight from them. I rejected a recursive resume, which would have to pass the waits and the original request down through every call.

    Refactor pass: I read the diff against `main` and found nothing to rename, simplify or remove. I made no changes.

    Description: the human's answer (entry 11) changed only one test row's expected waits. The Interface stays as it is, so I did not rewrite the Description.

    Noticed, not touched:
    - Neither `ProviderLimit` nor `InstanceSettings` is in the records contract, so no schemas were regenerated.
    - I did not run `make duplicates`; it is a record for the reviewer.
    - The docs criterion (19) is the documenter's.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 33 known, 3 gone
18. factory: started review as self.
19. reviewer: 1. criterion 18 added: it needs its test. Location: `tests/domain/test_settings_provider_limit_wait.py::test_the_cooldown_and_ceiling_are_read_in_minutes`. Problem: the Interface sets two limits for `read_settings`, and neither is tested at its accepting boundary. The first limit is "a whole number of minutes of at least 1": only `0` (refused) and `5` (accepted) are tested, never `1`. The second is "a ceiling below the cool-down raises": only 30/20 (refused) and 5/60 are tested, never a ceiling equal to the cool-down. The check `ceiling < cooldown` in `src/factory/domain/settings.py` (`_provider_limit`) is its own code, apart from `ProviderLimit`'s validator, so a `<=` there would pass every test. Fix: add the rows `{COOLDOWN: "1", CEILING: "1"}` → 1, 1 and `{COOLDOWN: "30", CEILING: "30"}` → 30, 30 to that parametrized test. No change under `src/` is needed. This gap is in the story too: criterion 3 named only the refused values and the 5/60 pair, so I wrote the accepting side into the work item as criterion 18, and the two closing criteria are now 19 (`make check`) and 20 (`docs:`).

    I stopped at group 1 (acceptance criteria), as the checklist says. Every other criterion from 1 to 17 has a test that checks what its criterion says. Entry 17 records that `make check` was green after the coder.

    Earlier tests: none changed. Every test file in the diff has status `A`.
20. factory: started doing as self.
21. coder: The reviewer added criterion 18 in entry 19. It needs only its test, so this goes to the tester. I changed no code and no test.

    The test change: add two rows to the parametrized `tests/domain/test_settings_provider_limit_wait.py::test_the_cooldown_and_ceiling_are_read_in_minutes`:
    - `{COOLDOWN: "1", CEILING: "1"}` gives a cool-down and a ceiling of 1 minute each.
    - `{COOLDOWN: "30", CEILING: "30"}` gives a cool-down and a ceiling of 30 minutes each.

    They sit beside the existing `5`/`60` row. The test file has no such rows yet.

    No change under `src/` is expected. `_provider_limit` in `src/factory/domain/settings.py` refuses only `ceiling < cooldown`, and `_minutes` accepts any whole number of at least 1. Both new rows are on the accepting side of those rules, so the current code already accepts them.

    What I built is unchanged from entries 10 and 17: `src/factory/application/{machine,provider_limits,sealed_runs,stage,boundaries}.py`, `src/factory/adapters/clock.py`, `src/factory/domain/{provider_limits,settings}.py` and `src/factory/entry/wiring.py`.

    Description: the reviewer added criterion 18 to the work item. The task means the same, and the Interface already states both limits, so I did not rewrite the Description.

    Noticed, not touched: nothing new.
22. factory: started tests as self.
23. tester: I wrote the test for criterion 18, which the reviewer added in entry 19. The coder's entry 21 named the change. It is two new rows in the parametrized `test_the_cooldown_and_ceiling_are_read_in_minutes`, next to the existing `five-and-sixty` row. Each row tests an accepting boundary that had no test:
    - `one-and-one`: `{COOLDOWN: "1", CEILING: "1"}` gives a cool-down and a ceiling of 1 minute each. This is the smallest whole number of minutes the Interface allows.
    - `ceiling-equals-cooldown`: `{COOLDOWN: "30", CEILING: "30"}` gives 30 and 30 minutes. A ceiling equal to the cool-down is accepted.

    The refused sides already had tests: `0` in `test_a_value_that_is_not_whole_minutes_of_at_least_one_is_refused`, and 30/20 in the existing ceiling-below-cool-down test.

    criterion 18: tests/domain/test_settings_provider_limit_wait.py::test_the_cooldown_and_ceiling_are_read_in_minutes[one-and-one] and [ceiling-equals-cooldown]

    Files changed: tests/domain/test_settings_provider_limit_wait.py. This story wrote that file, so no earlier story's test was changed. I created no new files.

    `make test` passed as expected, since the code already accepts these values: `test: green (36.0 s)`. Every module imported. `make lint` passed: `lint: green (0.0 s)`.

    `lint`: lint: green (0.0 s)
    `test`: test: green (37.3 s)
24. factory: started doing as self.
25. coder: Round 1. The reviewer's only finding (entry 19) was criterion 18, and it needed just its test. The tester added that test in entry 23: the `one-and-one` and `ceiling-equals-cooldown` rows in `tests/domain/test_settings_provider_limit_wait.py::test_the_cooldown_and_ceiling_are_read_in_minutes`. I changed no code and no test in this run. `make check` is green and ends with `check: green`, with coverage at 99.05 %.

    What I built is unchanged from entries 10 and 17:
    - `src/factory/application/machine.py` (`Waiter`)
    - `src/factory/adapters/clock.py` (`SleepingWaiter`, `ManualWaiter`)
    - `src/factory/application/boundaries.py` (`waiter`)
    - `src/factory/domain/provider_limits.py` (`cooldown`, `ceiling`)
    - `src/factory/domain/settings.py` (the two `..._MINUTES` variables, through the shared `_whole_number`)
    - `src/factory/application/provider_limits.py` (`CONTINUE_PROMPT`, `PatientRuns`)
    - `src/factory/application/sealed_runs.py` (`run=`)
    - `src/factory/application/stage.py` (`launch` goes through `PatientRuns`)
    - `src/factory/entry/wiring.py` (`SleepingWaiter()`)

    Main choice: `PatientRuns.run` is a single loop that keeps the joined result and the total waited so far. I rejected a recursive resume.

    Refactor pass: there was no new diff in this round, so nothing needed changing.

    Description: criterion 18 adds the accepting side of limits the Interface already states. The meaning of the task did not change, so I did not rewrite the Description.

    Noticed, not touched: only the work item's `.costs.jsonl` sidecar shows as modified, and the factory writes that file.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 33 known, 3 gone
