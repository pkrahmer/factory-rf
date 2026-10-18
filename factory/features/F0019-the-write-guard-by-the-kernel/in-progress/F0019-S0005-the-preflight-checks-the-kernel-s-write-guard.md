---
stage: docs
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 224
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-18T17:04:36.277337Z'
  lease_duration: 60
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
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T16:51:44.503697Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T16:54:11.240795Z'
  stage: tests
  run: 35b230ec5d9a4e51aa5b440502f0c3a2
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-18T16:54:31.124779Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-18T16:56:54.256196Z'
  stage: doing
  run: 1555ecbf28c74389ad68e2629da26e77
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-18T16:57:14.321024Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-18T16:58:16.111360Z'
  stage: review
  run: b1ac36990f9a4160b5f4fde14a7f1a04
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-18T16:58:36.274663Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-18T16:58:52.318179Z'
  stage: doing
  run: b9eb4d54b5ab47dd981d00a60658e887
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-18T16:59:12.997870Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-18T17:01:07.393306Z'
  stage: tests
  run: c4218b87ec974b8e94c792847961586f
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-18T17:01:27.861049Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-18T17:03:13.528700Z'
  stage: doing
  run: 2c937d5ed2ff4d74953ec6ded8a05402
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-18T17:03:33.601500Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-18T17:04:16.310970Z'
  stage: review
  run: 522672802fd34a16abf2c37572225854
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-18T17:04:36.277337Z'
  stage: docs
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
4. factory: started tests as self.
5. tester: Wrote the tests for the `confinement` preflight item and changed the extras-order test as the Interface allows under the feature's decision 12.

   - criterion 1: tests/application/test_confinement_item.py::test_the_item_passes_with_landlock_abi_3_and_the_wrapper_on_path_and_names_each_fault (rows abi-3, abi-7)
   - criterion 2: the same test (rows abi-0, abi-2)
   - criterion 3: the same test (rows not-on-path, no-path)
   - criterion 4: tests/application/test_confinement_item.py::test_the_kernels_fault_comes_before_the_wrappers
   - criterion 5: tests/application/test_confinement_item.py::test_the_wrapper_is_looked_for_on_the_environments_path
   - criterion 6: tests/entry/test_wiring_extras.py::test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user (both rows now have "confinement" between "agent-environment" and "agent-run-probe")
   - criterion 7: tests/application/test_confinement_item.py::test_a_failed_confinement_item_stops_the_machine_before_any_agent_run. It uses `build_preflight` with the one extra the criterion names. It checks four things: the return value is `preflight_failed`; there is one machine stop with that reason; the stop's detail holds `confinement: ` and the ABI 2 detail; the fake agent runtime received no requests.
   - criteria 8 and 9 (`make check`, docs) are not test criteria.

   Files: created tests/application/test_confinement_item.py. Changed tests/entry/test_wiring_extras.py, an earlier story's test, only in the two rows of names that the work item's Interface lists under decision 12.

   `make test` result: test_confinement_item.py does not collect, with an ImportError, because `confinement_item` does not exist yet in `factory.application.preflight`. Both rows of the extras-order test fail because `machine_extras` does not list `confinement` yet. After that run I renamed the unused arguments of the not-found fake to `_name` and `_path` and gave `split` a `maxsplit`; this was only to satisfy lint. `make lint` is green. I skipped the type check, as the stage says to.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/application/test_confinement_item.py - ImportError while importin...
6. factory: started doing as self.
7. coder: I built the `confinement` preflight item and wired it into the machine's extras.

   - `src/factory/application/preflight.py`: added `confinement_item(abi, environment, find)`, a private `_kernel_fault` and the constants `_CONFINEMENT_ITEM` and `_KERNEL_ADVICE`. `_kernel_fault` adds the "update the kernel …" advice to `abi_fault`'s text. The item joins the kernel's fault and the wrapper's with `"; "`, the kernel's first.
   - `src/factory/entry/wiring.py`: `machine_extras` now appends `lambda: confinement_item(abi_version, environment, _which_on)` after `agent-environment` and before `agent-run-probe`. `abi_version` comes from `factory.adapters.landlock`.

   Main choice: I reused the `_path_fault` helper that `agent_environment_item` already had. It used to be fixed to `GUARD_COMMAND`; it now takes the command as a parameter, and `agent-environment` passes `GUARD_COMMAND` while `confinement` passes `CONFINE_COMMAND`. Both texts ("the agent run has no PATH" and "… is not on the agent run's PATH …") are exactly what the Interface asks for. I rejected writing a second, nearly identical PATH check for the wrapper, because that would be a duplicate helper.

   One departure from the Interface: its docstring for `confinement_item` was 105 characters at its indent, over ruff's 100-character limit. I reworded it to "Check that the kernel offers the Landlock the write guard needs and runs find the wrapper." The meaning is the same.

   Refactor pass: I read the diff and found nothing to change.

   `make check` is green: lint, types, layers, sast, secrets, licenses and test. The smoke test prints `True` and then the expected joined detail.

   Noticed but not touched: the docs criterion (operator guide rows, the decisions entry *No agent runs without the kernel's write guard*) is left to the documenter. The journal did not change the meaning of the task, so `## Description` stays as it is.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: 1. tests/application/test_confinement_item.py:35: `_every_tool` is a sixth copy of the same helper. Five earlier modules already hold it word for word: tests/entry/test_wiring_extras.py:53, tests/entry/test_wiring_run.py:76, tests/entry/test_wiring_agent_user.py:53, tests/entry/test_wiring_preflight.py:18 and tests/application/test_tick_preflight.py:32. Fix: under the standing leave to move a shared test helper, the tester moves `_every_tool` to one shared place under `tests/` (a root module such as `git_support`, or a fixture in `tests/conftest.py`) and makes the new module and the earlier ones use it from there, every earlier test keeping its name and what it checks. The coder hands this over with `tests` (R9).

   Earlier tests:
   - tests/entry/test_wiring_extras.py: the human's leave, named in the story's Interface under the feature's decision 12. Only the two rows of names in `test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user` changed, each gaining "confinement" between "agent-environment" and "agent-run-probe". This is within the leave.
10. factory: started doing as self.
11. coder: Round 1: the reviewer's one finding is a change to tests, which the coder does not make. I am handing it to the tester under the standing leave in CLAUDE.md for moving a shared test helper.

    I checked the finding. `def _every_tool(name: str) -> str | None` appears in six test modules:
    - tests/application/test_confinement_item.py:35
    - tests/entry/test_wiring_extras.py:53
    - tests/entry/test_wiring_run.py:76
    - tests/entry/test_wiring_agent_user.py:53
    - tests/entry/test_wiring_preflight.py:18
    - tests/application/test_tick_preflight.py:32

    Change for the tester, in one sentence: move `_every_tool` into one shared module at the `tests/` root (or a fixture in `tests/conftest.py`), and change all six modules listed above to use it from there, each earlier test keeping its name and checking the same thing.

    What I built in round 0 stands unchanged (src/factory/application/preflight.py `confinement_item`, src/factory/entry/wiring.py `machine_extras`). I made no source change this round and did not run `make check` again; it was green at the end of round 0.

    The journal did not change the meaning of the task, so `## Description` stays as it is.
12. factory: started tests as self.
13. tester: Round 1, a test change: I made the move named in the coder's entry 11, which answers the reviewer's finding 1. It falls under CLAUDE.md's standing leave to move a shared test helper, so it needed no answer from the human.

    The helper `_every_tool` was copied word for word in six test modules. It is now in one shared place: `every_tool` in `tests/wiring_support.py`. That root module already holds the constants the wiring tests share; I widened its module docstring and gave the function a docstring. Each of the six modules now imports `every_tool` from there, and its own copy is gone. Every test keeps its name and checks the same thing; the only change in them is the name of the helper they pass.

    Criterion mapping: unchanged from entry 5.

    Files changed:
    - tests/wiring_support.py: added `every_tool`.
    - tests/application/test_confinement_item.py: this story's own test module.
    - Earlier test files changed under the standing leave:
      - tests/entry/test_wiring_extras.py
      - tests/entry/test_wiring_run.py
      - tests/entry/test_wiring_agent_user.py
      - tests/entry/test_wiring_preflight.py
      - tests/application/test_tick_preflight.py

    No files created. Every test module imports; none failed to import.

    `make test`: test: green (38.2 s). `make lint`: lint: green.

    `lint`: lint: green (0.0 s)
    `test`: test: green (40.5 s)
14. factory: started doing as self.
15. coder: Round 1, after the tester's move. The tester moved the shared helper into `tests/wiring_support.py` as `every_tool` (entry 13). That closes the reviewer's finding 1, so this round needed no source change from me.

    The code from round 0 stands as it was:
    - `src/factory/application/preflight.py`: `confinement_item` and its private `_kernel_fault`.
    - `src/factory/entry/wiring.py`: `machine_extras` now has the `confinement` item between `agent-environment` and `agent-run-probe`.

    Main choice, unchanged from round 0: `confinement_item` reuses the existing `_path_fault` helper with the command passed in as a parameter. I rejected writing a second PATH check for the wrapper, because it would duplicate that helper.

    Refactor pass: no new source diff this round, so nothing to change.

    I ran `make check` and it is green: `test: green (37.7 s)`, coverage 98.67 %, `check: green`.

    Noticed but not touched: the docs criterion is left to the documenter. The journal did not change the meaning of the task, so `## Description` stays as it is.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
16. factory: started review as self.
17. reviewer: no findings

    Read: the work item, plus `git diff main...HEAD -- . ':!factory'` (src/factory/application/preflight.py, src/factory/entry/wiring.py, tests/application/test_confinement_item.py, tests/wiring_support.py and the five earlier wiring and preflight test modules).

    - Criteria 1 to 3 are rows of one parametrized test: abi-3, abi-7, abi-0, abi-2, not-on-path and no-path. The ABI limit is tested on both sides (2 and 3), and so is PATH (present and absent). Criterion 4 checks the join order. Criterion 5 checks the exact `find` call. Criterion 6 checks the changed rows. Criterion 7 goes through `build_preflight` with the one extra the criterion names and asserts four things: the return value `preflight_failed`, one machine stop, the stop's detail holding `confinement: ` and the item's detail, and no request at the fake agent runtime. In the coder's entry 15, `make check` was green.
    - Architecture: `confinement_item` is in `application` and gets the ABI reader and `which` injected. It uses `abi_fault` from `domain`. `entry` wires `abi_version` from `adapters.landlock`, and the layer order holds.
    - Security: no suppression markers, no shell commands built from strings, no secrets.
    - Quality: the wrapper check reuses `_path_fault`, which now takes the command as a parameter, instead of a second copy. `_kernel_fault` only adds the advice to `abi_fault`'s text. The earlier `_every_tool` copies are gone, replaced by `tests/wiring_support.py::every_tool`, so the round 0 finding is closed. The test helpers `_found` and `_not_found` are not copies of an existing helper: `_find` in test_agent_environment_item.py works from a table of commands.
    - Hygiene: the journal records the reuse of `_path_fault` and the rejected duplicate. It also records the shorter docstring, reworded to stay within the line limit with the same meaning. The docs criterion still describes what the documenter must write. One note for the documenter: the operator guide's intro sentence that counts and lists the extras, docs/operator-guide.md:315, will also need `confinement`.

    Earlier tests:
    - tests/entry/test_wiring_extras.py: the human's leave, named in the story's Interface under the feature's decision 12. The two rows of names gained "confinement" and nothing else in them changed. The `_every_tool` → `every_tool` change in the same file is under the standing leave to move a shared test helper.
    - tests/entry/test_wiring_run.py: the standing leave to move a shared test helper. Only `_every_tool` was replaced by the shared `every_tool`; every test keeps its name and what it checks.
    - tests/entry/test_wiring_agent_user.py: the standing leave to move a shared test helper, with the same helper-only change.
    - tests/entry/test_wiring_preflight.py: the standing leave to move a shared test helper, with the same helper-only change.
    - tests/application/test_tick_preflight.py: the standing leave to move a shared test helper, with the same helper-only change.
    - tests/wiring_support.py: the shared place the helper moved to, under the same leave. It gained `every_tool` and a wider module docstring, and its constants are unchanged.
18. factory: started docs as self.
