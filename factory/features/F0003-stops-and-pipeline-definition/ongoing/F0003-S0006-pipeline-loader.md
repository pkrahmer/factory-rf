---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Loading the pipeline definition: installed agents and a reported stop

## Assignment (as of log entry 1)

Build `PipelineLoader`, the one place that loads the pipeline definition (R30): it reads `factory/pipeline.yml` at a git ref (by default `origin/main`, never the work tree), validates it through the reader of S0004, checks that the agent of every role is installed through the reader of S0005, and turns every refusal of the definition at `origin/main` into a reported stop (ST3, ST8.1): a `pipeline_definition_invalid` stop through S0002's `StopService` that names the fault, followed by `PipelineDefinitionInvalid`, so that the tick does nothing else; a later successful load of `origin/main` clears the stop. The stop is about the definition on `origin/main`: a load at any other ref still raises `PipelineDefinitionInvalid` but raises and clears no stop, so a read at another ref (the human's look at a branch) never changes the health status; the write paths at the stage-start commit are parsed directly by `WritePathService.at` (F0004 decision 16). Only the loader raises and clears this stop; no caller does (F0006's tick and `factory-watch` take what `load` gives). Covers ST8.1 (a missing key without default is a reported stop at load, one with a default takes it), the installed-agent half of ST8.3, and R30; keeps kept things 7 and 12. The refusals that look across keys (ST8.2, the write-path half of ST8.3, ST8.4, ST8.5, GH1.4) are S0007, which needs nothing more from the loader.

## Interface

`src/factory/application/pipeline_loading.py`

```python
PIPELINE_REF = "origin/main"                        # REMOTE + "/" + MAIN_BRANCH of factory.domain.paths

class PipelineLoader:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def load(self, ref: str = PIPELINE_REF) -> PipelineDefinition: ...
        # PipelineDefinitionInvalid (after its stop is raised, when ref is PIPELINE_REF); GitError; OSError from the stop's writes
```

Rules for `PipelineLoader.load(ref)`:

- It reads `PIPELINE_DEFINITION_FILE` at `ref` with `boundaries.git.show_file`, parses it with `boundaries.pipeline_reader`, and then checks the agents with `boundaries.agent_definitions`. It never reads a file of the work tree.
- A refusal has a fault: the file's absence is `factory/pipeline.yml is missing at <ref>`; the reader's `PipelineDefinitionInvalid` carries its own fault; an `AgentDefinitionError` from `names()` is `agent home unavailable: <its fault>`; each role of `roles` whose name is not among `names()` is `role <role>: agent is not installed`, in the order of `roles`, all joined by `; `. The agents are checked only when the text itself is valid.
- For each refusal it raises `PipelineDefinitionInvalid(<the fault>)`. When `ref` is `PIPELINE_REF` it first calls `StopService.raise_stop` with `RepositoryStop(scope="repository", reason="pipeline_definition_invalid", detail=<the fault>, at=boundaries.clock.now())`. The stop goes to the health status and the factory log only. An `OSError` of the stop's writes propagates instead of `PipelineDefinitionInvalid`.
- A load that succeeds returns the definition; when `ref` is `PIPELINE_REF` it first calls `StopService.clear_stop("pipeline_definition_invalid")`. Stops of other reasons are untouched. A load at another ref raises no stop and clears none.
- A `GitError` is not a fault of the definition: it propagates and raises no stop.

Tests: `tests/application/test_pipeline_loading.py`. The loader tests use the real `GitCli` on the fixtures `remote`, `checkout` and `human` (`human.push_file(branch, path, text)` for other versions of the file, on `main` or on a branch, followed by `checkout.fetch()`), a fixture `boundaries` whose `agent_definitions` reads a directory in `tmp_path` where the helper `install_agents(agent_home, roles)` of `tests/git_support.py` writes a valid agent file for each role (S0007's loader tests use it too), and `ManualClock` through the fixture `clock`. A test that needs the file gone from `main` removes it in a second clone with `run_git` from `tests/git_support.py` and pushes.

## Acceptance criteria

1. `PipelineLoader.load()` returns the definition that `factory/pipeline.yml` holds on `origin/main`, also when the file in the work tree of the checkout has been changed (for example to another `attempts_cap`); the work tree's file is not read.
2. `load("origin/<branch>")` returns the definition of the file on that branch, which a test pushed with another `attempts_cap`.
3. A definition without `contract` on `origin/main` makes `load` raise `PipelineDefinitionInvalid` whose `fault` is `missing key: contract` (ST8.1).
4. In that case exactly one stop is raised and `boundaries.health.read().stops` holds it: `scope` `repository`, `reason` `pipeline_definition_invalid`, `detail` equal to the fault, and `at` equal to `clock.now()`; one line `<stamp> stop repository pipeline_definition_invalid: missing key: contract` was written to the factory log.
5. A refusal reaches only the health status and the factory log: `hosting.pull_requests()` is empty and nothing was posted.
6. A definition on `origin/main` without `crash_cap` (`PIPELINE_YAML` with that line removed, pushed to `main`), which writes no `lease_duration` for any role, loads with `crash_cap` 2 and `lease_duration` 60 for every role, and raises no stop (ST8.1: a missing key that has a default takes it).
7. When the file does not exist on `origin/main`, `load` raises `PipelineDefinitionInvalid` with the fault `factory/pipeline.yml is missing at origin/main`, and raises the stop with that detail.
8. A successful `load` after a refused one removes the `pipeline_definition_invalid` stop from the health status and writes the line `<stamp> stop cleared pipeline_definition_invalid`; a stop of another reason (`fetch_failed`) that was in the status stays.
9. A `GitError` from reading the file propagates from `load` and raises no stop and writes no line, both for `load()` with a `git` that fails (the `boundaries` fixture's `git` replaced with `dataclasses.replace` by a `GitCli` on a directory that does not exist) and for `load("origin/nowhere")`, a ref that does not exist.
10. When a role of `roles` has no installed agent, `load` raises `PipelineDefinitionInvalid` with the fault `role <role>: agent is not installed`, raises the stop with that detail, and names every missing role (two missing roles give two faults joined by `; ` in the order of `roles`) (ST8.3).
11. When the agent of every role is installed, `load` returns the definition and raises no stop; agents installed that no role names do not matter.
12. When `<agent_home>/agents` does not exist, `load` raises `PipelineDefinitionInvalid` whose fault starts with `agent home unavailable: `, and raises the stop with that detail.
13. A load at another ref than `origin/main` of a definition that is refused (a missing `contract` on `origin/<branch>`, and a role there without an installed agent; one test, two cases) raises `PipelineDefinitionInvalid` with the fault, and the health status and the factory log are unchanged.
14. A successful load at another ref leaves a `pipeline_definition_invalid` stop that is in the health status where it is, and writes no line.
15. When the health status cannot be written, a refused `load` of `origin/main` raises `OSError` and not `PipelineDefinitionInvalid`, and the line of the stop has been written.
16. A definition without `contract` on `origin/main`, with `<agent_home>/agents` missing, is refused with the fault `missing key: contract` alone, and the stop's detail is that fault: the agents are checked only when the text itself is valid.
17. `make check` stays green.
18. docs: `docs/operator-guide.md` explains the stop `pipeline_definition_invalid`: it is raised by the load of `origin/main` only, its detail is the fault, and it clears itself at the next successful load of `origin/main`; and it lists the faults the loader reports (the file missing, a schema fault, an agent that is not installed, the agent home unavailable); what the tick does while the stop stands is F0006's docs criterion. `docs/project-guide.md` states that only the loader raises and clears this stop and that a load at another ref changes no stop; `docs/decisions.md` records that the stop belongs to the definition on `origin/main`.

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
