---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 264
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-19T13:31:24.863620Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T13:14:53.654803Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T13:14:53.661411Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T13:15:19.389252Z'
  stage: intake
  run: ca799b0896894fb3891b557fab6428e9
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T13:15:40.769641Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T13:19:45.998145Z'
  stage: tests
  run: a1d79c3efdca49b5942c40a11c16166a
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T13:20:07.125169Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T13:23:12.653072Z'
  stage: doing
  run: 61b207a83e2943428362380f1307848e
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T13:23:33.369419Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T13:24:30.582009Z'
  stage: review
  run: 5fe8c8a5480b4c188a5fafaa829d48b7
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T13:24:51.211353Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-19T13:27:16.588576Z'
  stage: doing
  run: 20d831e10db24367bf8c2fbd356e36d8
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T13:27:37.724482Z'
  stage: review
- number: 13
  speaker: reviewer
  kind: result
  at: '2026-10-19T13:28:25.193850Z'
  stage: review
  run: db39a2456b954fea95959bf34becd2fc
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T13:28:45.654425Z'
  stage: docs
- number: 15
  speaker: documenter
  kind: result
  at: '2026-10-19T13:31:03.098611Z'
  stage: docs
  run: 5991c9db6d644bc7892ef3ee57d49c95
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-19T13:31:24.863620Z'
  stage: smoke-test
---

# A project's own agent file replaces the shipped one for its role

## Description

Today the agent of every role is the file `<agent home>/agents/<role>.md`, which the image fills from v1.1's `claude/agents/`. A project cannot bring its own agent in its repository; the operator can only replace the file in the instance's agent home, outside the project's history. This story lets a project bring its own agents. For each role the factory reads `factory/agents/<role>.md` from the project's `origin/main` first, the same ref it reads the pipeline definition from, so a work item's branch never changes its own agent. It uses the installed agent only when the project has no such file. A project agent replaces the installed one whole; nothing is merged. A project may also add a role whose only agent is its own. The project's file is parsed by the same reader with the same rules (the applied keys, the budget, the refusals). It is checked at the same points: the load of every tick, which raises and clears `agent_definition_invalid` as today, and the preflight's probe. A faulty project file is never replaced by the installed one, and its fault names the file. `factory/agents/*` becomes a protected path, the human's like the pipeline definition. The loader, the task composer and the preflight change nothing: they reach the new reader through `boundaries.agent_definitions`. The agents' skills and the rule text that names `factory/agents/` come in S0002.

## Interface

`factory.domain.identifiers` (`domain`):

```python
def is_name(text: str) -> bool: ...
```

- `True` exactly when `Name` accepts `text` (`coder`, `smoke-tester`, `a1`); `False` for `Coder`, `README`, `1coder`, `co der`, `coder.md` and `""`.
- `factory.adapters.agent_files` uses it in place of its private `_is_name`, which goes; the reader's behaviour stays as it is.

`factory.domain.paths` (`domain`):

```python
PROJECT_AGENTS_DIRECTORY = "factory/agents"

def project_agent_file(name: str) -> str: ...
```

- `project_agent_file("coder")` is `"factory/agents/coder.md"`.

`factory.domain.write_paths` (`domain`):

- `PROTECTED_PATHS` gains `f"{PROJECT_AGENTS_DIRECTORY}/*"` (`"factory/agents/*"`) as its eleventh and last entry, after `"*/feature.md"`.

`factory.application.agent_runtime` (`application`):

```python
class AgentDefinitionReader(ABC):
    ...
    @abstractmethod
    def parse(self, name: str, text: str) -> AgentDefinition:
        """The definition of the agent `name` from the text of an agent file.

        `AgentDefinitionMissing` when `name` is not an agent name, `AgentDefinitionInvalid`
        when the text does not define an agent, with the faults of `read`.
        """
```

`factory.adapters.agent_files` (`adapters`):

- `FrontmatterAgentDefinitionReader.parse(name, text)`: a name that `is_name` refuses raises `AgentDefinitionMissing(name, f"not an agent name: {name}")`. Otherwise the text gets exactly the checks `read` makes once it has read the file, in the same order and with the same faults and keys: `no front matter`, the YAML faults, `key not applied by the agent runtime: <key>`, `missing key: <key>`, `budget_usd must be greater than 0`, `invalid <key>: <reason>`. The body without the whitespace around it is the instructions.
- `read(name)` checks the name, finds and reads the file as today (`no agent file <path>`, `cannot read: <reason>`), then returns `parse(name, text)`. Every fault of `read` stays as it is.

`factory.application.project_agents` (`application`, new):

```python
class ProjectAgentDefinitions(AgentDefinitionReader):
    """A project's own agents at `origin/main` first, the installed ones otherwise."""

    def __init__(self, git: Git, installed: AgentDefinitionReader, ref: str = PIPELINE_REF) -> None: ...
    def names(self) -> list[str]: ...
    def read(self, name: str) -> AgentDefinition: ...
    def parse(self, name: str, text: str) -> AgentDefinition: ...
```

- `PIPELINE_REF` is `factory.application.pipeline_loading.PIPELINE_REF` (`origin/main`).
- `names()`: the sorted union, without repeats, of `installed.names()` and the names of the project's agents: the files at `ref` whose path is `factory/agents/<stem>.md`, directly in that folder, with a stem that `is_name` accepts (`git.list_files(ref, PROJECT_AGENTS_DIRECTORY)`). A file in a subfolder, one with another suffix and one whose stem is not a name are left out. `AgentDefinitionError` of `installed.names()` and `GitError` propagate.
- `read(name)`: a name that `is_name` refuses raises `AgentDefinitionMissing(name, f"not an agent name: {name}")` before any call of `git`. Otherwise the text of `git.show_file(ref, project_agent_file(name))`. When it is `None`, the result is `installed.read(name)`. When there is a text, the result is `installed.parse(name, text)`, and an `AgentDefinitionInvalid` it raises is raised again as `AgentDefinitionInvalid(name, f"{project_agent_file(name)} at {ref}: {fault}", key)`, its `fault` and `key` those of the first. The installed file is then not read.
- It reads `git` at `ref` at every call (no copy kept between calls) and never the checkout's work tree, so the file on a checked-out branch or an uncommitted edit makes no difference.
- `parse(name, text)` is `installed.parse(name, text)`.
- It writes nothing.

`factory.entry.wiring` (`entry`):

- `build_boundaries` gives `agent_definitions=ProjectAgentDefinitions(git, FrontmatterAgentDefinitionReader(settings.agent_home))`, with the `GitCli` of the boundaries' `git`. `FrontmatterAgentDefinitionReader` is still built exactly once, with `settings.agent_home` (`tests/test_agent_home_wiring.py` stays as it is).

Unchanged: `PipelineLoader`, `TaskComposer`, `agent_run_probe_item`, `MachineChecks`, the stop `agent_definition_invalid` and its detail format `<name>: <fault>`.

Tests (the tester writes them): `tests/domain/test_is_name.py`, `tests/domain/test_project_agent_paths.py` (`project_agent_file` and the protected rows), `tests/adapters/test_agent_files_parse.py` (with `AGENT_FILE` and `COLOURED_AGENT_FILE` of `tests/git_support.py`), `tests/application/test_project_agents.py` (the `boundaries`, `human`, `remote` and `agent_home` fixtures of `tests/conftest.py`, `install_agents` and `write_agent` of `tests/git_support.py`; after a `human.push_file`, `boundaries.git.fetch()` before the read), `tests/application/test_pipeline_loading_project_agents.py`, `tests/application/test_tick_project_agent.py` (it imports `STORY`, `BACKLOG_PATH`, `INSTANCE`, `ENVIRONMENT` and `COMPLETED` from `tests/application/test_tick_agent_definition.py` and copies none of them), `tests/application/test_agent_run_probe_project_agent.py`, `tests/entry/test_wiring_project_agents.py`. A test that needs the boundaries with the project's agents builds them with `dataclasses.replace(boundaries, agent_definitions=ProjectAgentDefinitions(boundaries.git, boundaries.agent_definitions))`.

Changed under the feature's decision 14, by the tester only, nothing else in those modules: `tests/domain/test_write_paths.py`, the test `test_the_protected_paths_are_the_engines_ten_patterns`, renamed `test_the_protected_paths_are_the_engines_eleven_patterns`, whose expected tuple gains `"factory/agents/*"` last; `tests/entry/test_wiring_boundaries.py`, in `test_build_boundaries_picks_the_concrete_adapters_and_writes_nothing` the expected class of `agent_definitions` becomes `ProjectAgentDefinitions`, and `test_the_built_agent_definitions_are_read_from_the_agent_home` clones the `remote` fixture into `settings.checkout` with `GitCli` before it builds the boundaries and checks the same names. `tests/application/test_agent_definition_reader.py`: in `test_agent_definition_reader_is_abstract_with_names_and_read` the expected `__abstractmethods__` becomes `{"names", "parse", "read"}`, and in `test_agent_definition_reader_methods_are_their_docstrings_alone` the expected sorted names become `["names", "parse", "read"]`. All four keep their names.

## Acceptance criteria

1. `is_name` gives `True` for `coder`, `smoke-tester` and `a1` and `False` for `Coder`, `README`, `1coder`, `co der`, `coder.md` and `""` (rows of one parametrized test).
2. `project_agent_file("coder")` is `"factory/agents/coder.md"`. `matches_any(path, PROTECTED_PATHS)` is `True` for `factory/agents/coder.md` and `factory/agents/sub/notes.md`, and `False` for `factory/agentsx/coder.md`, `docs/factory/agents/coder.md` and `factory/features/F0001-x/agents/coder.md`. `refusal("factory/agents/coder.md", <guard with write paths ["*"] and PROTECTED_PATHS>)` is `factory/agents/coder.md is owned by the human; a change there is a question.` (rows).
3. `FrontmatterAgentDefinitionReader.parse("coder", AGENT_FILE)` equals `read("coder")` of an agent home that holds `AGENT_FILE` as `coder.md`. For the texts `COLOURED_AGENT_FILE`, one without front matter, one whose front matter is not valid YAML (`---\nmodel: [\n---\nx\n`), one without `budget_usd`, one with `budget_usd: 0` and one with `tools: 3`, `parse` raises `AgentDefinitionInvalid` with the same `fault` and `key` as `read` of the same text in a file. `parse("Coder", AGENT_FILE)` raises `AgentDefinitionMissing` with the fault `not an agent name: Coder` (rows of one parametrized test).
4. `ProjectAgentDefinitions.read("coder")`: with `factory/agents/coder.md` on `main` holding `---\nmodel: opus\ntools: [Read]\nbudget_usd: 2\n---\nThe project's coder.\n` and the installed `AGENT_FILE` for `coder`, it gives model `opus`, tools `["Read"]`, budget `2` and the instructions `The project's coder.`. Without the project file it gives the installed definition (instructions `Do the work.`). With a project file for `tester` only, `read("coder")` gives the installed one (rows).
5. `read("Coder")` and `read("../coder")` raise `AgentDefinitionMissing` with `not an agent name: <name>`, also on a `ProjectAgentDefinitions` whose `ref` is `origin/none`, which does not exist (no `GitError`: the name is checked first); on that instance `read("coder")` and `names()` raise `GitError` (rows).
6. The ref, not the work tree: with `main` holding the project coder above, a work-item branch `work-item/F0001-S0001` whose `factory/agents/coder.md` says `The branch's coder.` checked out in the checkout, and an uncommitted edit of the file there, `read("coder")` still gives `The project's coder.`. After the human pushes `The new coder.` to `main` and the checkout fetches, the next `read("coder")` of the same instance gives `The new coder.` (rows).
7. A faulty project file: `COLOURED_AGENT_FILE` as `factory/agents/coder.md` on `main` raises `AgentDefinitionInvalid` with name `coder`, fault `factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour` and key `colour`, though a valid installed `coder.md` exists; a project file without front matter raises fault `factory/agents/coder.md at origin/main: no front matter` with key `""` (rows).
8. `names()` with installed `coder` and `tester` and, on `main`, `factory/agents/coder.md`, `factory/agents/designer.md`, `factory/agents/README.md`, `factory/agents/Designer.md`, `factory/agents/notes.txt` and `factory/agents/sub/reviewer.md` gives `["coder", "designer", "tester"]`; without `factory/agents/` it gives `["coder", "tester"]`; with an agent home without an `agents` folder it raises `AgentDefinitionError` (rows).
9. `ProjectAgentDefinitions.parse("coder", AGENT_FILE)` equals the installed reader's `parse` of the same text.
10. `PipelineLoader` with the project's agents: with the installed `coder.md` removed from the agent home and `factory/agents/coder.md` on `main` holding a valid agent, `load()` returns the definition; without the project file it raises `PipelineDefinitionInvalid` with `role coder: agent is not installed` (rows).
11. `PipelineLoader.load()` with `COLOURED_AGENT_FILE` as `factory/agents/coder.md` on `main` raises `AgentDefinitionInvalid` and the health status holds one stop `agent_definition_invalid` with the detail `coder: factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour`. After the human replaces the file on `main` with a valid agent and the checkout fetches, the next `load()` returns the definition and the stop is gone.
12. A tick on a started story, whose first stage is `intake`: with `factory/agents/intake.md` on `main` holding `---\nmodel: opus\ntools: [Read]\nbudget_usd: 2\n---\nThe project's intake.\n`, the one request the fake agent runtime gets has an agent with the instructions `The project's intake.`, model `opus`, tools `["Read"]` and budget `2`; without the file, the installed `Do the work.` (rows).
13. `agent_run_probe_item` with the project's agents and `factory/agents/coder.md` on `main` holding `The project's coder.` runs one request whose agent has those instructions and the budget `PROBE_BUDGET_USD`. With `COLOURED_AGENT_FILE` there it fails, no run is requested, and its detail is `agent coder: factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour` (rows).
14. `build_boundaries` on settings whose checkout is a clone of a local remote whose `main` holds `factory/agents/coder.md` (`The project's coder.`), with `coder` and `tester` installed in the agent home: `agent_definitions` is a `ProjectAgentDefinitions`, its `read("coder")` gives `The project's coder.` and its `read("tester")` the agent home's file (rows).
15. `make check` stays green.
16. docs: `docs/operator-guide.md`, *The agent files*: a project's own agents, `factory/agents/<name>.md` on `origin/main`, read before the agent home's for each role at every tick; a project agent replaces the shipped one whole and never extends it (copy the shipped file from `claude/agents/` and change the copy); the same keys and faults, a project file's fault named `factory/agents/<name>.md at origin/main: <fault>`; how to add a role (the role in `factory/pipeline.yml` and its file under `factory/agents/`, in one commit on `main`); how to go back to the shipped agent (remove the file); a branch's own copy is never read; the preflight's probe runs the project's coder, once per image. *The stop `agent_definition_invalid`*: the detail of a project file and that the fix is a commit on `main`. *The pipeline definition*: `factory/agents/` among the engine's protected paths. `docs/project-guide/agents.md`, *The agent definition reader*: `ProjectAgentDefinitions` and where it is wired, `AgentDefinitionReader.parse`. `docs/project-guide/work-items.md`, *Identity, order and places of work items*: `is_name`, `PROJECT_AGENTS_DIRECTORY`. `docs/project-guide/write-guard.md`, *Protected paths and the refusal*: `PROTECTED_PATHS` as eleven patterns. `docs/decisions.md`: an entry *A project's agent replaces the shipped one, never extends it*, dated with the story, with the reasons of the feature's decisions 1 to 6.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git init -q --bare --initial-branch=main "$d/remote.git"
git init -q --initial-branch=main "$d/human"
git -C "$d/human" remote add origin "$d/remote.git"
uv run -q python - "$d" <<'EOF'
import sys
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.git_cli import GitCli
from factory.application.project_agents import ProjectAgentDefinitions
from factory.domain.errors import AgentDefinitionInvalid

d = Path(sys.argv[1])
agents = d / "human" / "factory" / "agents"
agents.mkdir(parents=True)
(agents / "coder.md").write_text("---\nmodel: opus\ntools: [Read]\nbudget_usd: 2\n---\nThe project's coder.\n", encoding="utf-8")
(agents / "designer.md").write_text("---\nmodel: sonnet\ntools: [Read]\nbudget_usd: 1\ncolour: red\n---\nThe designer.\n", encoding="utf-8")
human = GitCli(d / "human")
human.commit("project agents")
print(human.push("main"))
checkout = GitCli(d / "checkout")
checkout.clone(str(d / "remote.git"))
reader = ProjectAgentDefinitions(checkout, FrontmatterAgentDefinitionReader(Path("claude")))
coder = reader.read("coder")
print(coder.model, coder.budget_usd, coder.instructions)
print(reader.read("tester").instructions.splitlines()[0])
print(" ".join(reader.names()))
try:
    reader.read("designer")
except AgentDefinitionInvalid as error:
    print(error.fault)
EOF
```
Expect: five lines, `pushed`, `opus 2 The project's coder.`, `You test what the criteria say and nothing else; a case they leave open is a question.`, `acceptance-reviewer coder designer documenter intake reviewer smoke-tester tester`, `factory/agents/designer.md at origin/main: key not applied by the agent runtime: colour`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: concrete modules and signatures throughout (`identifiers.is_name`, `paths.project_agent_file`, `PROTECTED_PATHS` as the eleventh entry, `AgentDefinitionReader.parse`, `FrontmatterAgentDefinitionReader.parse`, `ProjectAgentDefinitions` with its constructor and methods, the `build_boundaries` wiring). The faults of `parse` and the wrapped fault format are spelled out, and the earlier tests that must change are named in the Interface and in feature decision 14.
   Criteria: 1 to 14 are each testable by one parametrized test. Every rule has both sides. The name check is in 1, 3 and 5. The project file versus the installed one is in 4. The ref versus the work tree, and no cache, is in 6. A faulty project file and no fallback is in 7. The names filter (subfolder, suffix, non-name, union, sorted) and the installed-reader error are in 8. The `GitError` and name-first ordering is in 5. The loader and its stop (raised and cleared) are in 10 and 11. The tick and the probe, valid and faulty, are in 12 and 13. The wiring is in 14. Two small gaps are not worth a question. "The installed file is then not read" is covered through 7, where a valid installed file exists. "Writes nothing" has no criterion of its own.
   Smoke test: runnable. `GitCli.commit` stages everything, `push` returns "pushed", `clone` creates the folder, and `show_file` and `list_files` exist. `claude/agents` holds the seven names the Expect line lists. Each of the five Expect lines is checkable against the output.
   Architecture: `ProjectAgentDefinitions` is an application class over the `Git` ABC and the reader ABC, and it is wired only in `factory.entry.wiring`. `is_name` and the paths sit in the domain, the adapter keeps the parsing, and `PIPELINE_REF` comes from the application layer. The layering holds.
   Scope: it stays within feature scope S0001, with nothing from the out-of-scope list. Skills, the shipped agent texts and the entrypoint are left to S0002. The write paths cover the files named. The tester's changes to earlier tests are the ones decision 14 lists.
4. factory: started tests as self.
5. tester: I wrote the tests for criteria 1 to 14. One test per criterion; each rule's cases are rows of one parametrized test. `make lint` is green. I ran `make test` once and it fails as expected: test modules fail at collection because the names they import do not exist yet.

   Criterion → test:
   - criterion 1: tests/domain/test_is_name.py::test_is_name_accepts_exactly_the_names
   - criterion 2: tests/domain/test_project_agent_paths.py::test_the_project_agent_file_lies_in_the_project_agents_directory, ::test_the_project_agents_folder_is_protected (the matches_any rows), ::test_a_write_to_a_project_agent_file_is_refused_as_the_humans
   - criterion 3: tests/adapters/test_agent_files_parse.py::test_parse_gives_what_read_gives_for_the_same_text_in_a_file
   - criterion 4: tests/application/test_project_agents.py::test_the_project_file_replaces_the_installed_agent_of_its_role
   - criterion 5: tests/application/test_project_agents.py::test_a_name_that_is_not_an_agent_name_is_refused_before_git_is_read (refs origin/main and origin/none), ::test_a_ref_that_does_not_exist_is_a_git_error (rows read and names)
   - criterion 6: tests/application/test_project_agents.py::test_the_agent_is_read_at_the_ref_at_every_call_never_from_the_work_tree
   - criterion 7: tests/application/test_project_agents.py::test_a_faulty_project_file_is_refused_naming_the_file_never_replaced
   - criterion 8: tests/application/test_project_agents.py::test_names_are_the_sorted_union_of_installed_and_project_agents, ::test_names_without_an_installed_agents_folder_is_an_error
   - criterion 9: tests/application/test_project_agents.py::test_parse_is_the_installed_readers_parse
   - criterion 10: tests/application/test_pipeline_loading_project_agents.py::test_a_role_without_an_installed_agent_loads_with_the_project_agent_alone
   - criterion 11: tests/application/test_pipeline_loading_project_agents.py::test_a_faulty_project_agent_stops_the_load_until_main_holds_a_valid_one
   - criterion 12: tests/application/test_tick_project_agent.py::test_the_stage_runs_the_project_agent_of_its_role (imports STORY, BACKLOG_PATH, INSTANCE, ENVIRONMENT and COMPLETED from tests/application/test_tick_agent_definition.py and copies none of them)
   - criterion 13: tests/application/test_agent_run_probe_project_agent.py::test_the_probe_runs_the_project_coder
   - criterion 14: tests/entry/test_wiring_project_agents.py::test_the_built_agent_definitions_read_the_project_agents_first

   Files I created: tests/domain/test_is_name.py, tests/domain/test_project_agent_paths.py, tests/adapters/test_agent_files_parse.py, tests/application/test_project_agents.py, tests/application/test_pipeline_loading_project_agents.py, tests/application/test_tick_project_agent.py, tests/application/test_agent_run_probe_project_agent.py, tests/entry/test_wiring_project_agents.py.

   Earlier test files I changed, as the Interface lists under the feature's decision 14 (all four tests keep their names, except the one rename the Interface asks for):
   - tests/domain/test_write_paths.py: `test_the_protected_paths_are_the_engines_ten_patterns` is renamed `..._eleven_patterns`, and its expected tuple gains `"factory/agents/*"` last.
   - tests/entry/test_wiring_boundaries.py: `test_build_boundaries_picks_the_concrete_adapters_and_writes_nothing` now expects `ProjectAgentDefinitions`. The now-unused `FrontmatterAgentDefinitionReader` import is gone. `test_the_built_agent_definitions_are_read_from_the_agent_home` takes the `remote` fixture, clones it into `settings.checkout` with `GitCli` before building the boundaries, and checks the same names.
   - tests/application/test_agent_definition_reader.py: the expected abstract methods and the sorted method names now include `parse`.

   Names the test run could not import:
   - `factory.domain.identifiers.is_name`
   - `factory.domain.paths.PROJECT_AGENTS_DIRECTORY` and `project_agent_file`
   - the module `factory.application.project_agents`

   The collection errors I saw included tests/domain/test_is_name.py, tests/domain/test_project_agent_paths.py, tests/entry/test_wiring_boundaries.py and tests/entry/test_wiring_project_agents.py. tests/adapters/test_agent_files_parse.py can be imported; it fails because `FrontmatterAgentDefinitionReader.parse` does not exist yet.

   Nothing needed interpreting. No test checks "writes nothing" or "the installed file is then not read" on its own: no criterion names them. The second is covered indirectly by criterion 7, where a valid installed coder.md exists.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/entry/test_wiring_project_agents.py - ImportError while importing...
6. factory: started doing as self.
7. coder: I implemented the Interface, and all the tester's tests pass unchanged. `make check` is green (`check: green`). No code changed after that run.

   What I built:
   - `src/factory/domain/identifiers.py`: new `is_name`, built on the existing `Name` type through a module-level `TypeAdapter`.
   - `src/factory/domain/paths.py`: `PROJECT_AGENTS_DIRECTORY` and `project_agent_file`.
   - `src/factory/domain/write_paths.py`: `PROTECTED_PATHS` gains `f"{PROJECT_AGENTS_DIRECTORY}/*"` as its eleventh and last entry.
   - `src/factory/application/agent_runtime.py`: the abstract `AgentDefinitionReader.parse`.
   - `src/factory/adapters/agent_files.py`: the private `_is_name` is gone and the reader uses `is_name`. The name refusal is now one private `_check_name`, used by both `read` and `parse`. `read` finds and reads the file as before, then returns `self.parse(name, text)`. `parse` does the front matter, unapplied-key and validation checks that `read` used to do inline, in the same order, so `read`'s faults are unchanged.
   - `src/factory/application/project_agents.py` (new): `ProjectAgentDefinitions`.
     - `read` checks the name before any git call, then reads `show_file(ref, project_agent_file(name))`. With no file it falls back to `installed.read`. With a file it uses `installed.parse` and re-raises an `AgentDefinitionInvalid` with the fault prefixed `<path> at <ref>: `, keeping its key.
     - `names` is the sorted union of the installed names and the project's names.
     - Nothing is kept between calls.
   - `src/factory/entry/wiring.py`: `build_boundaries` wraps the single `FrontmatterAgentDefinitionReader` in `ProjectAgentDefinitions` with the boundaries' `GitCli`.

   Main choice: `names()` keeps a project file only when its stem passes `is_name` and `project_agent_file(stem)` gives back exactly the listed path. That one round trip drops files in subfolders, files with another suffix and stems that are not names, and reuses the path helper. I rejected splitting the path with `PurePosixPath` and checking the parent folder and suffix separately: that is more code and repeats what `project_agent_file` already says.

   Refactor pass: I gave `paths.py` its own `_AGENT_SUFFIX` rather than reusing `_WORK_ITEM_SUFFIX` for agent files, which would have misled the reader, and I folded the duplicated name refusal into `_check_name`. Nothing else needed changing.

   Noticed but not touched:
   - I did not run the work item's smoke test, because running that script was not permitted in this stage; the smoke-test stage still has to run it.
   - `project_agents.py` uses a literal `".md"` when it strips the suffix in `names()`. It is safe because of the round-trip check against `project_agent_file`, but a reviewer may prefer a shared constant from `paths`. I left it rather than export a new public name.

   The journal did not change the meaning of the task, so I left `## Description` as it is.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: Round 0 review. I read the work item, the diff stat, the full diff under `src/` and `tests/`, and the output of `make duplicates`.

   Checklist groups 1 to 3 pass:
   - Group 1: each of criteria 1 to 14 has a test that checks what the criterion says, and the failing sides the Interface states are tested. The coder's `make check` was green (entry 7).
   - Group 2: layers and wiring hold. `ProjectAgentDefinitions` sits in `factory.application` over the `Git` and `AgentDefinitionReader` ABCs, and it is wired only in `factory.entry.wiring` with the boundaries' `GitCli`.
   - Group 3: the name is checked before any git path is built, and the diff adds no suppression marker.
   - None of the 5 new `make duplicates` findings is in a file this diff touches (`claude_runtime`, `opencode_runtime`, `clock`).

   Group 4 (quality) fails:
   1. `src/factory/application/project_agents.py:30-31`: the name refusal `if not is_name(name): raise AgentDefinitionMissing(name, f"not an agent name: {name}")` copies `_check_name` in `src/factory/adapters/agent_files.py:24-26`, which this diff added. The fault text now lives in two places, and the application layer cannot import the adapter's private helper. Fix: move the check to one public domain function beside `is_name` in `factory.domain.identifiers` (or beside `AgentDefinitionMissing`) that raises `AgentDefinitionMissing` with that fault. Use it in `ProjectAgentDefinitions.read` and in `FrontmatterAgentDefinitionReader` in place of `_check_name`, keeping the check before git is read.
   2. `src/factory/application/project_agents.py:53`: the literal `".md"` in `_project_names` repeats the agent suffix that `factory.domain.paths` holds as `_AGENT_SUFFIX` (and `agent_files.py` as its own `_AGENT_SUFFIX`). Fix: take the suffix from `factory.domain.paths`, for example as a public `AGENT_SUFFIX` beside `PROJECT_AGENTS_DIRECTORY` that `project_agent_file` uses, instead of writing it a third time.

   Earlier tests:
   - `tests/application/test_agent_definition_reader.py`: the human's leave. The story's Interface names both changes under the feature's decision 14 (`parse` added to the expected abstract methods and sorted names; both tests keep their names).
   - `tests/domain/test_write_paths.py`: the human's leave. The story's Interface names the rename to `test_the_protected_paths_are_the_engines_eleven_patterns` and `"factory/agents/*"` added last.
   - `tests/entry/test_wiring_boundaries.py`: the human's leave. The story's Interface names both changes: the expected class becomes `ProjectAgentDefinitions`, and the test clones `remote` into `settings.checkout` and checks the same names. The removed `FrontmatterAgentDefinitionReader` import was left unused by that change.
10. factory: started doing as self.
11. coder: Round 1: I fixed both review findings and changed nothing else. No test changed. `make check` is green (`check: green`).

    What I built:
    - Finding 1, the copied name refusal. The check is now one public domain function, `check_agent_name(name)`, in `src/factory/domain/agent_runs.py` beside the other agent rules (`APPLIED_AGENT_KEYS`, `KEY_NOT_APPLIED`). It raises `AgentDefinitionMissing(name, f"not an agent name: {name}")`. Three callers use it:
      - `FrontmatterAgentDefinitionReader.read` and `parse` in `src/factory/adapters/agent_files.py`, where the private `_check_name` is gone;
      - `ProjectAgentDefinitions.read` in `src/factory/application/project_agents.py`, where it still runs before any call of `git`.
    - Finding 2, the repeated `".md"`. `src/factory/domain/paths.py` now exports a public `AGENT_SUFFIX` beside `PROJECT_AGENTS_DIRECTORY`, and `project_agent_file` uses it. `project_agents.py` uses it in `_project_names` in place of the literal. `agent_files.py` drops its own `_AGENT_SUFFIX` and uses it too, so the suffix is written once.

    Main choice: I put `check_agent_name` in `factory.domain.agent_runs` rather than in `factory.domain.identifiers`, where the reviewer offered either.
    - The refusal is an agent rule that raises an agent error. `identifiers` is about work item ids and names, and imports no errors today.
    - `agent_runs` already imports from `identifiers`, and `errors` imports nothing of either, so no import cycle arises.

    Refactor pass: I reread the diff and nothing more needed changing.

    Noticed but not touched: `paths.py` still has the private `_WORK_ITEM_SUFFIX = ".md"` beside the new `AGENT_SUFFIX`. Both hold `.md`, but they mean different things, so I left them separate.

    The journal did not change the meaning of the task, so I left `## Description` as it is.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
12. factory: started review as self.
13. reviewer: Round 1 review. I read the work item, the diff's stat and name-status, and the full diff under `src/` and `tests/`.

    no findings

    - Group 1, acceptance criteria: each of criteria 1 to 14 has a test that checks what it says, with its rows as one parametrized test. The failing sides the Interface states are tested: a refused name in `read` and `parse`, `GitError` on a ref that does not exist (for both `read` and `names`), a faulty project file with no fallback to the installed one, an agent home with no `agents` folder, and the stop raised and then cleared. The coder's `make check` was green (entries 7 and 11).
    - Group 2, architecture: `check_agent_name` sits in `factory.domain.agent_runs`, a domain module importing domain modules (`errors` does not import `agent_runs`, so there is no cycle). `ProjectAgentDefinitions` is in `factory.application` over the `Git` and `AgentDefinitionReader` ABCs. It is wired only in `factory.entry.wiring`.
    - Group 3, security: the name is checked before any git path or file path is built, and the diff adds no suppression marker.
    - Group 4, quality: both round-0 findings are fixed. `src/factory/domain/agent_runs.py:36` `check_agent_name` is now the only place the name refusal lives; `adapters/agent_files.py` and `application/project_agents.py` both call it. `src/factory/domain/paths.py:18` `AGENT_SUFFIX` is the only place `.md` is written for agent files; `agent_files.py`, `project_agents.py` and `project_agent_file` all use it. No dead code is left (`_is_name`, `_NAME` and `_AGENT_SUFFIX` are gone from `agent_files.py`). `make duplicates` is unchanged at 5 new, and none of them is in a file this diff touches (entry 9).
    - Group 5, hygiene: entry 11 explains why `check_agent_name` went into `agent_runs` and not into `identifiers`. The Description and the docs criterion still describe what was built.

    Earlier tests:
    - `tests/application/test_agent_definition_reader.py`: the human's leave. The story's Interface lists it under the feature's decision 14: `parse` is added to the expected abstract methods and to the sorted names, and both tests keep their names.
    - `tests/domain/test_write_paths.py`: the human's leave. The story's Interface names the rename to `test_the_protected_paths_are_the_engines_eleven_patterns` and `"factory/agents/*"` added last.
    - `tests/entry/test_wiring_boundaries.py`: the human's leave. The story's Interface names both changes: the expected class is now `ProjectAgentDefinitions`, and the test clones `remote` into `settings.checkout` and checks the same names. The removed `FrontmatterAgentDefinitionReader` import is the one that change left unused.

    Notes:
    - `tests/application/test_agent_run_probe_project_agent.py:18-35`: `ENVIRONMENT`, `COMPLETED` and the `settings` fixture are copied from `tests/application/test_agent_run_probe.py:36-80`. The standing leave would let the tester move them to one shared place.
    - `PROJECT_CODER` and its likes (`AGENT_FILE.replace("Do the work.", "The project's coder.")`, or the opus/Read/2 text) are defined again in `tests/application/test_project_agents.py`, `test_agent_run_probe_project_agent.py` and `tests/entry/test_wiring_project_agents.py`. One constant in `tests/git_support.py` would do.
    - `tests/application/test_pipeline_loading_project_agents.py:30` and `tests/application/test_project_agents.py:69`: the tests take a parameter and branch on it in the body (`if project_file:`, `if files:`) rather than giving each row its own setup data.
14. factory: started docs as self.
15. documenter: Round 1 docs. I wrote the documentation the docs criterion asks for. I changed only documents, so I did not run `make check`; the factory runs it next. `make documents` reports `documents ok`. No findings: the diff matches the Interface and the criteria.

    Files changed:
    - `docs/operator-guide.md`:
      - *The agent files* now says an agent is the project's `factory/agents/<name>.md` on `origin/main` or the installed one. A new subsection, *A project's own agents*, covers read-first at every tick, whole replacement and never extension (copy from `claude/agents/`), the same keys and faults, and the fault text `factory/agents/<name>.md at origin/main: <fault>`. It also covers adding a role (one commit on `main`), going back to the shipped agent (remove the file), a branch's copy never being read, and the probe.
      - *The stop `agent_definition_invalid`* gives the detail of a project file and says the fix is a commit on `main`.
      - *The pipeline definition* lists `factory/agents/` among the protected paths and now says a role's agent may be the project's or the installed one.
      - The `pipeline_definition_invalid` table row `role <role>: agent is not installed` now names both places.
      - *The probe of the agent run* now says it runs the project's `coder` when there is one.
    - `docs/project-guide/agents.md`, *The agent definition reader*: three operations, `parse`, and `check_agent_name`. A new subsection, *A project's own agents*, describes `ProjectAgentDefinitions` and where it is wired.
    - `docs/project-guide/work-items.md`, *Ids and names*: `is_name`, `PROJECT_AGENTS_DIRECTORY`, `project_agent_file`, `AGENT_SUFFIX`.
    - `docs/project-guide/write-guard.md`, *Protected paths and the refusal*: eleven patterns, with `factory/agents/*` last.
    - `docs/decisions.md`: the new entry *A project's agent replaces the shipped one, never extends it*, with the reasons of decisions 1 to 6 and what was rejected.

    Cross-read and found current: the operator guide's remaining agent sections (*The shipped agents and settings*, the fault table of the reader). Also current: the reader's *Faults* table in `agents.md`; my addition there touches only the first lines. `README.md` names no agent location or protected-path count.

    Not touched:
    - The probe paragraph in the operator guide still says a missing `coder` fails with "the reader's message naming the agent". That stays true, so I left it.
    - The reviewer's test notes from round 1 are for the tester, not the docs: the copied `ENVIRONMENT`, `COMPLETED` and `settings` in `tests/application/test_agent_run_probe_project_agent.py`, and the repeated `PROJECT_CODER` text.

    `check`: check: green
    `documents`: documents ok
16. factory: started smoke-test as self.
