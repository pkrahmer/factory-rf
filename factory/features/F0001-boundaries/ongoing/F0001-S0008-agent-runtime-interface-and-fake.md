---
stage: doing
pr: 8
blocked: asked
comments_seen: 1
round: 0
attempts: 0
---
# The agent-runtime interface, its DTOs and the fake

## Assignment (as of log entry 1)

Define everything the factory knows about running an agent, with factory-shaped DTOs (R7): the agent definition, the request (agent, prompt, allowed decisions, `time_limit`, working directory, the run's whole environment, guard settings), the result (end reason, decision and entry, duration, turns, tokens, cost, permission denials, with cost and tokens `None` when unknown, never 0), and the `AgentRuntime` protocol with `run` and `version`. A run that dies, reaches its `time_limit` or exhausts its budget is a result with an end reason, not an error: for the caller it is a stall. Build the fake runtime that every stage test uses: it applies a scripted run to the working directory, records every request, and can reach the `agent-run` kill point after the agent's writes. Covers R12 (the interface; the `claude -p` implementation follows in S0009 and S0010), R6 and R7; keeps kept thing 20 (every agent run's duration, turns, tokens and cost are reported, and unknown is unknown) and kept thing 10 (`question` is always an allowed decision). This story also adds `Name` to `factory.domain.identifiers`, which S0002 created with `WorkItemId` only.

## Interface

`src/factory/domain/identifiers.py` (adds one name)

```python
Name = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]
```

`src/factory/domain/errors.py` (adds one type)

```python
class AgentRuntimeError(BoundaryError):
    detail: str
    def __init__(self, detail: str) -> None: ...
```

`src/factory/domain/agent_runs.py`

```python
QUESTION = "question"
EndReason = Literal["completed", "no_result", "time_limit", "budget", "died"]

class AgentDefinition(BaseModel):
    name: Name
    model: str
    tools: list[str]
    effort: str | None = None
    budget_usd: Decimal
    instructions: str

class GuardSettings(BaseModel):
    root: Path
    write_paths: list[str]
    protected_paths: list[str]

class AgentRunRequest(BaseModel):
    agent: AgentDefinition
    prompt: str
    allowed_decisions: list[str]
    time_limit: timedelta
    working_directory: Path
    environment: dict[str, str] = {}
    guard: GuardSettings | None = None
    os_user: str | None = None

class TokenCounts(BaseModel):
    input: NonNegativeInt
    output: NonNegativeInt
    cache_read: NonNegativeInt = 0
    cache_creation: NonNegativeInt = 0

class PermissionDenial(BaseModel):
    tool: str
    detail: str

class AgentRunResult(BaseModel):
    end_reason: EndReason
    decision: str | None = None
    entry: str | None = None
    duration: timedelta
    turns: NonNegativeInt | None = None
    tokens: TokenCounts | None = None
    cost_usd: Decimal | None = None
    permission_denials: list[PermissionDenial] = []

    @property
    def ok(self) -> bool: ...
```

`src/factory/application/agent_runtime.py`

```python
class AgentRuntime(Protocol):
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
    def version(self) -> str: ...
```

`src/factory/adapters/fake_agent_runtime.py`

```python
class ScriptedRun(BaseModel):
    writes: dict[str, str] = {}
    deletes: list[str] = []
    result: AgentRunResult
    kill: bool = False

class FakeAgentRuntime:      # satisfies AgentRuntime structurally, no inheritance
    def __init__(self, kill_points: KillPoints | None = None, version: str = "fake") -> None: ...
    def queue(self, run: ScriptedRun) -> None: ...
    def requests(self) -> list[AgentRunRequest]: ...
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
    def version(self) -> str: ...
```

The rules, each with a criterion below:

- Every model is frozen and forbids unknown keys.
- `AgentDefinition.budget_usd` is greater than 0. `AgentRunRequest.allowed_decisions` contains `QUESTION` (the validation error names `question`) and has no repeats; `time_limit` is greater than 0; `working_directory` is an absolute path; `GuardSettings.root` is an absolute path.
- `AgentRunResult` has a `decision` and an `entry` exactly when `end_reason` is `"completed"`; `ok` is true exactly then. A measure that was not reported is `None`, never 0. `TokenCounts` has no negative count.
- `FakeAgentRuntime.run` records the request first (so `requests()` holds every request received, in order, also one that raised), then takes the oldest queued `ScriptedRun`; with nothing queued it raises `AgentRuntimeError`. It then writes each `writes` entry (path relative to `request.working_directory`, parent directories created, UTF-8 text, an existing file replaced), removes each `deletes` entry (a path that does not exist is ignored), and, when `kill` is true and the fake has kill points, reaches `KillPoint.AGENT_RUN`; then it returns `result` as scripted. A path that is absolute or leaves the working directory (a `..` segment) raises `AgentRuntimeError` before anything is written or deleted.
- `version()` returns the string given at construction.
- `AgentRuntimeError` has the message `agent runtime failed: <detail>`.

Tests: `tests/domain/test_agent_runs.py`, `tests/domain/test_name.py`, `tests/domain/test_errors.py` (extended: it gains new tests only, no existing test is changed), `tests/adapters/test_fake_agent_runtime.py`; `tests/conftest.py` gains the fixture `agent_runtime`, a `FakeAgentRuntime(kill_points)` (an addition; no existing fixture is changed). A test module assigns `FakeAgentRuntime` to a variable annotated `AgentRuntime`, so that mypy checks the fit.

## Acceptance criteria

1. `QUESTION` is `"question"`, and `EndReason` has exactly the five values `completed`, `no_result`, `time_limit`, `budget` and `died`.
2. `Name` accepts `coder` and `smoke-tester` and rejects `Coder`, `1x`, `a b` and the empty string.
3. `AgentDefinition` accepts a `budget_usd` of `Decimal("0.01")` and rejects `Decimal("0")` and `Decimal("-1")`; it rejects the name `Coder`.
4. A minimal `AgentRunRequest` is accepted and has `environment == {}`, `guard` `None` and `os_user` `None`; the `environment` of two requests is not the same object.
5. `allowed_decisions` without `question` is rejected, for `[]` and for `["doing"]`, with an error that names `question`; `["doing", "question"]` is accepted.
6. `allowed_decisions` with a repeat, such as `["doing", "doing", "question"]`, is rejected.
7. `time_limit` of `timedelta(0)` is rejected and `timedelta(seconds=1)` is accepted.
8. A relative `working_directory` is rejected and an absolute one accepted.
9. `GuardSettings` rejects a relative `root`, accepts an absolute one, and keeps `write_paths` and `protected_paths` as given.
10. `TokenCounts` rejects `-1` for each of `input`, `output`, `cache_read` and `cache_creation`, accepts `0` for each, and has `cache_read == 0` and `cache_creation == 0` by default.
11. An `AgentRunResult` with `end_reason="completed"` is rejected without a `decision` and rejected without an `entry`, and accepted with both.
12. An `AgentRunResult` with any other end reason is rejected when it has a `decision` or an `entry`, for each of `no_result`, `time_limit`, `budget` and `died`, and accepted without them.
13. An `AgentRunResult` without measures has `turns`, `tokens` and `cost_usd` equal to `None`, not 0, and `ok` is true for `completed` and false for each of the other four end reasons.
14. Each of `AgentDefinition`, `GuardSettings`, `AgentRunRequest`, `TokenCounts`, `PermissionDenial`, `AgentRunResult` and `ScriptedRun` rejects an unknown keyword argument and rejects assignment to a field.
15. With two scripted runs queued, two calls of `run` return the two results in the order queued, and `requests()` holds the two requests in the order received.
16. A scripted run with `writes={"tests/test_a.py": "x = 1\n"}` and `deletes=["old.txt"]` creates `tests/test_a.py` (and the folder) under the working directory with that text, replaces it when it exists, and removes `old.txt`; a delete of a file that does not exist raises nothing.
17. A scripted run that writes `../escape.txt` or an absolute path, and a scripted run that deletes `../x` or an absolute path, each make `run` raise `AgentRuntimeError`, and nothing is written or deleted, not even by the valid entries of the same run (a file that exists under the working directory is still there).
18. `run` with nothing queued raises `AgentRuntimeError`, and the request is in `requests()`.
19. With a scripted run whose `kill` is true and `KillPoint.AGENT_RUN` armed, `run` raises `InjectedKill` after the writes: the written file is on disk.
20. With `kill` true and the point not armed, `run` returns the scripted result and `reached(KillPoint.AGENT_RUN)` is 1; with `kill` false the point is not reached (`reached` is 0) even when armed, and the result is returned.
21. A `FakeAgentRuntime()` built without kill points returns the scripted result for a run with `kill` true, and the writes are on disk.
22. `FakeAgentRuntime().version()` is `"fake"`, and `FakeAgentRuntime(version="2.1.289").version()` is `"2.1.289"`.
23. `AgentRuntimeError("boom")` has the message `agent runtime failed: boom`, carries `detail == "boom"` and is a subclass of `BoundaryError`.
24. `FakeAgentRuntime` is not a subclass of `AgentRuntime`, and a test module assigns a `FakeAgentRuntime` to a variable annotated `AgentRuntime`, so that `make check` (mypy) proves the structural fit.
25. make check stays green.
26. docs: `docs/project-guide.md` describes the agent-runtime interface (request, result, end reasons, unknown measures as `None`, `question` always allowed) and the fake for tests; `docs/decisions.md` records why a dead, timed-out or over-budget run is a result and not an error (WE6.3).

## Demo

```bash
uv run python -c "
import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, AgentRunResult
root = Path(tempfile.mkdtemp())
agent = AgentDefinition(name='tester', model='sonnet', tools=['Read'], budget_usd=Decimal('2'), instructions='Write tests.')
request = AgentRunRequest(agent=agent, prompt='Stage: tests', allowed_decisions=['doing', 'question'], time_limit=timedelta(minutes=40), working_directory=root)
runtime = FakeAgentRuntime()
result = AgentRunResult(end_reason='completed', decision='doing', entry='Wrote 3 tests.', duration=timedelta(seconds=5))
runtime.queue(ScriptedRun(writes={'tests/test_a.py': 'x = 1\n'}, result=result))
outcome = runtime.run(request)
print(outcome.ok, outcome.decision, (root / 'tests' / 'test_a.py').read_text().strip(), len(runtime.requests()))
"
```
Expect: one line, `True doing x = 1 1`: the scripted write is on disk, the decision comes back, one request was recorded.

```bash
uv run python -c "
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from pydantic import ValidationError
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
agent = AgentDefinition(name='coder', model='sonnet', tools=[], budget_usd=Decimal('3'), instructions='Code.')
try:
    AgentRunRequest(agent=agent, prompt='p', allowed_decisions=['review'], time_limit=timedelta(minutes=5), working_directory=Path('/tmp'))
except ValidationError as error:
    print('rejected:', 'question' in str(error))
"
```
Expect: one line, `rejected: True`: a request whose allowed decisions lack `question` is refused.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules (`domain/identifiers.py`, `domain/errors.py`, `domain/agent_runs.py`, `application/agent_runtime.py`, `adapters/fake_agent_runtime.py`) with full signatures. The layers are right (domain DTOs, application protocol, adapter fake). The tests, fixture and the structural-typing check are named.
   - Criteria: 26 in total, each testable by one function. Every rule of the Interface has a criterion for both sides: Name (2), budget_usd > 0 (3), question required and no repeats (5, 6), time_limit > 0 (7), absolute working_directory and root (8, 9), non-negative tokens (10), decision and entry exactly when completed (11, 12), unknown measures are None and `ok` (13), frozen and forbids extra keys (14). For the fake: order and recording (15), writes and deletes (16), escape paths with nothing written (17), empty queue with the request recorded (18), kill armed, unarmed and not requested (19-21), version (22), the error message (23).
   - Demo: both commands are runnable with the imports given. Each `Expect:` line is checkable (`True doing x = 1 1` and `rejected: True`).
   - Architecture: matches CLAUDE.md (R5 to R7, R12), with no concrete tool in the application layer, no `dict[str, Any]` across a boundary, and the fake as a structural fit.
   - Scope: inside F0001's scope (the agent-runtime interface, its DTOs and the fake). The `claude -p` implementation and the guard hook are left to S0009, S0010 and F0004.
3. tester: Wrote red tests for every criterion. Criteria 25 and 26 are left to make check and the documenter.
   - criterion 1: tests/domain/test_agent_runs.py::test_question_and_the_five_end_reasons
   - criterion 2: tests/domain/test_name.py::test_name_accepts_lower_case_hyphenated_words_only (parametrized: coder, smoke-tester accepted; Coder, 1x, "a b", "" rejected)
   - criterion 3: tests/domain/test_agent_runs.py::test_agent_budget_must_be_positive (0.01 / 0 / -1) and ::test_agent_name_must_be_a_name
   - criterion 4: tests/domain/test_agent_runs.py::test_minimal_request_has_empty_defaults_not_shared
   - criterion 5: tests/domain/test_agent_runs.py::test_allowed_decisions_without_question_are_rejected ([] and ["doing"], error text contains "question") and ::test_allowed_decisions_with_question_are_accepted
   - criterion 6: tests/domain/test_agent_runs.py::test_allowed_decisions_with_a_repeat_are_rejected
   - criterion 7: tests/domain/test_agent_runs.py::test_time_limit_must_be_positive
   - criterion 8: tests/domain/test_agent_runs.py::test_working_directory_must_be_absolute
   - criterion 9: tests/domain/test_agent_runs.py::test_guard_root_must_be_absolute_and_paths_are_kept
   - criterion 10: tests/domain/test_agent_runs.py::test_token_counts_reject_negative_counts (each field, 0 accepted, -1 rejected) and ::test_token_counts_default_cache_counts_to_zero
   - criterion 11: tests/domain/test_agent_runs.py::test_completed_result_needs_decision_and_entry
   - criterion 12: tests/domain/test_agent_runs.py::test_other_end_reasons_carry_no_decision_or_entry (one case per reason)
   - criterion 13: tests/domain/test_agent_runs.py::test_unreported_measures_are_none_and_ok_only_when_completed (all five reasons)
   - criterion 14: tests/domain/test_agent_runs.py::test_models_forbid_unknown_keys_and_are_frozen (the six domain models) and tests/adapters/test_fake_agent_runtime.py::test_scripted_run_forbids_unknown_keys_and_is_frozen. ScriptedRun is tested in the adapters folder so that the domain tests do not import an adapter.
   - criterion 15: tests/adapters/test_fake_agent_runtime.py::test_runs_return_queued_results_in_order_and_record_requests
   - criterion 16: tests/adapters/test_fake_agent_runtime.py::test_writes_create_and_replace_files_and_deletes_remove_them (the second run replaces the file and deletes the already-missing old.txt)
   - criterion 17: tests/adapters/test_fake_agent_runtime.py::test_paths_outside_the_working_directory_raise_before_any_change (four cases: write ../escape.txt, write an absolute path, delete ../x, delete an absolute path; each also has a valid write and a valid delete, which must not take effect)
   - criterion 18: tests/adapters/test_fake_agent_runtime.py::test_run_with_nothing_queued_raises_and_records_the_request
   - criterion 19: tests/adapters/test_fake_agent_runtime.py::test_armed_agent_run_kills_after_the_writes
   - criterion 20: tests/adapters/test_fake_agent_runtime.py::test_agent_run_point_is_reached_only_when_the_run_asks_for_it
   - criterion 21: tests/adapters/test_fake_agent_runtime.py::test_runtime_without_kill_points_ignores_kill
   - criterion 22: tests/adapters/test_fake_agent_runtime.py::test_version_is_the_one_given_at_construction
   - criterion 23: tests/domain/test_errors.py::test_agent_runtime_error_names_its_detail (new test; the only change to existing code is the added import)
   - criterion 24: tests/adapters/test_fake_agent_runtime.py::test_fake_fits_the_agent_runtime_protocol_without_inheriting (assigns to a variable annotated `AgentRuntime` and checks that `AgentRuntime` is not in the MRO)

   Files created: tests/domain/test_agent_runs.py, tests/domain/test_name.py, tests/adapters/test_fake_agent_runtime.py. Files extended: tests/domain/test_errors.py (one import and one new test) and tests/conftest.py (the `agent_runtime` fixture, `FakeAgentRuntime(kill_points)`, plus its import).

   Test run: red, as intended. Loading conftest fails with `ModuleNotFoundError: No module named 'factory.adapters.fake_agent_runtime'`, so the whole suite stays down until that module exists. This is expected because the ticket puts the fixture in conftest. The other modules that are not there yet are factory.domain.agent_runs, factory.application.agent_runtime, `Name` in factory.domain.identifiers and `AgentRuntimeError` in factory.domain.errors.

   make lint: green. Type check skipped in this stage, as the stage skill says.

   `make lint`: lint: green
   `make test`: E   ModuleNotFoundError: No module named 'factory.adapters.fake_agent_runtime'
4. coder: I built the whole interface, but `make check` fails on one line in a test, and I am not allowed to change tests.

   What I built (commit "feat(agent-runtime): DTOs, protocol and fake runtime"):
   - `Name` added to `src/factory/domain/identifiers.py`.
   - `AgentRuntimeError` added to `src/factory/domain/errors.py`.
   - `src/factory/domain/agent_runs.py`: the DTOs, all frozen and refusing unknown keys. It has an `AbsolutePath` type for `working_directory` and `GuardSettings.root`. Field validators require `question` in the allowed decisions, forbid repeats and require a positive `time_limit`. A model validator links `decision` and `entry` to `completed`.
   - `src/factory/application/agent_runtime.py`: the `AgentRuntime` Protocol.
   - `src/factory/adapters/fake_agent_runtime.py`: `ScriptedRun` and `FakeAgentRuntime`. It records the request first. It checks every write and delete path before touching the disk, so a bad path changes nothing. It reaches `KillPoint.AGENT_RUN` after the writes, and only when the run asks for a kill and the fake has kill points.

   Checks: `make lint`, `make test` (all green, coverage 100 %), `make layers` and `make sast` pass. `make types` fails:

   `tests/adapters/test_fake_agent_runtime.py:163: error: Unexpected keyword argument "unknown" for "ScriptedRun"  [call-arg]`

   The test calls `ScriptedRun(**dict(run), unknown=1)` directly. The pydantic mypy plugin gives `ScriptedRun` a typed `__init__`, so mypy rejects the unknown keyword at type-check time. The domain version of this test does not hit the error, because it calls through `model = type(instance)`, which mypy types as `type[BaseModel]`. `tests/domain/test_checks.py:71` already handles the same situation with `# type: ignore[call-arg]`.

   Options:
   (a) The tester adds `  # type: ignore[call-arg]` to line 163 of `tests/adapters/test_fake_agent_runtime.py`, as `test_checks.py` does. Alternatively, it can call through `model: type[BaseModel] = ScriptedRun`, as the domain test does. No code change is needed.
   (b) I give `ScriptedRun` a hand-written `__init__(self, **data: object)` so that the plugin does not generate the typed one. That would make every typed construction of `ScriptedRun` untyped just to suit one test, so I reject it.

   I recommend (a). Once you answer, I will end with `tests` and name that one-line change. I skipped the refactor step because `make check` is not green yet. I will do it on the next run.
