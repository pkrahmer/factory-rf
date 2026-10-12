# The agent-runtime interface, its DTOs and the fake

## Assignment (as of log entry 1)

Define everything the factory knows about running an agent, with factory-shaped DTOs (R7): the agent definition, the request (agent, prompt, allowed decisions, `time_limit`, working directory, the run's whole environment, guard settings), the result (end reason, decision and entry, duration, turns, tokens, cost, permission denials, with cost and tokens `None` when unknown, never 0), and the `AgentRuntime` protocol with `run` and `version`. A run that dies, reaches its `time_limit` or exhausts its budget is a result with an end reason, not an error: for the caller it is a stall. Build the fake runtime that every stage test uses: it applies a scripted run to the working directory, records every request, and can reach the `agent-run` kill point after the agent's writes. Covers R12 (the interface; the `claude -p` implementation follows in S0008), R6 and R7; keeps kept thing 20 (every agent run's duration, turns, tokens and cost are reported, and unknown is unknown) and kept thing 10 (`question` is always an allowed decision). This story also adds `Name` to `factory.domain.identifiers`, which S0002 created with `WorkItemId` only.

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

Tests: `tests/domain/test_agent_runs.py`, `tests/domain/test_name.py`, `tests/domain/test_errors.py` (extended), `tests/adapters/test_fake_agent_runtime.py`; `tests/conftest.py` gains the fixture `agent_runtime`, a `FakeAgentRuntime(kill_points)`. A test module assigns `FakeAgentRuntime` to a variable annotated `AgentRuntime`, so that mypy checks the fit.

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
10. `TokenCounts` rejects `input=-1`, accepts `input=0`, and has `cache_read == 0` and `cache_creation == 0` by default.
11. An `AgentRunResult` with `end_reason="completed"` is rejected without a `decision` and rejected without an `entry`, and accepted with both.
12. An `AgentRunResult` with any other end reason is rejected when it has a `decision` or an `entry`, for each of `no_result`, `time_limit`, `budget` and `died`, and accepted without them.
13. An `AgentRunResult` without measures has `turns`, `tokens` and `cost_usd` equal to `None`, not 0, and `ok` is true for `completed` and false for each of the other four end reasons.
14. Each of `AgentDefinition`, `GuardSettings`, `AgentRunRequest`, `TokenCounts`, `PermissionDenial`, `AgentRunResult` and `ScriptedRun` rejects an unknown keyword argument and rejects assignment to a field.
15. With two scripted runs queued, two calls of `run` return the two results in the order queued, and `requests()` holds the two requests in the order received.
16. A scripted run with `writes={"tests/test_a.py": "x = 1\n"}` and `deletes=["old.txt"]` creates `tests/test_a.py` (and the folder) under the working directory with that text, replaces it when it exists, and removes `old.txt`; a delete of a file that does not exist raises nothing.
17. A scripted run that writes `../escape.txt`, or an absolute path, makes `run` raise `AgentRuntimeError`, and nothing is written or deleted, not even by the valid entries of the same run.
18. `run` with nothing queued raises `AgentRuntimeError`, and the request is in `requests()`.
19. With a scripted run whose `kill` is true and `KillPoint.AGENT_RUN` armed, `run` raises `InjectedKill` after the writes: the written file is on disk.
20. With `kill` true and the point not armed, `run` returns the scripted result and `reached(KillPoint.AGENT_RUN)` is 1; with `kill` false the point is not reached (`reached` is 0) even when armed, and the result is returned.
21. `FakeAgentRuntime().version()` is `"fake"`, and `FakeAgentRuntime(version="2.1.289").version()` is `"2.1.289"`.
22. `AgentRuntimeError("boom")` has the message `agent runtime failed: boom`, carries `detail == "boom"` and is a subclass of `BoundaryError`.
23. `FakeAgentRuntime` is not a subclass of `AgentRuntime`, and a test module assigns a `FakeAgentRuntime` to a variable annotated `AgentRuntime`, so that `make check` (mypy) proves the structural fit.
24. make check stays green.
25. docs: `docs/project-guide.md` describes the agent-runtime interface (request, result, end reasons, unknown measures as `None`, `question` always allowed) and the fake for tests; `docs/decisions.md` records why a dead, timed-out or over-budget run is a result and not an error (WE6.3).

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
