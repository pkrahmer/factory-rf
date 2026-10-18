---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 224
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T16:51:06.356897Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T16:51:06.362329Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T16:51:24.594049Z'
  stage: intake
  run: 9c0192c99dee48378d0af712964229e3
---

# The preflight checks the kernel's write guard

## Description

Once every agent run starts through `factory-confine` (S0004), a kernel without Landlock, or with an ABI below 3, or an agent environment whose `PATH` lacks the wrapper, would make every run end in `AgentRuntimeError`. This story makes the preflight find that first: a new machine item `confinement` passes when the kernel offers Landlock ABI 3 or higher and `factory-confine` is on the agent run's `PATH`, and otherwise names each fault and what to do. Its failure is the existing machine stop `preflight_failed`, which names the failed items, so no agent runs and no new stop reason is needed; there is no fallback to the hook (feature decision 12, the human's to confirm). The item runs among the machine's extras, after `agent-environment` and before `agent-run-probe`, so the probe's run is not the first to find the fault. Like every machine item it runs once per image build. The hook's own check in `agent-environment` stays as it is.

## Interface

`factory.application.preflight` (`application`):

```python
_CONFINEMENT_ITEM = "confinement"

def confinement_item(
    abi: Callable[[], int],
    environment: Mapping[str, str],
    find: Callable[[str, str], str | None],
) -> PreflightItem:
    """Check that the kernel offers Landlock as the write guard needs, and that runs find the wrapper."""
```

- It passes (`PreflightItem(name="confinement", passed=True)`) when `abi_fault(abi())` is `None` and `find(CONFINE_COMMAND, environment["PATH"])` is not `None`.
- Otherwise its detail joins the faults with `"; "`, the kernel's first:
  - the kernel's: `f"{abi_fault(n)}: update the kernel (on WSL: wsl --update), or allow the Landlock system calls in the container runtime's seccomp profile"`, where `n` is `abi()`;
  - the wrapper's: `"the agent run has no PATH"` when the environment has no `PATH`, else `f"{CONFINE_COMMAND} is not on the agent run's PATH {path}"` when `find` returns `None`.

`factory.entry.wiring` (`entry`):

- `machine_extras` appends `lambda: confinement_item(abi_version, environment, _which_on)` right after the `agent-environment` item and before the `agent-run-probe` item, with `abi_version` from `factory.adapters.landlock`.

Tests (the tester writes them): `tests/application/test_confinement_item.py`. Changed under the feature's decision 12, by the tester only: `tests/entry/test_wiring_extras.py`, the test `test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user`, whose two rows of names gain `"confinement"` between `"agent-environment"` and `"agent-run-probe"`.

## Acceptance criteria

1. `confinement_item` with an `abi` returning 3 or 7 and a `find` that finds `factory-confine` on `PATH` passes, named `confinement`, with an empty detail (rows of one parametrized test).
2. With an `abi` returning 0 or 2 and the wrapper found, it fails with the detail `the kernel offers Landlock ABI 0, the write guard needs ABI 3 or higher: update the kernel (on WSL: wsl --update), or allow the Landlock system calls in the container runtime's seccomp profile`, or the same with `ABI 2` (rows of one parametrized test, in the same test as criterion 1).
3. With an `abi` returning 7, it fails with `factory-confine is not on the agent run's PATH /usr/bin` when `find` does not find it on `PATH` `/usr/bin`, and with `the agent run has no PATH` when the environment has none (rows of the same test).
4. With an `abi` returning 2 and the wrapper not found, the detail is the kernel's fault, then `; `, then the wrapper's.
5. `find` is asked for `factory-confine` on the environment's `PATH`: a `find` that records its calls is called with `("factory-confine", "/opt/factory/.venv/bin:/usr/bin")` for that `PATH`.
6. `machine_extras` lists its items in the order `token-file`, `agent-user`, (`tool:sudo` with an agent user), `agent-environment`, `confinement`, `agent-run-probe` (the changed rows of `tests/entry/test_wiring_extras.py`).
7. A preflight run that finds `confinement` failed returns `preflight_failed` and raises that machine stop, whose detail holds `confinement: ` and the item's detail, and no agent run is started (a preflight from `build_preflight` whose one extra is `lambda: confinement_item(lambda: 2, environment, find)`, the fake agent runtime receiving no request).
8. `make check` stays green.
9. docs: `docs/operator-guide.md`, section *The preflight's items*, gets a row for `confinement` (what it checks, its three faults, what to do: update the kernel, on WSL with `wsl --update`, or let the container runtime's seccomp profile allow `landlock_create_ruleset`, `landlock_add_rule` and `landlock_restrict_self`; install `factory-confine` with the factory), and the section *The stops of the repository or the machine* says that a kernel without Landlock ABI 3 is the stop `preflight_failed` and that the factory does not fall back to the hook. `docs/decisions.md` gets an entry *No agent runs without the kernel's write guard*, dated 2026-10-18 (F0019-S0005), with the reasons of the feature's decision 12 and the alternative left to the human (an operator setting that falls back to the hook alone).

## Smoke test

```bash
uv run -q python -c '
import os, shutil
from factory.adapters.landlock import abi_version
from factory.application.preflight import confinement_item
def find(name, path):
    return shutil.which(name, path=path)
print(confinement_item(abi_version, {"PATH": os.environ["PATH"]}, find).passed)
print(confinement_item(lambda: 2, {"PATH": "/nowhere"}, find).detail)
'
```
Expect: two lines, `True` and then `the kernel offers Landlock ABI 2, the write guard needs ABI 3 or higher: update the kernel (on WSL: wsl --update), or allow the Landlock system calls in the container runtime's seccomp profile; factory-confine is not on the agent run's PATH /nowhere`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`factory.application.preflight.confinement_item(abi, environment, find)`, `machine_extras` in `factory.entry.wiring`). The helpers it relies on exist: `abi_fault` (domain/confinement.py), `abi_version` (adapters/landlock.py), `CONFINE_COMMAND` (domain/agent_runs.py) and `_which_on` (entry/wiring.py). The detail texts are exact and the join order is stated.
   Criteria: each is testable by one test function. Every rule has both sides. The pass side is criterion 1. The kernel fault is criterion 2, with ABI 0 and 2. The wrapper-not-found fault and the no-`PATH` fault are criterion 3. Both faults together, in order, are criterion 4. The `find` call arguments are criterion 5. The extras order is criterion 6, and the `preflight_failed` stop with no agent run is criterion 7. `make check` and `docs:` are the last two. The test-change leave for `tests/entry/test_wiring_extras.py` is named and backed by feature decision 12.
   Smoke test: the command is runnable. Both `Expect:` lines are checkable against the output: `True`, then the exact joined fault text.
   Architecture: the item sits in `application`. The ABI reader and `which` are injected from `entry`, so `application` knows no tool. Layering is respected.
   Scope: it is within the feature's S0005 scope (preflight item and wiring). The fallback to the hook is out of scope and not added.
