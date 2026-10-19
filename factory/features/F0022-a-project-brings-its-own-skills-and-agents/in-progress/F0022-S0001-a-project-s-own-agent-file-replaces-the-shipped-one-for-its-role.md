---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 264
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-19T13:15:40.769641Z'
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
