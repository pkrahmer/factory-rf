# Agent files with no dead keys

## Assignment (as of log entry 1)

Refuse an agent file that holds a key the agent runtime does not apply. In print mode Claude Code ignores an agent file, so the runner builds its flags and its prompt from four keys itself; any other key reads as if it did something and does nothing. The agent files are read by the reader of F0003, which now refuses a file with an unapplied key, naming the key. The pipeline loader reads every role's agent file when it loads the pipeline definition, so the refusal happens at load. The loader is the one place that raises and clears the definition's stop (F0003-S0006, `docs/decisions.md`: no caller raises it), so it also raises the stop `agent_definition_invalid` for the refusal and clears it after a good load, both only for a load of `origin/main`; the tick turns the error into the end of the tick, the health check shows the stop, with the agent's name and the key in its detail, and nothing else happens until the file is fixed. `factory-watch` reports the same refusal without touching a stop. This covers SI4.1 and SI4.3 and implements the agent-file part of R30. F0003's decision 14 left the other keys ignored "until F0010 decides which keys the runtime applies"; SI4.1 decides it, and so this story replaces one test that F0003-S0005 wrote, `tests/adapters/test_agent_files.py::test_a_key_the_reader_does_not_interpret_is_left_aside`, which asserts that `colour: red` is ignored: the tester deletes that test function in the tests stage (the coder's write paths hold no test), and criterion 4 below (the same file, now refused with the key `colour`) is its replacement. The human's word for this change is in `FEATURE.md`, decision 28, as `CLAUDE.md` requires. The shipped agent files, and the proof that each of their keys has an effect (SI4.2), are a later story.

## Interface

`src/factory/domain/agent_runs.py` (extends the module)

```python
APPLIED_AGENT_KEYS: frozenset[str] = frozenset({"model", "tools", "effort", "budget_usd"})
KEY_NOT_APPLIED = "key not applied by the agent runtime"
```

`src/factory/adapters/agent_files.py`: `FrontmatterAgentDefinitionReader.read(name)` raises `AgentDefinitionInvalid` for an agent file whose front matter holds a key outside `APPLIED_AGENT_KEYS`. The error's `name` is the agent, its `key` is the first such key in the order the file lists them, its `fault` is `key not applied by the agent runtime: <key>` and its message contains that key. Keys are compared as written (`Model` is not `model`). The check comes before the validation of the applied keys: a file with an unapplied key and a missing or invalid applied key is refused for the unapplied key. A file with only applied keys is read as before. The reader's private tuple of interpreted keys is replaced by `APPLIED_AGENT_KEYS`.

`src/factory/application/pipeline_loading.py` (the loader of F0003-S0006):

- `PipelineLoader.load` calls `boundaries.agent_definitions.read(role)` for every role of the definition, in the order of `roles`, after its other checks pass; an `AgentDefinitionInvalid` it meets is raised to the caller.
- At `PIPELINE_REF` it first raises `RepositoryStop(scope="repository", reason="agent_definition_invalid", detail="<agent name>: <fault>", at=<now>)` through `StopService.raise_stop`, and a load that succeeds clears the stop `agent_definition_invalid`, exactly as it does for `pipeline_definition_invalid`. A definition that passes its own checks clears `pipeline_definition_invalid` at `PIPELINE_REF` before the agent files are read, so a refused agent file leaves only the stop `agent_definition_invalid`. A load at any other ref raises the same error and touches no stop.

`src/factory/application/tick.py`: `Tick._load` turns an `AgentDefinitionInvalid` into the end of the tick, `TickOutcome(stopped="agent_definition_invalid")`, as it does for `PipelineDefinitionInvalid`. The tick raises and clears no stop for it.

`src/factory/entry/watch.py` (F0006-S0006's `run_watch`): an `AgentDefinitionInvalid` from the load is written as `factory-watch: <the error's message>` and a newline to `err`, nothing goes to `out`, and `run_watch` returns 1; it touches no stop.

Tests: `tests/adapters/test_agent_file_keys.py` (agent files written to `tmp_path` with the real reader; a file of its own), `tests/application/test_pipeline_loading_agents.py`, `tests/application/test_tick_agent_definition.py` (the tick on the `remote`, `checkout`, `hosting` and `agent_runtime` fixtures with an agent home in `tmp_path`, `handler_factory(boundaries, "factory-1", <an environment with a PATH and a HOME>)` of F0006-S0007 for the handlers, and a complete story started through `human.push_file` and `human.start`, because the fixture's backlog story `# First story` has form findings that would turn the stage into rule 1), `tests/entry/test_watch_agent_definition.py`.

## Acceptance criteria

1. `APPLIED_AGENT_KEYS` is exactly `model`, `tools`, `effort` and `budget_usd`.
2. An agent file with only applied keys is read: its `model`, `tools`, `effort` and `budget_usd` are those of the file and its `instructions` is the file's body.
3. An agent file that adds any one of `name`, `description`, `permissionMode`, `hooks`, `background`, `disallowedTools` or `skills` is refused with `AgentDefinitionInvalid` whose `name` is the agent, whose `key` is that key, whose `fault` is `key not applied by the agent runtime: <key>` and whose message contains the key (SI4.1: a test per key the runner does not apply; the first six are v1's dead keys).
4. A key the runner has never heard of (`colour`) and a known key written in another case (`Model`) are refused in the same way (this replaces F0003's test that left `colour` aside).
5. A file with two unapplied keys, `hooks` listed before `description`, is refused naming `hooks`, the first in the file's order.
6. A file with `colour` and no `model` is refused for `colour`, not for the missing `model`.
7. A file with `colour` and `budget_usd: 0` is refused for `colour`, not for the budget.
8. `PipelineLoader.load` raises `AgentDefinitionInvalid` (not `PipelineDefinitionInvalid`) when the agent file of the second of two roles holds an unapplied key and the first role's file is fine, so every role's file is read.
9. When the files of both roles of criterion 8 hold an unapplied key, the error names the first role of `roles`.
10. A definition with one role whose agent is not installed and another whose file holds an unapplied key raises `PipelineDefinitionInvalid` naming the missing agent: the other checks come first.
11. A load of `origin/main` that raises `AgentDefinitionInvalid` leaves exactly one stop in the health status: scope `repository`, reason `agent_definition_invalid`, a detail that is `<agent name>: key not applied by the agent runtime: <key>` (SI4.3).
12. A load of `origin/main` that succeeds afterwards clears the stop `agent_definition_invalid`.
13. A load of `origin/main` that raised `pipeline_definition_invalid`, followed by a load of a valid definition whose second role's file holds an unapplied key, leaves the stop `agent_definition_invalid` and no stop `pipeline_definition_invalid`.
14. A load at another ref (a commit id) of a definition with an agent file that holds an unapplied key raises the same error and leaves the health status as it was, with no stop raised and none cleared.
15. A tick whose pipeline definition names a role with an unapplied key returns `TickOutcome(stopped="agent_definition_invalid")` and the health status holds the stop of criterion 11.
16. That tick does nothing else: no agent run is requested and no event is dispatched, although a started story is waiting on the remote.
17. After the agent file is corrected, the next tick returns `stopped=None`, dispatches the `run` event with the outcome `handled`, and the stop `agent_definition_invalid` is gone.
18. `run_watch` with the same refusal returns 1, writes `factory-watch: agent <name>: key not applied by the agent runtime: <key>` to `err` and nothing to `out`, and leaves the health status as it was.
19. make check stays green.
20. docs: `docs/project-guide.md` lists the four keys an agent file may hold (`model`, `tools`, `effort`, `budget_usd`) with what each does and says that any other key is refused at load; `docs/operator-guide.md` describes the stop `agent_definition_invalid` and that the operator fixes the named file in the agent home, and its agent-file section no longer says that other keys are ignored; `docs/decisions.md` rewrites the entry "Agent files: keys beyond the four are not interpreted until F0010" to say that F0010 decided: the four are applied, every other key is refused at load, and the loader raises the stop.

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
