---
stage: docs
pr: 45
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
2. intake: accepted
   - Interface: `src/factory/application/pipeline_loading.py` names `PIPELINE_REF`, `PipelineLoader.__init__(boundaries)` and `load(ref)`. It also names the Boundaries members it uses (git.show_file, pipeline_reader, agent_definitions, clock, health) and the exact fault texts.
   - Criteria: each one is testable by one test function. Every Interface rule has a criterion for its passing and its failing side:
     - Reading at a ref: 1 and 2.
     - Missing key, with a default taken instead: 3 and 6.
     - Missing file: 7.
     - Missing or unavailable agents: 10, 11 and 12.
     - Stop raised at `origin/main` only: 4, 13 and 14.
     - Stop cleared on success: 8.
     - `GitError` propagating: 9.
     - Failure of the health write: 15.
     - Agents checked only after the text is valid: 16.
     - Only the log and health status written: 5.
   - Demo: the stub git, the agents directory and the Boundaries wiring are runnable. The Expect line gives the five lines, with the stamp form, that the output can be checked against.
   - Architecture: the loader sits in `factory.application` and reaches git, the readers, the clock and the health status through `Boundaries`. It calls no tool itself.
   - Scope: the story stays inside FEATURE.md's scope (`PipelineLoader`, the installed-agent check, the reported stop). The cross-key rules are left to S0007, and the tick's use of `load` to F0006.
3. tester: Wrote the loader tests from the Interface and criteria 1–16. Criterion → test (all in tests/application/test_pipeline_loading.py):
   - Interface `PIPELINE_REF`: test_the_pipeline_ref_is_main_on_the_remote
   - criterion 1: test_load_reads_main_on_the_remote_not_the_work_tree
   - criterion 2: test_load_at_a_branch_reads_the_file_on_that_branch
   - criterion 3: test_a_definition_without_contract_is_refused_with_its_fault
   - criterion 4: test_a_refusal_raises_one_stop_and_writes_its_line
   - criterion 5: test_a_refusal_opens_no_pull_request_and_posts_nothing. There are no pull requests, so nothing can have been posted.
   - criterion 6: test_a_missing_key_with_a_default_takes_the_default
   - criterion 7: test_a_definition_missing_on_main_is_refused_and_stops. The file is removed in a second clone with `run_git` and pushed.
   - criterion 8: test_a_successful_load_clears_the_stop_and_keeps_other_stops. The first load is refused because no agents are installed. Installing them makes the next load succeed.
   - criterion 9: test_a_git_error_propagates_and_raises_no_stop, with two cases: a `GitCli` on a directory that does not exist, and `origin/nowhere`.
   - criterion 10: test_roles_without_an_installed_agent_are_refused_in_role_order, with two cases: one missing role, and two missing roles in the order of `roles`.
   - criterion 11: test_installed_agents_for_every_role_load_and_extra_agents_do_not_matter
   - criterion 12: test_an_unavailable_agent_home_is_refused_and_stops
   - criterion 13: test_a_refusal_at_another_ref_raises_but_changes_no_stop, with two cases: a missing `contract`, and an agent that is not installed.
   - criterion 14: test_a_successful_load_at_another_ref_leaves_the_stop_in_place
   - criterion 15: test_an_unwritable_health_status_raises_os_error_after_the_stop_line. A local `HealthStatusStore` refuses every write.
   - criterion 16: test_the_agents_are_checked_only_when_the_text_is_valid

   Files:
   - Created tests/application/test_pipeline_loading.py.
   - Extended tests/git_support.py with `AGENT_FILE` and `install_agents(agent_home, roles)`. The Interface names this helper for S0005's and S0007's loader tests.

   `make test` stops at collection: `ModuleNotFoundError: No module named 'factory.application.pipeline_loading'`. That is the only module that could not be imported. `make lint` is green. No criterion needed interpreting.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built `PipelineLoader` in src/factory/application/pipeline_loading.py (commit 78bd024). `make check` is green and all tests in tests/application/test_pipeline_loading.py pass.
   - `PIPELINE_REF` is built from `REMOTE` and `MAIN_BRANCH` of factory.domain.paths.
   - `load(ref)` works in this order:
     1. It reads the file with `git.show_file`. `None` is turned into the fault `factory/pipeline.yml is missing at <ref>`.
     2. It parses the text with `pipeline_reader.parse`.
     3. Only then does it check the agents. An `AgentDefinitionError` from `names()` becomes `agent home unavailable: <error.fault>`. Each role in `roles` that is not installed gives one fault, in role order, joined by `; `.
   - The stop is handled in one place in `load`. When `ref == PIPELINE_REF`, a `PipelineDefinitionInvalid` first calls `StopService.raise_stop` and is then re-raised; an `OSError` from the stop's writes propagates in its place. A success at that ref calls `clear_stop("pipeline_definition_invalid")`.
   - `GitError` is not caught, so it propagates and raises no stop.

   Design decision: the reading and checking live in a private `_read`, and the stop is decided once in `load` around that one call. I rejected raising the stop at each refusal site: that would repeat the ref check three times and make it easy to miss a site.

   Refactor pass: I read the diff and found nothing to change, so there is no separate refactor commit.

   Not touched: nothing noticed outside the ticket.

   `make check`: check: green
5. reviewer: no findings.
   - Acceptance criteria: every one of criteria 1–16 has a matching test in tests/application/test_pipeline_loading.py, and each test checks its criterion. The coder's entry reports `make check` green.
     - Work tree versus `origin/main`: criterion 1 edits the checkout's work-tree file, criterion 2 pushes to a branch.
     - Stop raised once with the correct `at` and log line: criterion 4 advances the clock by 5 s first.
     - Nothing posted: criterion 5. The fake only posts on an existing pull request, so an empty `pull_requests()` also means nothing was posted.
     - Default taken: criterion 6. `crash_cap: 2\n` is present in PIPELINE_YAML and no role sets `lease_duration`.
     - Clear keeps other stops: criterion 8 keeps `fetch_failed`.
     - `GitError` cases: criterion 9 covers both, a missing directory and an unknown ref.
     - Role order with two missing roles: criterion 10.
     - Both sides of the `ref == PIPELINE_REF` rule: refusal raises the stop (4, 7, 10, 12) and success clears it (8); at another ref neither happens (13, 14).
     - `OSError` from the stop's writes, after the stop line: criterion 15.
     - Agents checked only when the text is valid: criterion 16.
   - Architecture: src/factory/application/pipeline_loading.py imports only factory.application and factory.domain. It reaches git, the readers, the clock, the log and the health status through `Boundaries` and `StopService`, and calls no tool.
   - Security: no secrets, no suppression markers, no command or SQL built from strings.
   - Quality: one design point. `load` decides the stop once, around the private `_read`. `GitError` is not caught, so it propagates without a stop. The module, class and public-method docstrings are present and say what each one does. The test helper `install_agents` in tests/git_support.py is small and named by the Interface.
   - Ticket hygiene: the coder's entry states the main decision and the alternative rejected (raising the stop at each refusal site). The Assignment matches what was built. Criterion 18 still describes what the operator guide, the project guide and the decision log need.
