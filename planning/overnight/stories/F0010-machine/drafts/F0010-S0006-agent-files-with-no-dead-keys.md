# Agent files with no dead keys

## Assignment (as of log entry 1)

Refuse an agent file that holds a key the agent runtime does not apply. In print mode Claude Code ignores an agent file, so the runner builds its flags and its prompt from four keys itself; any other key reads as if it did something and does nothing. The agent files are read by the reader of F0003, which now refuses a file with an unapplied key, naming the key. The pipeline loader reads every role's agent file when it loads the pipeline definition, so the refusal happens at load, and the tick turns it into a repository stop that the health check shows, with the agent's name and the key in its detail, and does nothing else until the file is fixed. This covers SI4.1 and SI4.3 and implements the agent-file part of R30. The shipped agent files, and the proof that each of their keys has an effect (SI4.2), are the next story.

## Interface

`src/factory/domain/agent_runs.py` (extends the module)

```python
APPLIED_AGENT_KEYS: frozenset[str] = frozenset({"model", "tools", "effort", "budget_usd"})
```

`src/factory/adapters/agent_files.py`: `FrontmatterAgentDefinitionReader.read(name)` raises `AgentDefinitionInvalid` for an agent file whose front matter holds a key outside `APPLIED_AGENT_KEYS`. The error's `name` is the agent, its `key` is the first such key in the order the file lists them, and its message contains that key. Keys are compared as written (`Model` is not `model`). A file with only applied keys is read as before.

`src/factory/application/pipeline_loading.py`: `PipelineLoader.load` calls `boundaries.agent_definitions.read(role)` for every role of the definition, in the order of `roles`, after its other checks pass. An `AgentDefinitionInvalid` is not caught there.

`src/factory/application/tick.py`: where the tick loads the pipeline definition and turns a `PipelineDefinitionInvalid` into a repository stop, it also turns an `AgentDefinitionInvalid` into `RepositoryStop(scope="repository", reason="agent_definition_invalid", detail="<agent name>: <fault>", at=<now>)` through `StopService.raise_stop`, and ends there. After a load that succeeds it calls `StopService.clear_stop("agent_definition_invalid")`.

Tests: `tests/adapters/test_agent_files.py` (agent files written to `tmp_path` with the real reader), `tests/application/test_pipeline_loading.py`, `tests/application/test_tick_agent_definition.py` (the tick on the `remote`, `checkout`, `hosting` and `agent_runtime` fixtures with an agent home in `tmp_path`).

## Acceptance criteria

1. `APPLIED_AGENT_KEYS` is exactly `model`, `tools`, `effort` and `budget_usd`.
2. An agent file with only applied keys is read: its `model`, `tools`, `effort` and `budget_usd` are those of the file and its `instructions` is the file's body.
3. An agent file that adds any one of `name`, `description`, `permissionMode`, `hooks`, `background`, `disallowedTools` or `skills` is refused with `AgentDefinitionInvalid` whose `key` is that key and whose message contains it (SI4.1: a test per key the runner does not apply; the first six are v1's dead keys).
4. A key the runner has never heard of (`colour`) and a known key written in another case (`Model`) are refused in the same way.
5. A file with two unapplied keys, `hooks` listed before `description`, is refused naming `hooks`, the first in the file's order.
6. `PipelineLoader.load` raises `AgentDefinitionInvalid` (not `PipelineDefinitionInvalid`) when the agent file of the second of two roles holds an unapplied key and the first role's file is fine, so every role's file is read.
7. A tick whose pipeline definition names a role with an unapplied key leaves one stop in the health status with scope `repository` and reason `agent_definition_invalid`, whose detail contains the agent's name and the key (SI4.3).
8. That tick does nothing else: no agent run is requested and no event is dispatched, although a started story is waiting on the remote.
9. After the agent file is corrected, the next tick loads the definition, clears the stop `agent_definition_invalid` and carries on.
10. `make check` stays green.
11. docs: `docs/project-guide.md` lists the four keys an agent file may hold (`model`, `tools`, `effort`, `budget_usd`) with what each does and says that any other key is refused at load; `docs/operator-guide.md` describes the stop `agent_definition_invalid` and that the operator fixes the named file in the agent home.

## Demo

```bash
uv run python -c '
import tempfile, pathlib
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.domain.errors import AgentDefinitionInvalid
home = pathlib.Path(tempfile.mkdtemp())
(home / "agents").mkdir()
(home / "agents" / "coder.md").write_text("---\nmodel: opus\ntools: [Read]\nbudget_usd: 4\npermissionMode: auto\n---\nBody.\n")
try:
    FrontmatterAgentDefinitionReader(home).read("coder")
except AgentDefinitionInvalid as error:
    print(error.key, "|", error.name, "|", "permissionMode" in str(error))
'
```
Expect: one line, `permissionMode | coder | True`.

```bash
uv run python -c '
import tempfile, pathlib
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.domain.agent_runs import APPLIED_AGENT_KEYS
home = pathlib.Path(tempfile.mkdtemp())
(home / "agents").mkdir()
(home / "agents" / "coder.md").write_text("---\nmodel: opus\ntools: [Read, Edit]\neffort: medium\nbudget_usd: 4\n---\nNever edit tests.\n")
agent = FrontmatterAgentDefinitionReader(home).read("coder")
print(sorted(APPLIED_AGENT_KEYS), agent.model, agent.effort, agent.budget_usd)
'
```
Expect: one line, `['budget_usd', 'effort', 'model', 'tools'] opus medium 4`.

## Log (append only)

1. 2026-10-12 human: created.
