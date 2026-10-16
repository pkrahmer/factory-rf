---
stage: done
pr: 129
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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
2. intake: accepted
   - Interface: names concrete modules and signatures (`domain/agent_runs.py` constants, `adapters/agent_files.py` reader, `application/pipeline_loading.py` loader, `application/tick.py` `Tick._load`, `entry/watch.py` `run_watch`) and states the error's name, key, fault and message, the check order, case-sensitivity and the stop's detail format.
   - Criteria: 20 criteria, each testable by one test function. Every Interface rule has its failing side. Unapplied keys are refused (3, 4). The unapplied key takes precedence over a missing model or a bad budget (6, 7). The first key in file order is named (5, 9). The other checks come first (10). Other refs touch no stop (14). Files with only applied keys are read (2). Success clears the stop (12, 17). The earlier `pipeline_definition_invalid` is cleared (13). Criterion 3 says "first six" but lists seven keys; the list is explicit, so I did not treat it as a finding.
   - Demo: both blocks are runnable with `uv run python -c`, and each `Expect:` line is an exact output line that can be checked.
   - Architecture: the constants are in domain, the file reader is in adapters, the loader and tick are in application, and `run_watch` is in entry. Layer direction holds, and the reader replaces its private tuple with the domain constant.
   - Scope: within the feature's scope ("Agent files without dead keys, refused at load as a reported stop raised by the pipeline loader"). The shipped agents and SI4.2 are left to S0012, which matches Out of scope. The deletion of F0003's `colour` test is covered by FEATURE.md decision 28(1).
3. tester: Wrote red tests for criteria 1–18. Criteria 19 and 20 are the check and docs criteria, so no test covers them.

   - criterion 1: tests/adapters/test_agent_file_keys.py::test_the_applied_keys_are_model_tools_effort_and_budget (it also checks the text of `KEY_NOT_APPLIED`)
   - criterion 2: tests/adapters/test_agent_file_keys.py::test_a_file_with_only_applied_keys_is_read
   - criterion 3: tests/adapters/test_agent_file_keys.py::test_a_key_the_runner_does_not_apply_is_refused (one row per key: name, description, permissionMode, hooks, background, disallowedTools, skills)
   - criterion 4: tests/adapters/test_agent_file_keys.py::test_an_unknown_key_or_a_key_in_another_case_is_refused (rows `colour` and `Model`)
   - criterion 5: tests/adapters/test_agent_file_keys.py::test_the_first_unapplied_key_in_the_file_is_named
   - criteria 6 and 7: tests/adapters/test_agent_file_keys.py::test_an_unapplied_key_is_refused_before_the_applied_keys_are_validated (rows no-model and budget-zero: one rule, so one parametrized test)
   - criterion 8: tests/application/test_pipeline_loading_agents.py::test_the_agent_file_of_a_later_role_is_read_too
   - criterion 9: tests/application/test_pipeline_loading_agents.py::test_of_two_refused_agent_files_the_first_role_is_named
   - criterion 10: tests/application/test_pipeline_loading_agents.py::test_a_missing_agent_is_refused_before_any_agent_file_is_read
   - criterion 11: tests/application/test_pipeline_loading_agents.py::test_a_refused_agent_file_on_main_raises_one_stop
   - criterion 12: tests/application/test_pipeline_loading_agents.py::test_a_good_load_on_main_clears_the_agent_stop
   - criterion 13: tests/application/test_pipeline_loading_agents.py::test_a_refused_agent_file_after_a_refused_definition_leaves_only_the_agent_stop
   - criterion 14: tests/application/test_pipeline_loading_agents.py::test_a_refused_agent_file_at_a_commit_leaves_the_health_status_as_it_was (an agent stop already raised on main stays exactly as it was, so the test covers both "none raised" and "none cleared")
   - criterion 15: tests/application/test_tick_agent_definition.py::test_the_tick_ends_at_the_agent_stop
   - criterion 16: tests/application/test_tick_agent_definition.py::test_the_stopped_tick_requests_no_run_and_dispatches_nothing
   - criterion 17: tests/application/test_tick_agent_definition.py::test_after_the_file_is_corrected_the_next_tick_runs_the_stage
   - criterion 18: tests/entry/test_watch_agent_definition.py::test_a_refused_agent_file_is_reported_without_a_stop

   The "two roles" of criteria 8–10 are `tester` and `coder` from the shared `PIPELINE_YAML`, with every other role's agent file valid. `tester` comes first in `roles`, which is the reverse of alphabetical order, so a check that read the roles in alphabetical order would fail. The tick tests use the `coder` role, the story from `tests/entry/test_run.py` started through `human.push_file` and `human.start`, and `handler_factory` with a PATH and HOME environment.

   Files created: tests/adapters/test_agent_file_keys.py, tests/application/test_pipeline_loading_agents.py, tests/application/test_tick_agent_definition.py, tests/entry/test_watch_agent_definition.py.

   Files changed:
   - tests/adapters/test_agent_files.py: deleted `test_a_key_the_reader_does_not_interpret_is_left_aside`, as the Assignment says.
   - tests/git_support.py: added `COLOURED_AGENT_FILE` (the shared agent file plus `colour: red`) and `write_agent(agent_home, role, text)`. `install_agents` now writes through `write_agent`.

   `make test`: collection stops at tests/adapters/test_agent_file_keys.py with `ImportError: cannot import name 'APPLIED_AGENT_KEYS' from 'factory.domain.agent_runs'`, the expected reason. That error stops collection, so this run did not show the other three new files failing. They import only names that already exist, so they should fail on wrong results once collection gets through. `make lint` is green. The type check was skipped, as the stage says.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Made criteria 1–18 pass without changing any test. `make check` is green (coverage 99.53 %). Commits: f714e10 (feat) and 109748d (refactor).

   Built:
   - `src/factory/domain/agent_runs.py`: added `APPLIED_AGENT_KEYS` and `KEY_NOT_APPLIED`.
   - `src/factory/adapters/agent_files.py`: the private `_INTERPRETED_KEYS` tuple is gone. A new `_refuse_unapplied_keys` goes through the front matter in the file's order and raises `AgentDefinitionInvalid(name, "key not applied by the agent runtime: <key>", key)` at the first key outside `APPLIED_AGENT_KEYS`. It runs before `AgentDefinition.model_validate`, so a dead key wins over a missing `model` or a bad budget. Once every key is known to be applied, the front matter goes to the model as a whole instead of filtered.
   - `src/factory/application/pipeline_loading.py`: `load` now does two steps. `_load_definition` is the old behaviour: the `pipeline_definition_invalid` stop, cleared before the agent files are read. `_check_agent_files` then reads every role in the order of `roles`. When a file is refused it raises `agent_definition_invalid` with the detail `<name>: <fault>`, and a good load clears that stop. Both stops are touched only at `PIPELINE_REF`. `_stop` now takes the reason as a parameter.
   - `src/factory/application/tick.py`: `_load` turns `AgentDefinitionInvalid` into `_Stopped("agent_definition_invalid")`.
   - `src/factory/entry/watch.py`: writes `factory-watch: <str(error)>`, which gives `agent <name>: <fault>`, and returns 1, the same exit code as an invalid definition.

   Main decision: the agent files are read in a separate step after the definition step, not inside `_read`/`_require_agents`. That way the loader can clear `pipeline_definition_invalid` before the agent check, as criterion 13 requires, and each refusal sits next to the stop it raises. I rejected wrapping `AgentDefinitionInvalid` into `PipelineDefinitionInvalid`, because the Interface requires the agent error itself to reach the caller.

   Refactor: split `load` into one helper per stop (109748d). Behaviour is unchanged.

   Noticed, not touched: `run_watch` returns the same exit code 1 for both refusals, which matches the Interface. The docs criterion (20) is left for the documenter. The `Assignment` is unchanged.

   `make check`: check: green
5. reviewer: no findings.

   Checked against the ticket and `git diff main...HEAD -- . ':!factory'`. I did not use the ticket's own account of the work.

   - Acceptance criteria: criteria 1–18 each have a test that checks what it is named after:
     - Criteria 3 and 4 are parametrized, one row per dead key plus `colour` and `Model`.
     - Criteria 6 and 7 are rows of one parametrized test, because they are one rule.
     - Criterion 9's roles are ordered against the alphabet.
     - Criterion 14 starts from an existing agent stop, so the test covers both "none raised" and "none cleared".
     - Criterion 16 checks that no run is requested, no event is returned, no dispatch happens and no pull request is opened.

     Every rule in the Interface has its failing side tested:
     - case-sensitivity: `Model`;
     - check order: no `model`, and `budget_usd: 0`;
     - other checks come first: criterion 10;
     - another ref touches no stop: criterion 14.

     The deleted `colour` test is the one the Assignment names. The coder's entry reports `make check` green (99.53 %).
   - Architecture: the constants are in domain, the key check is in the adapter reader, and the stop handling is in the application loader, the one place that raises and clears the definition's stops. The tick and watch only turn the error into their outcome. Layer direction holds and nothing new wires.
   - Security: no suppression markers. The agent name is still validated before any path is built. Keys are stringified by the YAML handler, so `key` stays a `str`.
   - Quality: `_refuse_unapplied_keys` replaces the private tuple with `APPLIED_AGENT_KEYS`. `_load_definition` and `_check_agent_files` each own one stop. `_stop` is generalized over the reason rather than copied. The comments explain why, and the docstrings of `PipelineLoader` and `load` were updated for the second stop. `write_agent` in `tests/git_support.py` is reused by `install_agents`, not duplicated.

     A side effect worth knowing: any `AgentDefinitionInvalid` met at load (no front matter, bad budget) now raises `agent_definition_invalid`, not only an unapplied key. This matches the Interface ("an `AgentDefinitionInvalid` it meets is raised to the caller").
   - Ticket hygiene: the coder's entry names the main decision (a separate agent-file step after the definition step) and the rejected alternative (wrapping the error in `PipelineDefinitionInvalid`). The Assignment matches what was built. Criterion 20 still describes what the documenter must write.
6. documenter: wrote the documentation for criterion 20 and fixed the places that said other agent-file keys were ignored. No findings. `make check` is green (coverage 99.53 %). I ran the first demo block and it printed `permissionMode | coder | True`, plus the error message.

   Files changed:
   - `docs/operator-guide.md`:
     - "The agent files": the four keys are the only ones applied, and any other key (including a key in another case) is refused at load. Added the fault `key not applied by the agent runtime: <key>`, and the order of faults now puts it first.
     - New section "The stop `agent_definition_invalid`": the detail format, a log example, and that the operator fixes the named file in the agent home. The tick does nothing else while the stop holds, and a missing agent still shows as `pipeline_definition_invalid`.
     - "The stops of the tick": now four stops, with a row for the new one. The stops table in the health section also has a row for it.
     - `factory-watch` exit status 1: now also covers a refused agent file, and the message is `factory-watch: agent <name>: <fault>`.
   - `docs/project-guide.md`:
     - The agent file section: the four applied keys, what each does, and the refusal rules. Keys are compared as written. The refusal comes before the validation of the applied keys.
     - The faults table: added a row for the unapplied key, and removed the stale pointer to F0010-S0006.
     - The loader section: it reads every role's agent file after clearing `pipeline_definition_invalid`. It raises and clears `agent_definition_invalid`, and passes the error through unwrapped.
     - The tick step 2 now names both outcomes.
   - `docs/decisions.md`: rewrote the entry "Agent files: keys beyond the four are not interpreted until F0010". It is now "the four keys are applied, every other key is refused at load", with the reason and the alternatives rejected.

   Cross-read and found current: README (it has nothing on agent files) and the rest of the operator guide, including the health status reasons list, which already named `agent_definition_invalid`.

   Left alone because they are unrelated to this story: nothing stale seen.

   Details of the docs that rest on the code diff:
   - The loader raises the stop for any `AgentDefinitionInvalid`, not only an unapplied key. The reviewer noted this and the Interface allows it, so I documented it as it is.
   - `docs/project-guide.md` describes what `effort` and `budget_usd` do from the existing runner section (`--effort`, `--max-budget-usd`).

   `make check`: check: green
7. demo: both commands met their `Expect:` lines. No findings.

   1. A file with `permissionMode` among applied keys is refused.
   ```
   permissionMode | coder | True
   ```
   Exit 0. Matches `permissionMode | coder | True`: the error's `key` is the unapplied key, its `name` is the agent, and the message contains the key (criterion 3).

   2. A file with only the four applied keys is read.
   ```
   ['budget_usd', 'effort', 'model', 'tools'] opus medium 4
   ```
   Exit 0. Matches `['budget_usd', 'effort', 'model', 'tools'] opus medium 4`: `APPLIED_AGENT_KEYS` is exactly the four keys (criterion 1) and the file's values are read (criterion 2).

   Cross-check against the acceptance criteria: the output contradicts none of them. The demo exercises only the reader. Criteria 4–18 (loader, stops, tick, watch) are not demonstrated here; they rest on the tests listed in the tester's entry and the green `make check` reported by the coder and the documenter.
8. done (pull request merged); cost: 6 runs, 15.9 min, 66 turns, 192k tokens in (1731k more from cache), 35k out, $2.25
