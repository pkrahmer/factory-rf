---
stage: demo
pr: 134
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The preflight probes one agent run

## Assignment (as of log entry 1)

Make the preflight try what an agent run needs, once for each image build, before any work item is claimed. Two more machine items check the agent run's environment and run the agent runtime once with the factory's own arguments (questionnaire 1, Q22; F0001 decisions 17 and 18; F0005 decision 23; F0006 decision 16): the environment of the agent run (`production_environment()`, completed by `agent_run_environment`) must have a `PATH` under which the command `factory-guard` is found, because Claude Code treats a hook that cannot start as not blocking, and a `HOME` that is an existing directory, because `claude -p` finds its login there; and one `claude -p` call, made exactly as a stage makes it, must end `completed`, because a flag that the pinned `claude` rejects would make every real run end `died` with no text that says why. The probe runs the shipped agent `coder` with a budget of 0.10 dollar, a fixed one-line prompt, the decision `question` only and a time limit of 2 minutes, as the agent user, with the same environment and a guard, so that the call carries the same flags as a stage's; it costs a few cents once for each image build, because both are machine items that the stamp of the previous stories skips while the image is unchanged. A refused `sudo` shows here too, as the runtime's `AgentRuntimeError`, before any claim is pushed (an error after a claim would reach the crash path of F0008). This story also assembles every extra machine item in one place, `machine_extras`, in the order the operator guide lists them, and wires the preflight with them into `build_tick`: the token item of the token story, the agent-user item and the `sudo` tool item of the second-user stories, and the two items of this story. It covers no condition of its own: it carries F0001 decision 18's probe of the flags, which F0001 left to a morning observation, and F0001 decision 17's check of `PATH` and `HOME`, and it makes a refused `sudo` (the misconfiguration behind WE3.1) a machine stop before any claim. The real call is the morning observation.

## Interface

`src/factory/application/preflight.py` (extends the module)

```python
PROBE_AGENT = "coder"
PROBE_PROMPT = "Probe: end with the decision question and the entry probe."
PROBE_BUDGET_USD = Decimal("0.10")
PROBE_RUN_TIME_LIMIT = timedelta(minutes=2)

def agent_environment_item(
    environment: Mapping[str, str],
    find: Callable[[str, str], str | None],
    is_directory: Callable[[Path], bool],
) -> PreflightItem: ...
def agent_run_probe_item(
    boundaries: Boundaries, settings: InstanceSettings, environment: Mapping[str, str]
) -> PreflightItem: ...
```

`GUARD_COMMAND = "factory-guard"` moves from `factory.adapters.claude_runtime` to `factory.domain.agent_runs`; `claude_runtime` and this module import it from there, so the name has one definition (`CLAUDE.md`: a second copy of an existing helper is a finding, and the application layer cannot import the adapter's).

`src/factory/entry/wiring.py` (extends the module)

```python
def machine_extras(
    boundaries: Boundaries,
    settings: InstanceSettings,
    which: Callable[[str], str | None],
    environment: Mapping[str, str],
) -> list[Callable[[], PreflightItem]]: ...
```

Rules:

- `agent_environment_item(environment, find, is_directory)` is the item `agent-environment`. It passes when `environment` has a `PATH` and `find("factory-guard", <that PATH>)` finds the command, and has a `HOME` for which `is_directory(Path(<HOME>))` is true. Otherwise it fails with a detail that names each fault: the missing `PATH` or the `PATH` without `factory-guard`, the missing `HOME` or the `HOME` that is no directory.
- `agent_run_probe_item(boundaries, settings, environment)` is the item `agent-run-probe`. It reads the agent `coder` through `boundaries.agent_definitions.read(PROBE_AGENT)` and sets its `budget_usd` to `PROBE_BUDGET_USD`; it runs `boundaries.agent_runtime.run(AgentRunRequest(agent=<that agent>, prompt=PROBE_PROMPT, allowed_decisions=["question"], time_limit=PROBE_RUN_TIME_LIMIT, working_directory=boundaries.checkout, environment=<a copy of environment>, guard=GuardSettings(root=boundaries.checkout, write_paths=[], protected_paths=[]), os_user=settings.agent_user))`. It passes exactly when the end reason is `completed`. It fails, with a detail that names the end reason and says to run `claude -p` by hand as the agent user to see why, for any other end reason; it fails with the error's message for an `AgentRuntimeError` (a refused `sudo`, a state directory that cannot be written), and with the error's message for an `AgentDefinitionError` (no agent `coder` is installed). The probe writes nothing into the checkout itself; its guard gives the agent no write path.
- `machine_extras(boundaries, settings, which, environment)` returns these callables, in this order, each returning its item when called: `token_file_item(settings.token_file, uid=os.getuid(), stat=os.stat)` (named `token-file`), `agent_user_item(settings, Path.exists)` (`agent-user`), `tool_item("sudo", which)` (`tool:sudo`) only when `settings.agent_user` is not `None`, `agent_environment_item(environment, <shutil.which with a path>, Path.is_dir)` and `agent_run_probe_item(boundaries, settings, environment)`. They follow `agent-runtime-version` in the report, as the `extra` items of `MachineChecks`.
- `build_tick(boundaries, settings, which=shutil.which)` computes `environment = agent_run_environment(settings, production_environment())` once, gives it to `handler_factory(...)` and to `machine_extras(...)`, and passes `preflight=build_preflight(boundaries, settings, which, machine_extras(...))` to the `Tick`.

Tests: `tests/application/test_agent_environment_item.py`, `tests/application/test_agent_run_probe.py` (`FakeAgentRuntime` scripted `completed` and `died`, `ScriptedRun`; a `ClaudeCodeRuntime` on the stand-in of `tests/adapters/claude_stand_in.py` for the flags; a runtime double that inherits `AgentRuntime` and raises `AgentRuntimeError`), `tests/entry/test_wiring_extras.py`. From this story on `build_tick`'s preflight holds the extra items, so two earlier tests that tick through `build_tick` meet them: F0010-S0004's test of its criterion 6 (as F0010-S0010 changed it) and F0010-S0014's test of its criterion 14. The tester of this story changes those two tests and nothing else in them: `settings.token_file` names a file of the test's uid with mode 0600, `settings.agent_user` is `agent` (a token file without an agent user fails the item `agent-user`, decision 25), `settings.agent_home` is the `agent_home` fixture (the agent user's `HOME` is its parent, which the item `agent-environment` requires to be a directory), the `which` answers a path for `sudo` too (the item `tool:sudo`), a scripted `completed` run is queued for the probe before the stage's run, and the stage's request is the last of `agent_runtime.requests()`; in F0010-S0004's test that request's `environment` then equals `agent_run_environment(settings, production_environment())` instead of `production_environment()`; the human's word is in `FEATURE.md` decision 28. A test of `build_tick` or `run_instance` never starts the real `claude`: it uses `FakeAgentRuntime` or a `claude_executable` that does not exist.

## Acceptance criteria

1. `agent_environment_item` passes for a `PATH` under which `factory-guard` is found (a `find` stub backed by a dictionary) and a `HOME` that is an existing directory (a directory in `tmp_path`); its name is `agent-environment`.
2. `agent_environment_item` fails, naming `factory-guard`, for a `PATH` under which it is not found, and fails, naming `PATH`, for an environment without a `PATH`.
3. `agent_environment_item` fails, naming `HOME`, for an environment without a `HOME` and for a `HOME` that is not a directory (two cases).
4. `agent_run_probe_item` passes when the agent runtime is scripted to end `completed`, and its name is `agent-run-probe`.
5. The request the probe makes has the prompt `PROBE_PROMPT`, the allowed decisions `["question"]`, a `time_limit` of 2 minutes, the working directory `boundaries.checkout`, an `environment` equal to the one given, `os_user` equal to `settings.agent_user`, a guard with root `boundaries.checkout`, no write paths and no protected paths, and the agent `coder` with its own model and tools and a `budget_usd` of `0.10`.
6. `agent_run_probe_item` fails, with a detail that contains `died` and `claude -p`, when the agent runtime is scripted to end `died`.
7. `agent_run_probe_item` fails, naming the end reason, for each of `no_result`, `time_limit` and `budget`.
8. `agent_run_probe_item` fails, with a detail that contains the error's message, when the agent runtime raises `AgentRuntimeError("sudo: a password is required")`: a refused `sudo` is a machine fault found before any claim.
9. `agent_run_probe_item` fails, naming the agent, when no agent `coder` is installed.
10. The probe's call carries the same flags as a stage's: with `ClaudeCodeRuntime` on the stand-in, the arguments of the probe's call and of a call for a request built like a stage's (the agent `coder`, a guard, the decisions `review` and `question`) hold the same flags, the arguments that start with `--`, in the same order.
11. Both items are machine items: under `Preflight`, two `run()` calls with the same non-`None` image make the agent runtime run the probe once.
12. `machine_extras` for settings without an agent user returns callables whose items are named `token-file`, `agent-user`, `agent-environment` and `agent-run-probe`, in this order.
13. `machine_extras` for settings with `agent_user == "agent"` returns callables whose items are named `token-file`, `agent-user`, `tool:sudo`, `agent-environment` and `agent-run-probe`, in this order.
14. A `Tick` from `build_tick(boundaries, settings, which)` over a remote with one started story and a `Makefile` on `main` whose target `lint` is `true`, with `settings.agent_user == "agent"` (a token file without an agent user fails the item `agent-user`, `FEATURE.md` decision 25), `settings.agent_home` equal to the `agent_home` fixture and `settings.state_directory` in `tmp_path`, a `which` that answers a path for every tool, `sudo` included, agents installed, a runtime reporting the pinned version and a scripted `completed` probe, but a token file that does not exist, returns `TickOutcome(stopped="preflight_failed")` and the stop's detail names `token-file`; with a token file of the test's uid and mode 0600 instead, the tick passes the preflight, and the probe's request and the stage's request carry the same `environment`.
15. make check stays green.
16. docs: `docs/operator-guide.md` lists the preflight's items in the order the report gives them (the seven of the items story, then `token-file`, `agent-user`, `tool:sudo` when an agent user is set, `agent-environment` and `agent-run-probe`) with the fix for each, says that the probe makes one `claude -p` call of at most 0.10 dollar once for each image build and what a failure of it means (a flag the pinned `claude` rejects, a login missing for the agent user, a refused `sudo`), and that `PATH` must hold `factory-guard` and `HOME` must exist; `docs/decisions.md` records why the preflight runs the factory's own arguments once for each image build (questionnaire 1, Q22) and why a refused `sudo` is found by the probe before any claim.

## Demo

```bash
uv run python -c "
import pathlib, tempfile
from factory.application.preflight import agent_environment_item
home = tempfile.mkdtemp()
found = lambda name, path: '/bin/factory-guard' if '/bin' in path.split(':') else None
print(agent_environment_item({'PATH': '/bin:/usr/bin', 'HOME': home}, found, pathlib.Path.is_dir).passed)
item = agent_environment_item({'PATH': '/usr/bin', 'HOME': '/nonexistent'}, found, pathlib.Path.is_dir)
print(item.name, item.passed, 'factory-guard' in item.detail, 'HOME' in item.detail)
"
```
Expect: two lines, `True` and `agent-environment False True True`.

```bash
uv run python -c "
from factory.application.preflight import PROBE_AGENT, PROBE_BUDGET_USD, PROBE_RUN_TIME_LIMIT
print(PROBE_AGENT, PROBE_BUDGET_USD, PROBE_RUN_TIME_LIMIT.total_seconds())
"
```
Expect: one line, `coder 0.10 120.0`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures (preflight.py constants and the two item functions, wiring.py `machine_extras`, the `build_tick` change, the `GUARD_COMMAND` move to `factory.domain.agent_runs`). Every behaviour in the rules is spelled out: item names, the order of the extras, the `sudo` item only with an agent user, the probe's request fields.
   - Criteria: each is testable by one test function. Every rule has its failing side. Environment: a missing PATH, PATH without factory-guard, a missing HOME and a HOME that is no directory (criteria 2 and 3). Probe: `died`, `no_result`, `time_limit`, `budget`, `AgentRuntimeError` and a missing `coder` (criteria 6 to 9). Extras: with and without an agent user (criteria 12 and 13). Tick: a missing token file stops it, a valid one passes (criterion 14). The machine-item skip is criterion 11 and the flag parity is criterion 10. Criterion 14 holds two scenarios and the tester can write them as two cases of one parametrized test.
   - Demo: both blocks are runnable with `uv run python -c`, and each Expect line is checkable against the output (`True` / `agent-environment False True True`, and `coder 0.10 120.0`).
   - Architecture: the items live in application, the wiring in entry, and the shared constant moves down to domain so application does not import the adapter. This matches the layer rules in CLAUDE.md. Items use the existing wrappers and interfaces (AgentRuntime, AgentDefinitions), with no new tool or dependency.
   - Scope: within the feature's scope (the preflight's items and the probe with the factory's own arguments). It matches decisions 20, 22, 25, 28 and 31. The two changes to earlier tests are the ones the human allowed in decision 28.
3. tester: Wrote the red tests for every acceptance criterion, and changed the two earlier build_tick tests that FEATURE.md decision 28 allows.

   Criterion → test:
   - criterion 1: tests/application/test_agent_environment_item.py::test_a_path_holding_factory_guard_and_an_existing_home_pass
   - criterion 2: tests/application/test_agent_environment_item.py::test_a_fault_in_the_environment_fails_naming_it, rows path-without-factory-guard and no-path
   - criterion 3: the same test, rows no-home and home-not-a-directory (HOME is a regular file)
   - criterion 4: tests/application/test_agent_run_probe.py::test_a_completed_probe_passes
   - criterion 5: tests/application/test_agent_run_probe.py::test_the_probe_runs_the_coder_on_a_small_budget_with_the_question_alone
   - criteria 6 and 7: tests/application/test_agent_run_probe.py::test_a_probe_that_does_not_complete_fails_naming_its_end_and_claude_p, one parametrized test over died, no_result, time_limit and budget. Every row checks that the detail names the end reason and contains `claude -p`, because the Interface rule asks for both on any end reason other than completed.
   - criterion 8: tests/application/test_agent_run_probe.py::test_a_runtime_that_cannot_run_the_probe_fails_with_its_message. The double is RefusingRuntime, which inherits AgentRuntime.
   - criterion 9: tests/application/test_agent_run_probe.py::test_a_missing_coder_fails_the_probe_naming_the_agent
   - criterion 10: tests/application/test_agent_run_probe.py::test_the_probe_calls_claude_with_the_flags_of_a_stage. It runs ClaudeCodeRuntime on the claude stand-in with no agent user, then compares the `--` arguments of the probe's call with those of a stage-like call (coder, a guard, decisions review and question).
   - criterion 11: tests/application/test_agent_run_probe.py::test_the_probe_runs_once_for_each_image_build. Both items go in as extras under Preflight. Two run() calls with image build-7 give exactly one runtime request and one `find` call.
   - criteria 12 and 13: tests/entry/test_wiring_extras.py::test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user, with rows no-agent-user and agent-user.
   - criterion 14: tests/entry/test_wiring_extras.py::test_a_tick_stops_on_a_failed_extra_and_otherwise_probes_in_the_stages_environment, with rows no-token-file and token-file. The token file is written in tmp_path with mode 0600, so it belongs to the test's uid.

   Changes to earlier tests, as the Assignment specifies:
   - tests/entry/test_wiring_run.py::test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance: the settings now have a 0600 token file and agent_user "agent". A completed probe run is queued before the stage's run. The stage's request is `requests()[-1]`, and its environment must equal `agent_run_environment(ready, production_environment())`.
   - tests/entry/test_wiring_agent_user.py::test_a_tick_with_an_agent_user_runs_the_agent_as_that_user_in_its_home: a 0600 token file is added, a completed probe run is queued first, and the stage's request is `requests()[-1]`.
   - In both, agent_home was already the fixture and the `which` (`_every_tool`) already answers for sudo.

   Files created: tests/application/test_agent_environment_item.py, tests/application/test_agent_run_probe.py, tests/entry/test_wiring_extras.py. Files changed: tests/entry/test_wiring_run.py, tests/entry/test_wiring_agent_user.py.

   `make test` stops with 3 collection errors, in the three new files, because the names under test do not exist yet: `agent_environment_item`, `agent_run_probe_item` and `PROBE_PROMPT` in factory.application.preflight, and `machine_extras` in factory.entry.wiring. The two changed tests did not run, because collection stopped the run. `make lint` is green.

   Open for the coder:
   - The criterion 14 test and the changed test_wiring_run test depend on the venv's `factory-guard` being on the production PATH (the interpreter's directory). Its HOME is the agent home's parent, tmp_path.
   - test_wiring_preflight.py was left as it is. Its preflight fails at tool:git anyway, and the probe there fails with the fake's "no scripted run is queued".

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Made the tester's red tests pass without changing them. `make check` is green (coverage 99.54 %). The commit is "feat(preflight): probe the agent run's environment and one claude -p call".

   What I built:
   - src/factory/domain/agent_runs.py: `GUARD_COMMAND = "factory-guard"` moved here from src/factory/adapters/claude_runtime.py, which now imports it. The name has one definition.
   - src/factory/application/preflight.py: the constants `PROBE_AGENT`, `PROBE_PROMPT`, `PROBE_BUDGET_USD` and `PROBE_RUN_TIME_LIMIT`, and two items.
     - `agent_environment_item`: the private helpers `_path_fault` and `_home_fault` each return a fault or `None`. The item fails with every fault joined by "; ", so one detail names all of them.
     - `agent_run_probe_item`: reads `coder`, lowers its `budget_usd` with `model_copy`, and runs one request through `_probe_request`. That request has `allowed_decisions=[QUESTION]`, a copy of the environment, a guard with no write or protected paths, and `os_user=settings.agent_user`. `AgentDefinitionError` and `AgentRuntimeError` fail the item with `str(error)`, so the agent's name or the sudo message appears in the detail. Any end reason other than `completed` fails with "the probe run ended <reason>; run claude -p by hand as <agent user or the factory user> to see why".
   - src/factory/entry/wiring.py:
     - `machine_extras` returns the lambdas in the order token-file, agent-user, tool:sudo (only when there is an agent user), agent-environment, agent-run-probe. The private `_which_on(name, path)` adapts `shutil.which(name, path=path)` to the `find` signature.
     - `build_tick` computes the agent-run environment once and gives it to both `handler_factory` and `machine_extras`, then passes the extras to `build_preflight`.

   Main decision: the extras are plain closures over the boundaries and settings. Their callers give `MachineChecks` the `extra` sequence that already existed. I rejected adding them as methods on `MachineChecks`, because the Interface gives the items as functions and wiring owns `os.getuid`/`os.stat`/`shutil.which`.

   Refactor: I read the diff and found nothing to change, so there is no separate refactor commit.

   Noticed, not touched: as the tester noted, test_wiring_preflight.py still fails at tool:git before it reaches the extras. Docs (criterion 16) are left to the documenter.

   `make check`: check: green
5. reviewer: No findings.

   What I checked:
   - Acceptance criteria 1 to 14: each has a test that checks what its criterion says.
     - `tests/application/test_agent_environment_item.py` covers criterion 1 with its pass case. Criteria 2 and 3 are four parametrized rows: a PATH without factory-guard, no PATH, no HOME, and a HOME that is a regular file.
     - `tests/application/test_agent_run_probe.py` covers criteria 4 to 11:
       - the request fields, including the coder's own model and tools and the 0.10 budget;
       - `died`, `no_result`, `time_limit` and `budget` as rows of one test, each checking the end reason and `claude -p`;
       - the `AgentRuntimeError` raised by a double that inherits `AgentRuntime`;
       - a missing `coder`;
       - the `--` flags of the probe and of a stage-like call, compared on the stand-in;
       - the machine-item skip: two `run()` calls give one request and one `find`.
     - `tests/entry/test_wiring_extras.py` covers the order of the extras with and without an agent user (criteria 12 and 13). For criterion 14 it has a no-token-file row (the stop names `token-file`) and a token-file row (the probe and the stage have the same environment).
     - The tester changed the two earlier `build_tick` tests (`test_wiring_run.py`, `test_wiring_agent_user.py`) only as the Assignment and FEATURE.md decision 28 allow.
     - The coder's entry reports `make check` green.
   - Architecture:
     - `GUARD_COMMAND` now has one definition, in `factory.domain.agent_runs`. `claude_runtime` and `preflight` both import it from there.
     - The two items in `factory.application.preflight` import only the application and domain layers.
     - `os.getuid`, `os.stat` and `shutil.which` are called only in `factory.entry.wiring` (`machine_extras`, `_which_on`).
     - `build_tick` computes the agent-run environment once and passes it to both `handler_factory` and `machine_extras`.
     - The extras reach `MachineChecks` through the `extra` parameter that already existed in `build_preflight`.
   - Security: no new markers, secrets, shell strings or dependencies. The probe's guard has no write paths and no protected paths. An error fails the item with the error's own message, as the Interface asks.
   - Quality:
     - Names follow the module's existing `_..._ITEM` style.
     - `_path_fault` and `_home_fault` each check one thing. Their faults are joined, so one detail names every fault.
     - Comments explain why (a guard that cannot start does not block; a rejected flag ends every run `died`), and the new public names have docstrings.
     - No duplicate helper: `_which_on` only adapts `shutil.which` to the `find` signature.
   - Ticket hygiene: the coder's entry gives the main decision (closures over the boundaries and settings, fed to `MachineChecks.extra`) and what was rejected (methods on `MachineChecks`). The Assignment matches what was built. Criterion 16 (docs) still names the operator guide's order of items, the probe's cost and failure meanings, and the two decision-log reasons.
6. documenter: Wrote the documentation for criterion 16. No findings: the diff matches the Interface. `make check` is green.

   Files changed:
   - docs/operator-guide.md:
     - The preflight's items table now follows the report's order: the seven earlier items, then `token-file`, `agent-user`, `tool:sudo` (only with an agent user), `agent-environment` and `agent-run-probe`, each with its fix.
     - The "built, not yet run" and "wiring comes later" sentences are removed, and the item count is corrected.
     - A new section, "The probe of the agent run", covers the one `claude -p` call of at most 0.10 dollar once for each image build. It gives the failure meanings: a rejected flag, a missing login for the agent user, a refused `sudo`, an unwritable state directory, a missing `coder`.
     - It says `PATH` must hold `factory-guard` and `HOME` must exist.
     - The stale lines in the opening paragraph, the "flags not yet checked" paragraph and the `factory-guard` paragraph are fixed.
   - docs/decisions.md: a new entry on why the preflight runs the factory's own arguments once for each image build (Q22, F0001 decisions 17 and 18) and why a refused `sudo` is found by the probe before any claim. It records the rejected alternatives: leaving it to the first stage run, and probing only `claude --version`.
   - docs/project-guide.md: the tick's preflight step now names `machine_extras`, the two new items, `GUARD_COMMAND`'s new home and the extras' order. The `token_file_item` sentence now says it has a caller.
   - README.md: the "preflight still to come" sentence is replaced with the current state.

   Cross-read and found current: the project guide's guard and environment sections, and the operator guide's stamp/probe and stops sections.

   Not run: the two demo blocks from the ticket. Nothing stale and unrelated was seen that I left untouched.

   `make check`: check: green
