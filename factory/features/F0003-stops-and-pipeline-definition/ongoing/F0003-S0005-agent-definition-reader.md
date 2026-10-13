---
stage: docs
pr: 44
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
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

`src/factory/application/agent_runtime.py` (adds to F0001-S0008's module)

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

Tests: `tests/adapters/test_agent_files.py`, `tests/application/test_agent_definition_reader.py`; the existing tests of the work item reader stay unchanged. The tests write agent files into a directory in `tmp_path` and build the `boundaries` fixture's reader on it. The test that `AgentDefinitionReader` cannot be instantiated (criterion 16) calls it through a variable typed `type[object]` (`interface: type[object] = AgentDefinitionReader`), as `tests/application/test_interfaces.py` does, because a direct call is a `mypy --strict` error (`abstract`).

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
2. intake: accepted
   - Interface: concrete modules and signatures throughout (errors.py, agent_runtime.py, work_item_markdown.split_front_matter, agent_files.py, Boundaries field). It builds on code that exists: `AgentDefinition` (domain/agent_runs.py), `Name`, `RuamelYamlHandler`, `first_fault` in adapters/validation_faults.py, and the current `_split` in work_item_markdown.py that becomes the shared function.
   - Criteria: each is testable by one test function (criteria 8, 9 and 10 are parametrized). Every Interface rule has a criterion for both sides. Passing side: 1, 3-7, and 11 with 0.01. Failing side: 2 (missing agents directory), 8, 9, 10, 11 (0, -1, text, boolean), 12 (fault order), 13 (absent file, directory) and 14 (bad names, plus no read of `../x.md`). Criterion 15 covers the error hierarchy, 16 the abstract base class, 18 the docs.
   - Demo: runnable with `uv run python -c`. The Expect line gives four checkable lines, including the `tools | invalid tools:` prefix.
   - Architecture: the interface sits in application, the reader in adapters, the errors in domain, and the wiring through `Boundaries`. The one YAML handler, the semgrep naming rule and the ABC convention are all respected.
   - Scope: inside F0003 ("the agent definition reader that tells which agents are installed and reads one"). Refusing runtime-inapplicable keys stays with F0010, and the loader with S0006.
3. tester: Wrote the red tests for the agent definition reader, one per criterion.

   - criterion 1: tests/adapters/test_agent_files.py::test_names_are_the_sorted_agent_file_stems_alone (leaves out notes.txt, a `nested.md` directory, sub/deep.md, README.md and Coder.md)
   - criterion 2: tests/adapters/test_agent_files.py::test_names_without_an_agents_directory_is_an_error (two cases: absent, regular file)
   - criterion 3: tests/adapters/test_agent_files.py::test_an_agent_file_is_read_into_its_definition
   - criterion 4: tests/adapters/test_agent_files.py::test_effort_left_out_is_none_and_tools_may_be_empty
   - criterion 5: tests/adapters/test_agent_files.py::test_a_key_the_reader_does_not_interpret_is_left_aside
   - criterion 6: tests/adapters/test_agent_files.py::test_front_matter_is_read_as_yaml_one_point_two
   - criterion 7: tests/adapters/test_agent_files.py::test_a_line_of_hyphens_in_the_body_belongs_to_the_instructions
   - criterion 8: tests/adapters/test_agent_files.py::test_a_file_that_is_not_an_agent_file_is_invalid_as_a_whole (four cases)
   - criterion 9: tests/adapters/test_agent_files.py::test_a_required_key_left_out_is_named (three cases)
   - criterion 10: tests/adapters/test_agent_files.py::test_a_value_of_the_wrong_type_is_named_with_its_key (three cases)
   - criterion 11: tests/adapters/test_agent_files.py::test_a_budget_that_is_not_a_positive_number_is_refused (0, -1, high, true) and ::test_a_budget_of_one_cent_is_accepted (0.01)
   - criterion 12: tests/adapters/test_agent_files.py::test_a_missing_key_is_reported_before_an_invalid_value
   - criterion 13: tests/adapters/test_agent_files.py::test_an_agent_without_a_file_is_missing (nobody; coder.md as a directory)
   - criterion 14: tests/adapters/test_agent_files.py::test_a_name_that_is_not_an_agent_name_is_missing_without_reading_a_file (`../x`, `a/b`, `Coder`). The test puts valid agent files at `<agent_home>/x.md`, `agents/a/b.md` and `agents/Coder.md`, so reading any of them would return a definition instead of raising.
   - criterion 15: tests/application/test_agent_definition_reader.py::test_agent_definition_errors_carry_name_fault_and_key
   - criterion 16: tests/application/test_agent_definition_reader.py::test_agent_definition_reader_is_abstract_with_names_and_read, ::test_agent_definition_reader_methods_are_their_docstrings_alone, ::test_frontmatter_reader_implements_the_agent_definition_reader
   - Boundaries field (Interface): tests/application/test_agent_definition_reader.py::test_boundaries_hand_out_a_frontmatter_reader_on_the_agent_home

   Files: created tests/adapters/test_agent_files.py and tests/application/test_agent_definition_reader.py. Changed tests/conftest.py: a new `agent_home` fixture (`tmp_path / "agent-home"`, nothing created in it), and the `boundaries` fixture now passes `agent_definitions=FrontmatterAgentDefinitionReader(agent_home)`, as the Interface says. The adapter tests build the reader directly on `agent_home` so they don't need a git checkout. Only the boundaries test goes through the fixture.

   Not tested: `split_front_matter` on its own. No criterion names it, and the existing work item reader tests are unchanged.

   `make test` result: conftest fails to import with ModuleNotFoundError: No module named 'factory.adapters.agent_files', so every test is red for the right reason until that module exists. Also not importable yet: `factory.application.agent_runtime.AgentDefinitionReader` and `factory.domain.errors.AgentDefinitionError/Missing/Invalid`. `make lint` is green.

   `make lint`: lint: green
   `make test`: E   ModuleNotFoundError: No module named 'factory.adapters.agent_files'
4. coder: Built the agent definition reader. Commit 2193fdb. `make check` is green and the demo prints the four lines it should expect.

   - `src/factory/domain/errors.py`: adds `AgentDefinitionError(name, fault)` and its subclasses `AgentDefinitionMissing` and `AgentDefinitionInvalid(name, fault, key)`.
   - `src/factory/application/agent_runtime.py`: adds the `AgentDefinitionReader` ABC with `names` and `read`. Each method's body is its docstring alone.
   - `src/factory/application/boundaries.py`: adds the field `agent_definitions: AgentDefinitionReader`. No code in `src` builds `Boundaries` yet, so the only wiring is the tester's fixture.
   - `src/factory/adapters/work_item_markdown.py`: `FrontmatterWorkItemReader._split` is now the module function `split_front_matter(handler, text)`. Both readers call it; its behaviour is the same.
   - `src/factory/adapters/agent_files.py`: `FrontmatterAgentDefinitionReader`.
     - The name is checked through `TypeAdapter(Name)` before any path is built.
     - `read` then checks for a regular file, reads it as UTF-8, splits it with `split_front_matter` and loads the front matter with one `RuamelYamlHandler`.
     - Only `model`, `tools`, `effort` and `budget_usd` go into `AgentDefinition.model_validate`, together with `name` and `instructions`. Any other key is ignored, because `AgentDefinition` is `extra="forbid"`.
     - A `budget_usd` fault that is not a missing key becomes `budget_usd must be greater than 0`. Every other fault uses `first_fault`'s spelling.
   - `src/factory/adapters/validation_faults.py`: new `first_error(validation_error) -> ErrorDetails`, which is the `min` by the existing rank. `first_fault` now formats that error. Its result is unchanged, because the sort was stable.

   Main decision: the reported `key` comes from `first_error`, the same error that `first_fault` formats, so the key and the fault always name the same problem. Rejected: re-ranking pydantic's errors inside `agent_files.py`. That would have copied the rank order kept in `validation_faults`.

   Refactor: I reread the diff and found nothing to change, so there is no separate refactor commit.

   Noticed but not touched: nothing.

   `make check`: check: green
5. reviewer: one finding, sent back to doing.

   Groups 1–3 pass. Every criterion from 1 to 16 has a test that checks what it says. Both sides of each Interface rule are tested: no agents directory against a present one, `budget_usd` 0 against 0.01, a missing key ranked before an invalid value, a bad name refused before any read, with decoy files at `x.md`, `agents/a/b.md` and `agents/Coder.md`. The coder's entry reports `make check` green. All layer imports point downward. The interface is an ABC whose method bodies are their docstrings alone, and the reader inherits it. YAML is loaded only through the one `RuamelYamlHandler`, and no variable is named `yaml`. There are no suppression markers and no secrets. Moving `_split` to `split_front_matter` keeps its behaviour. `first_error` uses `min` by `_rank`, which picks the same error as the first item of the stable sort, so `first_fault` returns the same result as before.

   Findings:
   1. `src/factory/application/agent_runtime.py`, docstring of `AgentDefinitionReader.names`: it says `AgentDefinitionError` is raised "without any" agents. The Interface says the error is raised only when `<agent_home>/agents` is not a directory; an empty agents directory returns `[]` (`agent_files.py` `names`). S0006's loader will be written against this docstring. Fix: reword it, for example "The names of the installed agents, sorted; `AgentDefinitionError` when there is no agents directory."
6. coder: Round 1: fixed the reviewer's one finding. Commit f036740.

   - `src/factory/application/agent_runtime.py`, `AgentDefinitionReader.names`: the docstring said `AgentDefinitionError` was raised "without any" agents. It now says the error is raised only when there is no agents directory, and that an empty agents directory gives `[]`. This matches the Interface and the code in `agent_files.py`.
   - I split the docstring over two lines, summary and detail, because the reviewer's one-line wording was longer than the line-length limit.

   Only this docstring changed: no other code, and no tests. There is no separate refactor commit. Before amending the commit I re-ran `make check`, and it passed.

   `make check`: check: green

   `make check`: check: green
7. reviewer: no findings; passed on to docs.

   Round 1 fix: the docstring of `AgentDefinitionReader.names` in `src/factory/application/agent_runtime.py` now says `AgentDefinitionError` is raised only when there is no agents directory, and that an empty directory gives `[]`. That matches the Interface and `agent_files.py` `names`. Entry 5's finding is closed.

   What I checked again across the whole diff:
   - **Criteria.** Criteria 1–16 each have a test that checks what the criterion says, and both sides of every Interface rule are tested:
     - an absent agents directory and one that is a regular file, against the populated case;
     - `budget_usd` at 0, -1, `high` and `true`, against 0.01;
     - a missing key ranked before an invalid value;
     - a bad name refused before any read, with decoy files at `agent_home/x.md`, `agents/a/b.md` and `agents/Coder.md`;
     - `coder.md` as a directory, and `nobody` absent.
     The coder's entry reports `make check` green.
   - **Architecture.**
     - The errors are in domain, the ABC in application and the reader in adapters, and every import points downward.
     - The ABC's methods have docstring-only bodies, and `FrontmatterAgentDefinitionReader` inherits it.
     - `Boundaries` is built only in `tests/conftest.py`, so the new field needs no other wiring.
     - YAML is loaded only through the one `RuamelYamlHandler`, and no variable is named `yaml`.
   - **Security.** No suppression markers and no secrets. The name is validated as a `Name` before any path is built.
   - **Quality.**
     - `split_front_matter` is the old `_split` moved without changes, and the work item reader tests are untouched.
     - `first_error` takes `min` by `_rank`, which picks the same error as the first element of the old stable sort, so `first_fault` returns what it did before. The reported key and fault come from that same error.
     - Comments explain why, and the public names have their docstrings.
   - **Ticket hygiene.** The log names the main decision (key and fault both come from `first_error`) and what was rejected (re-ranking inside `agent_files.py`). The Assignment matches what was built, and criterion 18 still describes what the documenter has to write.
