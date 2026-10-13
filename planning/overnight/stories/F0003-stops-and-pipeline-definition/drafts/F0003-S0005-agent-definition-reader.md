# The agent definition reader: which agents are installed and what they say

## Assignment (as of log entry 1)

Build the reader of the agent files, which tells which agents are installed (ST8.3, the second half: a role names an agent that must exist) and reads one agent into the `AgentDefinition` of F0001: `FrontmatterAgentDefinitionReader`, with the `AgentDefinitionReader` abstract base class that it inherits and the agent definition errors. F0005 will use its `read` to compose every task and S0006's loader uses `names()`. The agent file is split as the work item reader splits a work item (python-frontmatter's `detect` and `split`) and its front matter is loaded with ruamel.yaml through `RuamelYamlHandler` (R13; F0002 decision 4), never through PyYAML, which python-frontmatter would use by default. Refusing keys that the agent runtime does not apply is F0010-S0006, which extends `AgentDefinitionInvalid` and does not recreate it; keys beyond `model`, `tools`, `effort` and `budget_usd` are not interpreted here. Covers the installed-agent half of ST8.3 and R30; keeps kept thing 7. The loader that turns a missing agent into a reported stop is S0006.

## Interface

`src/factory/domain/errors.py` (adds to the hierarchy)

```python
class AgentDefinitionError(FactoryError):
    name: str
    fault: str
    def __init__(self, name: str, fault: str) -> None: ...

class AgentDefinitionMissing(AgentDefinitionError): ...

class AgentDefinitionInvalid(AgentDefinitionError):
    key: str                                        # "" for a fault of the whole file
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

`src/factory/adapters/work_item_markdown.py` (the split of `FrontmatterWorkItemReader._split` becomes a function that both readers call; the work item reader's behaviour and tests stay unchanged)

```python
def split_front_matter(handler: RuamelYamlHandler, text: str) -> tuple[str, str] | None: ...
    # the front matter text and the body, or None when there is no front matter
```

`src/factory/adapters/agent_files.py`

```python
class FrontmatterAgentDefinitionReader(AgentDefinitionReader):
    def __init__(self, agent_home: Path) -> None: ...     # the agent files are <agent_home>/agents/<name>.md
    def names(self) -> list[str]: ...
    def read(self, name: str) -> AgentDefinition: ...
```

`src/factory/application/boundaries.py` (adds the field `agent_definitions: AgentDefinitionReader` to `Boundaries`; the `boundaries` fixture gets a `FrontmatterAgentDefinitionReader` on a directory of the test's own).

An agent file, as `read` understands it (the text of `<agent home>/agents/coder.md`, written here as a Python string; the YAML front matter sits between the two lines of three hyphens):

```python
CODER_FILE = "---\nmodel: sonnet\ntools: [Read, Write]\neffort: low\nbudget_usd: 0.1\n---\nThe agent's instructions.\n"
```

Rules for `FrontmatterAgentDefinitionReader`:

- `names()` returns the sorted stems of the regular files with the suffix `.md` that lie directly in `<agent_home>/agents/` and whose stem is a `Name` (`factory.domain.identifiers`: `README` and `Coder` are not agents); other files and subdirectories do not count. When `<agent_home>/agents` is not a directory it raises `AgentDefinitionError(name="", fault="no agents directory at <path>")`.
- `read(name)` goes through these steps, and the first that fails decides:
  1. A `name` that is not a `Name` (`../x`, `a/b`, `Coder`) is `AgentDefinitionMissing(name, fault="not an agent name: <name>")`, before any path is built or any file read.
  2. When `<agent_home>/agents/<name>.md` is not a regular file (absent, or a directory), it is `AgentDefinitionMissing(name, fault="no agent file <path>")`.
  3. The file is read as UTF-8; a file that cannot be read or decoded is `AgentDefinitionInvalid(name, fault="cannot read: <reason>", key="")`.
  4. The text is split with `split_front_matter` and the front matter loaded with a `RuamelYamlHandler` (so `model: on` is the text `on`, as YAML 1.2 reads it, and not the boolean that PyYAML would make of it). A text with no front matter is `AgentDefinitionInvalid(name, "no front matter", key="")`; a `WorkItemFormatError` of the handler (`front matter is not valid YAML`, `front matter is not a mapping`) is `AgentDefinitionInvalid(name, <its fault>, key="")`. The body, without surrounding whitespace, is `instructions`; a later line of hyphens in the body belongs to it.
  5. The keys `model`, `tools`, `effort` and `budget_usd` are validated, with `name` and `instructions`, into the existing `AgentDefinition`; other front matter keys are not interpreted. `effort` is optional and `None` when left out; `tools` may be an empty list; `budget_usd` is the number written (`0.1` gives `Decimal("0.1")`, as pydantic converts it, never a binary float).
  6. A validation fault is `AgentDefinitionInvalid` with `key` the top-level key the fault names. When there are several, the first in the order of `first_fault` (unknown key, missing key, invalid value) is reported. A missing key is `missing key: <key>`; a fault of `budget_usd` that is not a missing key (zero, negative, text, a boolean) is `budget_usd must be greater than 0`; any other is `invalid <path>: <message>` in the spelling of `factory.adapters.validation_faults`.
- The reader constructs one `RuamelYamlHandler` and loads YAML only through it. No variable in the module is named `yaml`, because the project's semgrep rule `factory-no-unsafe-yaml-load` matches any `yaml.load(...)`.
- Each abstract method's body is its docstring alone.

Tests: `tests/adapters/test_agent_files.py`, `tests/application/test_agent_definition_reader.py`; the existing tests of the work item reader stay unchanged. The tests write agent files into a directory in `tmp_path` and build the `boundaries` fixture's reader on it.

## Acceptance criteria

1. `names()` returns the sorted stems of the `.md` files directly in `<agent_home>/agents/`, and leaves out a file with another suffix, a subdirectory, and files named `README.md` and `Coder.md`.
2. `names()` raises `AgentDefinitionError` with `name == ""` and a `fault` that starts with `no agents directory at ` when `<agent_home>/agents` does not exist, and when it is a regular file.
3. `read("coder")` of the agent file `CODER_FILE` in the Interface returns an `AgentDefinition` with `name == "coder"`, `model == "sonnet"`, `tools == ["Read", "Write"]`, `effort == "low"`, `budget_usd == Decimal("0.1")` and `instructions == "The agent's instructions."`.
4. `read` of a file without an `effort` key returns `effort is None`; `read` of a file with `tools: []` returns `tools == []`.
5. `read` of a file with a key it does not interpret (for example `colour: red`) returns the definition as if the key were absent.
6. `read` of a file whose front matter says `model: on` returns `model == "on"`: the YAML is loaded by `RuamelYamlHandler`.
7. `read` of a file whose body holds a line of three hyphens returns that body whole in `instructions`, the line included, with the whitespace around it removed.
8. `read` of a file with no front matter, with front matter that is not YAML (`model: [`), with front matter that is a list, and with bytes that are not UTF-8 raises `AgentDefinitionInvalid` with `key == ""` and a `fault` that is `no front matter`, `front matter is not valid YAML`, `front matter is not a mapping`, and one that starts with `cannot read: ` (one test, four cases).
9. `read` of a file that leaves out `model`, `tools` or `budget_usd` raises `AgentDefinitionInvalid` whose `key` is the missing key and whose `fault` is `missing key: <key>` (one test, three cases).
10. `read` of a file with the wrong type (`model: 3`, `tools: Read`, `effort: 3`) raises `AgentDefinitionInvalid` whose `key` is that key and whose `fault` starts with `invalid <key>:` (one test, three cases).
11. `read` of a file with `budget_usd` 0, -1, `high` or `true` raises `AgentDefinitionInvalid` with `key == "budget_usd"` and the fault `budget_usd must be greater than 0`; `budget_usd` 0.01 is accepted.
12. `read` of a file that has no `model` and `tools: Read` reports the first fault in the reader's order: `key == "model"` and `missing key: model`.
13. `read("nobody")` raises `AgentDefinitionMissing` with `name == "nobody"` and a `fault` that starts with `no agent file `; so does `read("coder")` when `coder.md` is a directory.
14. `read` of a `name` that is not a `Name` (`../x`, `a/b`, `Coder`) raises `AgentDefinitionMissing` with a `fault` that starts with `not an agent name: `, and does not read the file `../x.md` that a test put next to the `agents` directory.
15. `AgentDefinitionMissing` and `AgentDefinitionInvalid` are subclasses of `AgentDefinitionError`, which is a `FactoryError`; each carries its `name` and `fault`, and `AgentDefinitionInvalid` its `key`.
16. `AgentDefinitionReader` is an abstract base class that cannot be instantiated, whose abstract methods are exactly `names` and `read`, each with a body that is its docstring alone, and `FrontmatterAgentDefinitionReader` inherits it.
17. `make check` stays green.
18. docs: `docs/operator-guide.md` says where agent files live (`<agent home>/agents/<name>.md`, keys `model`, `tools`, `effort`, `budget_usd`, the body being the instructions) and lists the faults the reader reports; `docs/project-guide.md` states that every role of the pipeline definition needs an agent file of the same name, that the front matter is read with ruamel.yaml through `RuamelYamlHandler` and split as the work item reader splits it, and its *Faults* section gets a line for the agent reader; `docs/decisions.md` records that other keys are not interpreted until F0010 decides which the runtime applies.

## Demo

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.domain.errors import AgentDefinitionInvalid, AgentDefinitionMissing
home = Path(tempfile.mkdtemp())
agents = home / 'agents'
agents.mkdir()
(agents / 'coder.md').write_text('---\nmodel: sonnet\ntools: [Read, Write]\neffort: low\nbudget_usd: 0.1\n---\nWrite the code.\n')
(agents / 'tester.md').write_text('---\nmodel: sonnet\ntools: Read\nbudget_usd: 1\n---\nWrite the tests.\n')
(agents / 'README.md').write_text('Not an agent.\n')
reader = FrontmatterAgentDefinitionReader(home)
print(reader.names())
agent = reader.read('coder')
print(agent.model, agent.tools, agent.effort, agent.budget_usd, repr(agent.instructions))
try:
    reader.read('tester')
except AgentDefinitionInvalid as error:
    print(error.key, '|', error.fault)
try:
    reader.read('nobody')
except AgentDefinitionMissing as error:
    print(error.name)
"
```
Expect: four lines of output: `['coder', 'tester']`, then `sonnet ['Read', 'Write'] low 0.1 'Write the code.'`, then a line that starts with `tools | invalid tools:`, then `nobody`.

## Log (append only)

1. 2026-10-12 human: created.
