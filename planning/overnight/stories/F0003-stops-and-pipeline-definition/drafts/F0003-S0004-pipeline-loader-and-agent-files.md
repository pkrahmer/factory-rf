# Loading the pipeline definition: installed agents and a reported stop

## Assignment (as of log entry 1)

Build `PipelineLoader`, the one place that loads the pipeline definition (R30): it reads `factory/pipeline.yml` at a git ref (by default `origin/main`, never the work tree), validates it through the reader of S0003, checks that the agent of every role is installed, and turns every refusal into a reported stop (ST3, ST8.1): a `pipeline_definition_invalid` stop through S0001's `StopService` that names the fault, followed by `PipelineDefinitionInvalid`, so that the tick does nothing else; a later successful load clears the stop. To know which agents are installed (ST8.3, the second half) the story also builds the agent definition reader, `FrontmatterAgentDefinitionReader`, with the `AgentDefinitionReader` protocol and the agent definition errors; F0005 will use its `read` to compose every task. Refusing keys that the agent runtime does not apply is F0010-S0006; keys beyond `model`, `tools`, `effort` and `budget_usd` are not interpreted here. Covers ST8.1 (a missing key without default is a reported stop at load, one with a default takes it), the installed-agent half of ST8.3, and R30; keeps kept things 7 and 12. The refusals that look across keys (ST8.2, the write-path half of ST8.3, ST8.4, ST8.5, GH1.4) are S0005, which needs nothing more from the loader.

## Interface

`src/factory/domain/errors.py` (adds to the hierarchy)

```python
class AgentDefinitionError(FactoryError):
    name: str
    fault: str
    def __init__(self, name: str, fault: str) -> None: ...

class AgentDefinitionMissing(AgentDefinitionError): ...

class AgentDefinitionInvalid(AgentDefinitionError):
    key: str
    def __init__(self, name: str, fault: str, key: str) -> None: ...
```

`src/factory/application/agent_runtime.py` (adds to F0001-S0007's module)

```python
class AgentDefinitionReader(ABC):
    @abstractmethod
    def names(self) -> list[str]: ...                 # installed agents, sorted; AgentDefinitionError
    @abstractmethod
    def read(self, name: str) -> AgentDefinition: ... # AgentDefinitionMissing; AgentDefinitionInvalid
```

`src/factory/adapters/agent_files.py`

```python
class FrontmatterAgentDefinitionReader:
    def __init__(self, agent_home: Path) -> None: ...     # the agent files are <agent_home>/agents/<name>.md
    def names(self) -> list[str]: ...
    def read(self, name: str) -> AgentDefinition: ...
```

`src/factory/application/pipeline_loading.py`

```python
class PipelineLoader:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def load(self, ref: str = "origin/main") -> PipelineDefinition: ...
        # PipelineDefinitionInvalid (after its stop is raised); GitError; OSError from the stop's writes
```

`src/factory/application/boundaries.py` (adds the field `agent_definitions: AgentDefinitionReader` to `Boundaries`; the `boundaries` fixture gets a `FrontmatterAgentDefinitionReader` on a directory of the test's own).

An agent file, as `read` understands it (the text of `<agent home>/agents/coder.md`, written here as a Python string; the YAML front matter sits between the two lines of three hyphens):

```python
CODER_FILE = "---\nmodel: sonnet\ntools: [Read, Write]\neffort: low\nbudget_usd: 1.5\n---\nThe agent's instructions.\n"
```

Rules for `FrontmatterAgentDefinitionReader`:

- `names()` returns the sorted stems of the regular files with the suffix `.md` that lie directly in `<agent_home>/agents/`; other files and subdirectories do not count. When `<agent_home>/agents` is not a directory it raises `AgentDefinitionError(name="", fault="no agents directory at <path>")`.
- `read(name)` returns `AgentDefinition(name=name, model, tools, effort, budget_usd, instructions)` from `<agent_home>/agents/<name>.md`. The front matter is read with python-frontmatter; `instructions` is the body without surrounding whitespace; `budget_usd` is a `Decimal` built from the number written (`1.5` gives `Decimal("1.5")`); `effort` is optional and `None` when left out. Other front matter keys are not interpreted.
- A file that does not exist is `AgentDefinitionMissing(name, fault="no agent file <path>")`.
- A missing `model`, `tools` or `budget_usd` is `AgentDefinitionInvalid` with `key` set to that key and `fault` `missing key <key>`. A `budget_usd` that is not a number greater than 0 is `AgentDefinitionInvalid` with `key="budget_usd"` and `fault` `budget_usd must be greater than 0`.

Rules for `PipelineLoader.load(ref)`:

- It reads `PIPELINE_DEFINITION_FILE` at `ref` with `boundaries.git.show_file`, parses it with `boundaries.pipeline_reader`, and then checks the agents with `boundaries.agent_definitions`. It never reads a file of the work tree.
- A refusal has a fault: the file's absence is `factory/pipeline.yml is missing at <ref>`; the reader's `PipelineDefinitionInvalid` carries its own fault; an `AgentDefinitionError` from `names()` is `agent home unavailable: <its fault>`; each role of `roles` whose name is not among `names()` is `role <role>: agent is not installed`, in the order of `roles`, all joined by `; `. The agents are checked only when the text itself is valid.
- For each refusal it calls `StopService.raise_stop` with `RepositoryStop(scope="repository", reason="pipeline_definition_invalid", detail=<the fault>, at=boundaries.clock.now())` and then raises `PipelineDefinitionInvalid(<the fault>)`. The stop goes to the health status and the factory log only.
- A load that succeeds calls `StopService.clear_stop("pipeline_definition_invalid")` and returns the definition. Stops of other reasons are untouched.
- A `GitError` is not a fault of the definition: it propagates and raises no stop.

Tests: `tests/adapters/test_agent_files.py`, `tests/application/test_pipeline_loading.py`. The loader tests use the real `GitCli` on the fixtures `remote`, `checkout` and `human` (`human.push_file(branch, path, text)` for other versions of the file), a fixture `boundaries` whose `agent_definitions` reads a directory in `tmp_path`, and `ManualClock` through the fixture `clock`.

## Acceptance criteria

1. `PipelineLoader.load()` returns the definition that `factory/pipeline.yml` holds on `origin/main`, also when the file in the work tree of the checkout has been changed (for example to another `attempts_cap`); the work tree's file is not read.
2. `load("origin/<branch>")` returns the definition of the file on that branch, which a test pushed with another `attempts_cap`.
3. A definition without `contract` makes `load` raise `PipelineDefinitionInvalid` whose `fault` is `missing key contract` (ST8.1).
4. In that case exactly one stop is raised and `boundaries.health.read().stops` holds it: `scope` `repository`, `reason` `pipeline_definition_invalid`, `detail` equal to the fault, and `at` equal to `clock.now()`; one line `<stamp> stop repository pipeline_definition_invalid: missing key contract` was written to the factory log.
5. A refusal reaches only the health status and the factory log: `hosting.pull_requests()` is empty and nothing was posted.
6. The example definition of S0003, which writes no `lease_duration` for any role and no `crash_cap`, loads with `lease_duration` 60 for every role and `crash_cap` 2, and raises no stop (ST8.1: a missing key that has a default takes it).
7. When the file does not exist at the ref, `load` raises `PipelineDefinitionInvalid` with the fault `factory/pipeline.yml is missing at <ref>`, and raises the stop with that detail.
8. A successful `load` after a refused one removes the `pipeline_definition_invalid` stop from the health status and writes the line `<stamp> stop cleared pipeline_definition_invalid`; a stop of another reason (`fetch_failed`) that was in the status stays.
9. A `GitError` from reading the file (a ref that does not exist) propagates from `load`, and no stop is raised.
10. When a role of `roles` has no installed agent, `load` raises `PipelineDefinitionInvalid` with the fault `role <role>: agent is not installed`, raises the stop with that detail, and names every missing role (two missing roles give two faults joined by `; ` in the order of `roles`) (ST8.3).
11. When the agent of every role is installed, `load` returns the definition and raises no stop; agents installed that no role names do not matter.
12. When `<agent_home>/agents` does not exist, `load` raises `PipelineDefinitionInvalid` whose fault starts with `agent home unavailable: `, and raises the stop with that detail.
13. `FrontmatterAgentDefinitionReader.names()` returns the sorted stems of the `.md` files directly in `<agent_home>/agents/`, and leaves out a file with another suffix and a subdirectory.
14. `names()` raises `AgentDefinitionError` with `name == ""` and a `fault` that starts with `no agents directory at ` when `<agent_home>/agents` does not exist.
15. `read("coder")` of the agent file `CODER_FILE` in the Interface returns an `AgentDefinition` with `name == "coder"`, `model == "sonnet"`, `tools == ["Read", "Write"]`, `effort == "low"`, `budget_usd == Decimal("1.5")` and `instructions == "The agent's instructions."`.
16. `read` of a file without an `effort` key returns `effort is None`.
17. `read("nobody")` raises `AgentDefinitionMissing` with `name == "nobody"`.
18. `read` of a file that leaves out `model`, `tools` or `budget_usd` raises `AgentDefinitionInvalid` whose `key` is the missing key and whose `fault` is `missing key <key>` (one test, three cases).
19. `read` of a file with `budget_usd` 0, -1 or `high` raises `AgentDefinitionInvalid` with `key == "budget_usd"`; `budget_usd` 0.01 is accepted.
20. `AgentDefinitionMissing` and `AgentDefinitionInvalid` are subclasses of `AgentDefinitionError`, which is a `FactoryError`; each carries its `name` and `fault`, and `AgentDefinitionInvalid` its `key`.
21. `make check` stays green.
22. docs: `docs/operator-guide.md` explains the stop `pipeline_definition_invalid` (the tick does nothing else until the definition on `origin/main` is fixed, the stop clears itself at the next successful load), lists the faults the loader reports (the file missing, a schema fault, an agent that is not installed, the agent home unavailable) and says where agent files live (`<agent home>/agents/<name>.md`, keys `model`, `tools`, `effort`, `budget_usd`); `docs/project-guide.md` states that every role of the pipeline definition needs an agent file of the same name.

## Demo

```bash
uv run python -c "
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import ManualClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.application.boundaries import Boundaries
from factory.application.pipeline_loading import PipelineLoader
from factory.domain.errors import PipelineDefinitionInvalid
TEXT = '''contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
  tester: {write_paths: ['tests/*']}
stages:
  tests: {role: tester, next: [doing]}
  doing: {role: coder, next: [done]}
  done: {}
'''
class StubGit:
    def show_file(self, ref, path):
        return TEXT
root = Path(tempfile.mkdtemp())
agents = root / 'home' / 'agents'
agents.mkdir(parents=True)
(agents / 'coder.md').write_text('---\nmodel: sonnet\ntools: [Read, Write]\nbudget_usd: 4\n---\nWrite the code.\n')
clock = ManualClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))
health = JsonHealthStatusFile(root / 'state' / 'health.json')
parts = dict.fromkeys(['hosting', 'agent_runtime', 'project_commands', 'work_item_reader', 'work_item_writer', 'cost_reader', 'cost_writer'])
boundaries = Boundaries(**parts, git=StubGit(), clock=clock, log=TimestampedFactoryLog(root / 'state' / 'factory.log', clock), health=health, pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(root / 'home'), checkout=root)
loader = PipelineLoader(boundaries)
try:
    loader.load()
except PipelineDefinitionInvalid as error:
    print(error.fault)
print([stop.reason for stop in health.read().stops])
(agents / 'tester.md').write_text('---\nmodel: sonnet\ntools: [Read, Write]\nbudget_usd: 2\n---\nWrite the tests.\n')
print(loader.load().first_stage(), health.read().healthy)
"
```
Expect: five lines of output: `<stamp> stop repository pipeline_definition_invalid: role tester: agent is not installed` (the stamp has the form `YYYY-MM-DDTHH:MM:SSZ` and starts with `2026-10-12T`), then `role tester: agent is not installed`, then `['pipeline_definition_invalid']`, then `<stamp> stop cleared pipeline_definition_invalid`, then `tests True`.

## Log (append only)

1. 2026-10-12 human: created.
