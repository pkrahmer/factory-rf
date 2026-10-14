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
GUARD_COMMAND = "factory-guard"

def agent_environment_item(
    environment: Mapping[str, str],
    find: Callable[[str, str], str | None],
    is_directory: Callable[[Path], bool],
) -> PreflightItem: ...
def agent_run_probe_item(
    boundaries: Boundaries, settings: InstanceSettings, environment: Mapping[str, str]
) -> PreflightItem: ...
```

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
- `agent_run_probe_item(boundaries, settings, environment)` is the item `agent-run-probe`. It reads the agent `coder` through `boundaries.agent_definitions.read(PROBE_AGENT)` and sets its `budget_usd` to `PROBE_BUDGET_USD`; it runs `boundaries.agent_runtime.run(AgentRunRequest(agent=<that agent>, prompt=PROBE_PROMPT, allowed_decisions=["question"], time_limit=PROBE_RUN_TIME_LIMIT, working_directory=boundaries.checkout, environment=<a copy of environment>, guard=GuardSettings(root=boundaries.checkout, write_paths=[], protected_paths=[]), os_user=settings.agent_user))`. It passes exactly when the end reason is `completed`. It fails, with a detail that names the end reason and says to run `claude -p` by hand as the agent user to see why, for any other end reason; it fails with the error's message for an `AgentRuntimeError` (a refused `sudo`, a state directory that cannot be written), and with the error's message for an `AgentDefinitionError` (no agent `coder` is installed). The probe changes nothing in the checkout.
- `machine_extras(boundaries, settings, which, environment)` returns these callables, in this order, each returning its item when called: `token_file_item(settings.token_file, uid=os.getuid(), stat=os.stat)` (named `token-file`), `agent_user_item(settings, Path.exists)` (`agent-user`), `tool_item("sudo", which)` (`tool:sudo`) only when `settings.agent_user` is not `None`, `agent_environment_item(environment, <shutil.which with a path>, Path.is_dir)` and `agent_run_probe_item(boundaries, settings, environment)`. They follow `agent-runtime-version` in the report, as the `extra` items of `MachineChecks`.
- `build_tick(boundaries, settings, which=shutil.which)` computes `environment = agent_run_environment(settings, production_environment())` once, gives it to `handler_factory(...)` and to `machine_extras(...)`, and passes `preflight=build_preflight(boundaries, settings, which, machine_extras(...))` to the `Tick`.

Tests: `tests/application/test_agent_environment_item.py`, `tests/application/test_agent_run_probe.py` (`FakeAgentRuntime` scripted `completed` and `died`, `ScriptedRun`; a `ClaudeCodeRuntime` on the stand-in of `tests/adapters/claude_stand_in.py` for the flags; a runtime double that inherits `AgentRuntime` and raises `AgentRuntimeError`), `tests/entry/test_wiring_extras.py`.

## Acceptance criteria

1. `agent_environment_item` passes for a `PATH` under which `factory-guard` is found (a `find` stub backed by a dictionary) and a `HOME` that is an existing directory (a directory in `tmp_path`); its name is `agent-environment`.
2. `agent_environment_item` fails, naming `factory-guard`, for a `PATH` under which it is not found, and fails for an environment without a `PATH`.
3. `agent_environment_item` fails, naming `HOME`, for an environment without a `HOME` and for a `HOME` that is not a directory (two cases).
4. `agent_run_probe_item` passes when the agent runtime is scripted to end `completed`, and its name is `agent-run-probe`.
5. The request the probe makes has the prompt `PROBE_PROMPT`, the allowed decisions `["question"]`, a `time_limit` of 2 minutes, the working directory `boundaries.checkout`, an `environment` equal to the one given, `os_user` equal to `settings.agent_user`, a guard, and the agent `coder` with its own model and tools and a `budget_usd` of `0.10`.
6. `agent_run_probe_item` fails, with a detail that contains `died`, when the agent runtime is scripted to end `died`.
7. `agent_run_probe_item` fails, naming the end reason, for each of `no_result`, `time_limit` and `budget`.
8. `agent_run_probe_item` fails, with a detail that contains the error's message, when the agent runtime raises `AgentRuntimeError("sudo: a password is required")`: a refused `sudo` is a machine fault found before any claim.
9. `agent_run_probe_item` fails, naming the agent, when no agent `coder` is installed.
10. The probe's call carries the same flags as a stage's: with `ClaudeCodeRuntime` on the stand-in, the arguments of the probe's call and of a call for a request built like a stage's (the agent `coder`, a guard, the decisions `review` and `question`) hold the same flags, the arguments that start with `--`, in the same order.
11. Both items are machine items: under `Preflight`, two `run()` calls with the same non-`None` image make the agent runtime run the probe once.
12. `machine_extras` for settings without an agent user returns callables whose items are named `token-file`, `agent-user`, `agent-environment` and `agent-run-probe`, in this order.
13. `machine_extras` for settings with `agent_user == "agent"` returns callables whose items are named `token-file`, `agent-user`, `tool:sudo`, `agent-environment` and `agent-run-probe`, in this order.
14. A `Tick` from `build_tick(boundaries, settings, which)` with every tool present, agents installed, a runtime reporting the pinned version and a scripted `completed` probe, but a token file that does not exist, returns `TickOutcome(stopped="preflight_failed")` and the stop's detail names `token-file`.
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
