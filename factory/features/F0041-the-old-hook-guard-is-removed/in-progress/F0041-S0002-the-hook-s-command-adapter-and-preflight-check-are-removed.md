---
stage: docs
blocked: null
round: 1
attempts: 1
crashes: 0
pull_request: 348
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T10:51:23.005340Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T10:51:23.010607Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T10:51:41.180416Z'
  stage: intake
  run: 8731112fc6e74ab386f965206a1c2aed
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T10:52:01.792838Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T10:58:33.077840Z'
  stage: tests
  run: b4bb58e5eccb430caf3bd091fa323184
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T10:58:54.071199Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T11:04:40.998177Z'
  stage: doing
  run: 281a4c80cd414df0b3ede4a899ac56f5
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T11:05:02.966727Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T11:06:02.441951Z'
  stage: review
  run: 2583ef78fa3f495d955026a291a932b2
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T11:06:23.813000Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-20T11:06:40.957227Z'
  stage: doing
  run: d450c74b3b664639853a415122d50039
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T11:07:02.024362Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-20T11:12:06.394864Z'
  stage: tests
  run: fccd8e5f13ac45b5b3c5f8158d80bc7a
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-20T11:12:26.967178Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-20T11:22:16.951575Z'
  stage: doing
  run: afaf1f24cd2240d4be9576c38d742368
- number: 16
  speaker: factory
  kind: stall
  at: '2026-10-20T11:22:16.977879Z'
  stage: doing
  run: afaf1f24cd2240d4be9576c38d742368
  reason: check_red
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-20T11:22:39.882138Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-20T11:28:13.392349Z'
  stage: doing
  run: 499b5c91135f4eb59e51b9dd78e1199f
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-20T11:28:34.337832Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-20T11:29:16.655212Z'
  stage: review
  run: 2256e0a7cf644f38b81f2fcb64e5d211
---

# The hook's command, adapter and preflight check are removed

## Description

After S0001 no agent run registers the hook `factory-guard`, but its code is still there: the entry module `factory.entry.guard` (the console script), the adapter `factory.adapters.claude_guard` (`judge`, `read_guard_settings`, `GuardVerdict` and the fail-open reading of the payload), the wiring's re-exports of `judge` and `read_guard_settings`, the constant `GUARD_COMMAND`, the error `GuardSettingsInvalid`, the field `GuardSettings.temporary_directory` that only the hook read, and the preflight item `agent-environment`'s search for `factory-guard` on the agent run's `PATH`, which stops the machine when the script is missing. This story removes all of it and the tests that pin it (the feature's decision 10). The hook's fail-open rule for a payload without a file path goes with it, and nothing replaces it (decision 5). The item `agent-environment` keeps its name and checks the agent run's `HOME` only (decision 2); the item `confinement` still reports a missing `PATH` and searches it for `factory-confine`. What the kernel's guard, the undo and the stage use stays: `GuardSettings` with `root`, `write_paths`, `protected_paths` and `tool_paths`, `AgentRunRequest.guard`, `CONFINE_COMMAND`, `refusal`, `PROTECTED_PATHS`, `WritePathService` and the preflight's probe, whose request keeps its guard settings so that it carries a stage's confinement. The console script line in `pyproject.toml` is the human's change 1, after this story; the documents are S0003's.

## Interface

Deleted modules: `src/factory/adapters/claude_guard.py` (`adapters`) and `src/factory/entry/guard.py` (`entry`).

`src/factory/domain/agent_runs.py` (`domain`):

```python
class GuardSettings(BaseModel):
    """Where an agent may write: the root, write paths, protected paths and tool paths."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    root: AbsolutePath
    write_paths: list[str]
    protected_paths: list[str]
    tool_paths: list[str] = []
```

- `GUARD_COMMAND` and its comment are removed; `CONFINE_COMMAND = "factory-confine"` stays.
- `GuardSettings` has exactly the four fields above; a value with `temporary_directory` is refused (`extra="forbid"`).

`src/factory/domain/errors.py` (`domain`): `GuardSettingsInvalid` is removed.

`src/factory/application/preflight.py` (`application`):

```python
def agent_environment_item(
    environment: Mapping[str, str],
    is_directory: Callable[[Path], bool],
) -> PreflightItem:
    """Check that an agent run finds its login in `HOME`."""
```

- The item is named `agent-environment`. It passes when `environment["HOME"]` names a directory (`is_directory`), whatever `PATH` holds or whether it is there. It fails with `the agent run has no HOME` when `HOME` is missing, and with `the agent run's HOME <home> is no directory` when it is not a directory.
- The import of `GUARD_COMMAND` goes. `_path_fault` stays for `confinement_item`, unchanged.
- The comment in `confinement_item` says there is no other guard to fall back to (it names no hook); the comment in `_probe_request` says the guard settings give the probe a stage's confinement (it names no flag of a hook).

`src/factory/entry/wiring.py` (`entry`):

- The import of `judge` and `read_guard_settings` and their two entries in `__all__` are removed.
- `machine_extras` adds `lambda: agent_environment_item(environment, Path.is_dir)`, in the same place.
- The comment in `production_environment` names `factory-confine` among the console scripts next to the interpreter.

Tests (the tester writes them):

- `tests/test_hook_removed.py` (new): criteria 1 and 2.
- `tests/application/test_agent_environment_item.py`: rewritten for criterion 3 under the leave of the feature's decision 10.
- `tests/entry/test_wiring_agent_environment.py` (new): criterion 4, through `machine_extras` as `tests/entry/test_wiring_extras_path.py` reaches an item (the tester may move its `_item` helper to a shared module under the standing leave of `CLAUDE.md`, *Tests*).
- Deleted under decision 10: `tests/adapters/test_claude_guard.py`, `tests/adapters/test_claude_guard_temporary.py`, `tests/entry/test_guard.py`, `tests/guard_support.py`.
- Changed under decision 10: `tests/application/test_undo.py` (`test_the_guard_refuses_exactly_what_the_undo_puts_back`, `_payload`), `tests/test_model_configuration.py` (`EXCEPTIONS`), `tests/application/test_agent_run_probe.py` (`test_the_probe_runs_once_for_each_image_build`), `tests/entry/test_wiring_extras_path.py` (two rows of `test_the_wrapper_items_search_the_agent_run_s_path_not_the_process_s`), `tests/entry/test_wiring_handlers.py` (`test_the_agent_environment_is_a_path_led_by_the_scripts_and_a_home`).

## Acceptance criteria

1. The hook's code is gone and the kernel's guard is kept (rows of one parametrized test). `importlib.util.find_spec` gives `None` for `factory.adapters.claude_guard` and for `factory.entry.guard`. `hasattr` is `False` for `factory.domain.agent_runs.GUARD_COMMAND`, `factory.domain.errors.GuardSettingsInvalid`, `factory.entry.wiring.judge` and `factory.entry.wiring.read_guard_settings`, and neither `"judge"` nor `"read_guard_settings"` is in `factory.entry.wiring.__all__`. `hasattr` is `True` for `factory.domain.agent_runs.CONFINE_COMMAND` (equal to `"factory-confine"`), `factory.domain.agent_runs.GuardSettings`, `factory.domain.write_paths.refusal`, `factory.domain.write_paths.PROTECTED_PATHS` and `factory.application.preflight.confinement_item`.
2. `GuardSettings` has no temporary folder (rows of one parametrized test, the constructor reached through a variable typed `type[BaseModel]`): `list(GuardSettings.model_fields)` is `["root", "write_paths", "protected_paths", "tool_paths"]`; `root=Path("/w"), write_paths=["src/*"], protected_paths=[]` builds a value; the same with `temporary_directory=Path("/t")` raises `ValidationError`.
3. The item `agent-environment` checks `HOME` only (rows of one parametrized test of `agent_environment_item(environment, Path.is_dir)`, `tmp_path` holding the folder `home` and the file `file`). `{"PATH": "/usr/bin", "HOME": <home>}` passes, `{"HOME": <home>}` passes, and `{"PATH": "/opt/factory/bin", "HOME": <home>}` passes. `{"PATH": "/usr/bin"}` fails with the detail `the agent run has no HOME`; `{"PATH": "/usr/bin", "HOME": <file>}` fails with `the agent run's HOME <file> is no directory`. Every row's item is named `agent-environment`.
4. The wiring's item passes without `factory-guard` (rows of one parametrized test through `machine_extras`): with the agent run's `PATH` a folder that holds only `factory-confine` and its `HOME` an existing folder, the item `agent-environment` is `PreflightItem(name="agent-environment", passed=True)`; with `HOME` a missing folder `<home>`, it fails with `the agent run's HOME <home> is no directory`.
5. The undo still puts back exactly what the write paths refuse (`test_the_guard_refuses_exactly_what_the_undo_puts_back`, judging with `refusal`): of `src/a.py`, `docs/a.md`, `tests/t.py`, `pyproject.toml` and `factory/pipeline.yml` written in a `doing` stage, the refused set is `{"docs/a.md", "tests/t.py", "pyproject.toml", "factory/pipeline.yml"}`, and the undo's `reverted` and `deleted` together are that set.
6. `make check` stays green.
7. docs: none. S0003 writes the documents (the feature's decision 1).

## Smoke test

```bash
uv run python - <<'EOF'
import importlib.util
import tempfile
from pathlib import Path

import factory.domain.agent_runs as runs
import factory.domain.errors as errors
import factory.entry.wiring as wiring
from factory.application.preflight import agent_environment_item

print(importlib.util.find_spec("factory.adapters.claude_guard"), importlib.util.find_spec("factory.entry.guard"))
print(hasattr(runs, "GUARD_COMMAND"), hasattr(errors, "GuardSettingsInvalid"), hasattr(wiring, "judge"), list(runs.GuardSettings.model_fields))
home = tempfile.mkdtemp()
for environment in ({"PATH": "/usr/bin", "HOME": home}, {"PATH": "/usr/bin"}):
    item = agent_environment_item(environment, Path.is_dir)
    print(item.name, item.passed, item.detail or "-")
EOF
```
Expect: four lines, `None None`, `False False False ['root', 'write_paths', 'protected_paths', 'tool_paths']`, `agent-environment True -` and `agent-environment False the agent run has no HOME`

```bash
ls src/factory/adapters/claude_guard.py src/factory/entry/guard.py tests/adapters/test_claude_guard.py tests/entry/test_guard.py tests/guard_support.py 2>&1 | grep -c 'No such file'
```
Expect: `5`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names the two deleted modules, the exact `GuardSettings` with its four fields, the removal of `GUARD_COMMAND` and `GuardSettingsInvalid`, the full signature of `agent_environment_item(environment, is_directory)` with its pass and fail details, and the wiring changes (imports, `__all__`, `machine_extras` lambda). Concrete modules and signatures; the comment rewrites in `confinement_item`, `_probe_request` and `production_environment` are stated but are not behaviour.
   - Criteria: each is testable by one parametrized test function. 1 covers the removed and the kept names, 2 the field list with the accepting side and the refused `temporary_directory`, 3 every `HOME` and `PATH` row with both the passing and the failing sides and the exact details, 4 the wiring's pass and its fail through `machine_extras`, and 5 the undo against `refusal` with the exact set. Criterion 6 is `make check` and 7 is docs: none, as decision 1 states.
   - Smoke test: the Python heredoc and the `ls | grep -c` line are runnable without a paid call and never run pytest, so the `-q` rule does not apply. The `Expect:` lines name exact output: four lines in the first block and `5` in the second.
   - Architecture: the changes stay in their layers. The domain loses a constant, an error and a field. The application item narrows to `HOME`. The entry wiring drops the re-exports. The adapter and the entry module are deleted. No layer import is reversed, and `GuardSettings`, `AgentRunRequest.guard`, `refusal` and `WritePathService` are kept as decision 4 says.
   - Scope: within the feature's S0002 scope list (decisions 2, 3, 4, 5, 8, 10). The human's leave in decision 10 names every changed or deleted test of other stories. The console script line, the documents and the kernel's guard are left out, as the feature's out-of-scope list requires.
4. factory: started tests as self.
5. tester: Wrote the tests for this story's criteria, and deleted or changed the earlier tests that the Interface lists under the feature's decision 10.

   Criterion → test:
   - criterion 1: tests/test_hook_removed.py::test_the_hook_s_code_is_gone_and_the_kernel_s_guard_is_kept (one row per name: two `find_spec` rows, four removed names, two `__all__` rows, `CONFINE_COMMAND == "factory-confine"`, and four kept names)
   - criterion 2: tests/test_hook_removed.py::test_the_guard_settings_have_no_temporary_folder (rows: the four fields in order, a build without `temporary_directory`, and `ValidationError` with it; the constructor is reached through a variable typed `type[BaseModel]`)
   - criterion 3: tests/application/test_agent_environment_item.py::test_the_agent_environment_checks_the_home_only (five rows: PATH /usr/bin with home, home without PATH, PATH /opt/factory/bin with home, no HOME, HOME a file)
   - criterion 4: tests/entry/test_wiring_agent_environment.py::test_the_wiring_s_agent_environment_needs_no_factory_guard (rows `home` and `missing-home`, run through `machine_extras` with an agent PATH that holds only `factory-confine`)
   - criterion 5: tests/application/test_undo.py::test_the_guard_refuses_exactly_what_the_undo_puts_back, now judging with `factory.domain.write_paths.refusal(path, settings)` on the relative paths
   - criteria 6 and 7: no test (`make check`; docs: none)

   Files created: tests/test_hook_removed.py, tests/entry/test_wiring_agent_environment.py.

   Files deleted under decision 10: tests/adapters/test_claude_guard.py, tests/adapters/test_claude_guard_temporary.py, tests/entry/test_guard.py, tests/guard_support.py.

   Files changed under decision 10:
   - tests/application/test_agent_environment_item.py: rewritten for criterion 3.
   - tests/application/test_undo.py: `judge` replaced by `refusal`; `_payload` and the unused `json` and `Path` imports removed.
   - tests/test_model_configuration.py: the two `claude_guard` rows removed from `EXCEPTIONS`.
   - tests/application/test_agent_run_probe.py::test_the_probe_runs_once_for_each_image_build: now calls `agent_environment_item(environment, is_directory)`. The old count of `find` calls is replaced by a count of `is_directory` calls (`homes == [tmp_path]`), so it still checks that the item runs once across the two preflight runs.
   - tests/entry/test_wiring_extras_path.py: the two `agent-environment`/`factory-guard` rows removed.
   - tests/entry/test_wiring_handlers.py::test_the_agent_environment_is_a_path_led_by_the_scripts_and_a_home: the `guard_present` parameter, the `factory-guard` script, the `shutil.which` check and the `shutil` import removed. The PATH and HOME checks are unchanged.

   Under the standing leave in CLAUDE.md (*Tests*), I moved `_item` from tests/entry/test_wiring_extras_path.py to tests/wiring_support.py as `machine_item`. The earlier file now imports it from there, and its test keeps its name and checks the same thing.

   `make test`, run once: it failed on the new and changed tests for the right reasons, not on syntax. The last lines named test_model_configuration's `claude_guard` rows (the module still exists), test_agent_run_probe's image-build test (old signature), and test_hook_removed's refused-`temporary_directory` row. After that run I merged test_hook_removed.py's separate test functions into the two parametrized tests that criteria 1 and 2 call for, and fixed two lint findings (an unused `Path` import, a `PLR0402` import alias). I did not run `make test` again, as the stage says. The restructured file has the same checks and passes `make lint`, but its failure has not been seen in a run. `make lint`: green.

   The test runner could import every module the tests need. The failures are wrong results or the old `agent_environment_item` signature, not missing modules.

   Nothing is open; no criterion needed interpreting.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/application/test_agent_environment_item.py::test_the_agent_environment_checks_the_home_only[home-not-a-directory]
6. factory: started doing as self.
7. coder: Removed the hook guard's code. The kernel's guard is unchanged. `make check` passes.

   What I built:
   - I deleted `src/factory/adapters/claude_guard.py` and `src/factory/entry/guard.py`. I used plain `rm` because `git rm` was refused (the `.git/index` write guard), so the deletions are left in the working tree.
   - `src/factory/domain/agent_runs.py`: removed `GUARD_COMMAND` and its comment, and removed `GuardSettings.temporary_directory`. The docstring now names the four fields that remain. `CONFINE_COMMAND` is kept.
   - `src/factory/domain/errors.py`: removed `GuardSettingsInvalid`.
   - `src/factory/application/preflight.py`: `agent_environment_item(environment, is_directory)` now checks only `HOME`, using the existing `_home_fault`. Removed the `GUARD_COMMAND` import. `_path_fault` is unchanged and still used by `confinement_item` and `opencode_item`. Rewrote the comments in `confinement_item` (there is no other guard to fall back to) and `_probe_request` (the guard gives the probe a stage's confinement) so they no longer mention the hook or its flags.
   - `src/factory/entry/wiring.py`: removed the `judge` and `read_guard_settings` import and their `__all__` entries. `machine_extras` now calls `agent_environment_item(environment, Path.is_dir)` in the same place. The comment in `production_environment` now names `factory-confine`.

   Main design decision: with only one possible fault left, `agent_environment_item` returns `_home_fault`'s single result directly. I rejected keeping the list-and-join shape that `confinement_item` uses: with one entry, that is dead structure.

   Refactor: I read the diff and found nothing to change. Code removed: 188 lines; code added: 10.

   Noticed but not touched:
   - `pyproject.toml:17` still declares `factory-guard = "factory.entry.guard:main"`, which now points to a deleted module. Per the description, removing that line is the human's change 1, after this story.
   - `InstanceSettings.temporary_directory` (`src/factory/domain/settings.py`, set in `wiring.read_environment_settings`, read in `disk_records._folders`) is a different field from the one removed and stays.
   - A leftover `mutants/` folder from an earlier mutmut sweep still holds copies of the old guard tests. It does not affect `make check`. Every mutmut run deletes it first.
   - The documents are S0003's.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item. Groups 1 to 5 pass. Criteria 1 to 5 each have one parametrized test that checks what its criterion says, and the coder's `make check` was green (entry 7). The layers hold. No silencing markers. No references to the hook are left in `src`/`tests`, apart from `pyproject.toml:17`, which is the human's change 1. The 5 new `make duplicates` findings are in `claude_runtime`/`opencode_runtime`/`clock`, which this diff does not touch. Item 6 fails: two earlier tests were changed differently from the change the human's leave (the feature's decision 10) spells out.

   1. `tests/application/test_agent_run_probe.py::test_the_probe_runs_once_for_each_image_build`: decision 10 says the first extra item becomes `confinement_item(lambda: LANDLOCK_MINIMUM_ABI, environment, find)` and the last line expects `finds == ["factory-confine"]`. The tester kept `agent_environment_item` instead, with a new `is_directory` counter (`homes == [tmp_path]`), which goes beyond the leave. Fix: the tester makes exactly decision 10's change (keep `find`/`finds`, call `confinement_item`, expect `["factory-confine"]`).
   2. `tests/entry/test_wiring_handlers.py::test_the_agent_environment_is_a_path_led_by_the_scripts_and_a_home`: decision 10 says the test places and finds `factory-confine` instead of `factory-guard`, with the parameter `confine_present` and the ids `confine-present`/`confine-absent`. The tester dropped the parametrization and the `shutil.which` check, so the test no longer checks that a script in the scripts folder is found on the PATH. Fix: the tester restores the parametrized test with `confine_present`, writes `factory-confine` into `scripts` and asserts `shutil.which("factory-confine", path=environment["PATH"])` as before.

   Earlier tests (item 6):
   - tests/adapters/test_claude_guard.py (D): the human's leave, decision 10 (deleted whole).
   - tests/adapters/test_claude_guard_temporary.py (D): the human's leave, decision 10 (deleted whole).
   - tests/entry/test_guard.py (D): the human's leave, decision 10 (deleted whole).
   - tests/guard_support.py (D): the human's leave, decision 10 (deleted whole).
   - tests/application/test_undo.py (M): the human's leave, decision 10 (`judge` replaced by `refusal`, `_payload`/`json` removed); within it.
   - tests/test_model_configuration.py (M): the human's leave, decision 10 (two `EXCEPTIONS` rows removed); within it.
   - tests/application/test_agent_environment_item.py (M): the human's leave, decision 10, as the story narrows it ("rewritten for criterion 3", one parametrized test). The single test replaces the two names decision 10 gave; the story's criterion 3 asks for that.
   - tests/entry/test_wiring_extras_path.py (M): the human's leave, decision 10 (two `agent-environment` rows removed), plus the standing leave to move a shared test helper (`_item` moved to `tests/wiring_support.py` as `machine_item`; the test keeps its name and its checks); within both.
   - tests/wiring_support.py (M): the standing leave to move a shared test helper (it receives `machine_item`).
   - tests/application/test_agent_run_probe.py (M): the human's leave, decision 10; beyond it (finding 1).
   - tests/entry/test_wiring_handlers.py (M): the human's leave, decision 10; beyond it (finding 2).
10. factory: started doing as self.
11. coder: Round 1: both review findings (entry 9) are changes to tests, so I changed no code and am handing them to the tester. The tester makes exactly the change that the feature's decision 10 spells out:

    1. `tests/application/test_agent_run_probe.py::test_the_probe_runs_once_for_each_image_build`: the first extra item becomes `confinement_item(lambda: LANDLOCK_MINIMUM_ABI, environment, find)`, with `find` and `finds` kept as before, and the last line expects `finds == ["factory-confine"]`. Drop the `is_directory` counter (`homes == [tmp_path]`).
    2. `tests/entry/test_wiring_handlers.py::test_the_agent_environment_is_a_path_led_by_the_scripts_and_a_home`: restore the parametrized test with the parameter `confine_present` and the ids `confine-present` and `confine-absent`. When the parameter is true, the test writes `factory-confine` into `scripts` and asserts `shutil.which("factory-confine", path=environment["PATH"])` as before, together with the unchanged PATH and HOME checks.

    The current code already supports both changes. `confinement_item(abi, environment, find)` in `src/factory/application/preflight.py:182` has the signature finding 1 needs, and `LANDLOCK_MINIMUM_ABI` is in `factory.domain.confinement`. The code's built state is unchanged from entry 7: the two modules are deleted, and `agent_runs.py`, `errors.py`, `preflight.py` and `wiring.py` are edited as that entry describes.

    Main choice: send this to tests rather than adjust code. I rejected adjusting code, because neither finding concerns the code and the coder never edits tests (R9).

    Noticed but not touched, still open: `pyproject.toml:17` still declares `factory-guard`, which is the human's change 1 after this story. A leftover `mutants/` folder holds copies of the old guard tests; every mutmut run deletes it first. I did not run `make check` this round, because nothing in the code changed since entry 7, when it passed.
12. factory: started tests as self.
13. tester: Round 1: I made the two test changes from the coder's entry 11, which fix review entry 9's findings, exactly as the feature's decision 10 spells them out. I changed nothing else.

    1. `tests/application/test_agent_run_probe.py::test_the_probe_runs_once_for_each_image_build`:
       - The first extra item is now `confinement_item(lambda: LANDLOCK_MINIMUM_ABI, environment, find)`. `find` and `finds` are back as they were on `main`.
       - The last line expects `finds == ["factory-confine"]`.
       - I removed the `is_directory`/`homes` counter. In the imports, `agent_environment_item` is replaced by `confinement_item`, and I added `LANDLOCK_MINIMUM_ABI` from `factory.domain.confinement`.
    2. `tests/entry/test_wiring_handlers.py::test_the_agent_environment_is_a_path_led_by_the_scripts_and_a_home`:
       - It is parametrized again, on `confine_present`, with the ids `confine-present` and `confine-absent`.
       - When the parameter is true, the test writes an executable `factory-confine` into `scripts`.
       - It asserts `shutil.which("factory-confine", path=environment["PATH"])` against that script, or `None` when the script is absent. The PATH and HOME checks are unchanged, and the `shutil` import is back.

    Both are earlier tests of other stories, changed under the human's leave in the feature's decision 10, as the review asked.

    Criterion → test (unchanged from entry 5):
    - criterion 1: tests/test_hook_removed.py::test_the_hook_s_code_is_gone_and_the_kernel_s_guard_is_kept
    - criterion 2: tests/test_hook_removed.py::test_the_guard_settings_have_no_temporary_folder
    - criterion 3: tests/application/test_agent_environment_item.py::test_the_agent_environment_checks_the_home_only
    - criterion 4: tests/entry/test_wiring_agent_environment.py::test_the_wiring_s_agent_environment_needs_no_factory_guard
    - criterion 5: tests/application/test_undo.py::test_the_guard_refuses_exactly_what_the_undo_puts_back
    - criteria 6 and 7: no test (`make check`; docs: none)

    Files created this round: none. Files changed: the two above.

    `make test`, run once: test: green (134.7 s). The code was already in place, so no test is red. The test run imported every module it needed.

    `make lint`: green. Nothing is open.

    `lint`: lint: green (0.0 s)
    `test`: test: green (134.5 s)
14. factory: started doing as self.
15. coder: Round 1: the tester has made the two test changes that review entry 9 asked for (entry 13). The code needed nothing more, so this round changed no code. The built state is the one entry 7 describes:
    - deleted: `src/factory/adapters/claude_guard.py` and `src/factory/entry/guard.py`
    - `src/factory/domain/agent_runs.py`: `GUARD_COMMAND` and `GuardSettings.temporary_directory` removed
    - `src/factory/domain/errors.py`: `GuardSettingsInvalid` removed
    - `src/factory/application/preflight.py`: `agent_environment_item(environment, is_directory)` checks `HOME` only, through `_home_fault`; the comments are rewritten
    - `src/factory/entry/wiring.py`: the re-exports are gone, `machine_extras` uses the new signature, and the comment names `factory-confine`

    Main choice: `agent_environment_item` returns `_home_fault`'s one result directly. I rejected the list-and-join shape that `confinement_item` uses, because with a single fault it is dead structure.

    Refactor: I read the diff again (9 lines added, 189 removed) and found nothing to change.

    Checks: the second `make check` was green (`test: green (134.5 s)`, `check: green`). The first run failed on two rows that pass when run alone and that this diff does not touch:
    - `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode[--follow]`
    - `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode[factory-last-line]`

    I cannot quote the failure's `E` lines or its `file:line`. I printed only the tail of that run, so only the two FAILED lines were kept, and a later `make test` ran without the failure. My guess, not verified: the test scans every file under `src/` with `rglob`, so it can catch a file that a worker writes there at the same moment. Its exception for `documents.py` covers only `domain/__pycache__/documents.*`. This is a flaky test outside this story and is still open; I left it alone.

    Noticed but not touched:
    - `pyproject.toml:17` still declares `factory-guard`. Removing it is the human's change 1, after this story.
    - The leftover `mutants/` folder still holds copies of the old guard tests. Every mutmut run deletes it first.
16. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
    src/factory/entry/check_story.py                   92      1     18      1    98%   161
    src/factory/entry/confine.py                       70      1      8      1    97%   110
    src/factory/entry/contract.py                      28      1      6      1    94%   41
    src/factory/entry/health.py                        33      1     10      1    95%   48
    src/factory/entry/run.py                           71      1      4      1    97%   170
    src/factory/entry/watch.py                         52      1      6      1    97%   87
    -------------------------------------------------------------------------------------------
    TOTAL                                            8845     54   1812     26    99%

    111 files skipped due to complete coverage.
    Required test coverage of 90.0% reached. Total coverage: 99.19%
    =========================== short test summary info ============================
    FAILED tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode[--follow]
    FAILED tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode[factory-last-line]
    make: *** [Makefile:75: test] Error 1
17. factory: started doing as self.
18. coder: Round 1, after the stall in entry 16: I changed no code. The code is still what entry 7 built:
    - deleted: `src/factory/adapters/claude_guard.py` and `src/factory/entry/guard.py`
    - `src/factory/domain/agent_runs.py`: `GUARD_COMMAND` and `GuardSettings.temporary_directory` removed
    - `src/factory/domain/errors.py`: `GuardSettingsInvalid` removed
    - `src/factory/application/preflight.py`: `agent_environment_item(environment, is_directory)` checks `HOME` only, through `_home_fault`
    - `src/factory/entry/wiring.py`: the re-exports are removed and `machine_extras` uses the new signature

    Main choice (unchanged): `agent_environment_item` returns `_home_fault`'s one result directly. I rejected the list-and-join shape that `confinement_item` uses, because with a single fault it is dead structure. Refactor: nothing more to change.

    The stall: the factory's `make check` failed on `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode[--follow]` and `[factory-last-line]`. This is the same pair entry 15 saw once. The story does not touch that test or what it reads.
    - I re-ran `make check` in the foreground and it was green (`test: green (135.0 s)`, `check: green`).
    - `grep -rla` over `src/` finds the two phrases only in `src/factory/domain/documents.py`, which the test leaves out on purpose.
    - The factory's output kept only the FAILED lines and the coverage table, not the `E` lines or the failing `file:line`. Neither failed run printed its traceback where I can see it, so I cannot quote the cause.

    My guess, not checked: the test reads every file under `src/` with `rglob` while other xdist workers run. It can pick up a file that something writes there during the run whose bytes hold `--follow` or `factory-last-line`. Its exception for `documents.py` covers only `domain/documents.py` and `domain/__pycache__/documents.*`.

    This test is flaky, outside this story, and still open. I did not touch it, because it is another story's test. If the factory's check goes red on it again, the human should decide on a separate story to make it deterministic.

    Noticed but not touched:
    - `pyproject.toml:17` still declares `factory-guard`. Removing it is the human's change 1, after this story.
    - A stale, git-ignored `src/factory/adapters/__pycache__/claude_guard.cpython-312.pyc` is left over from the deleted module. It contains neither phrase.
    - The leftover `mutants/` folder still holds copies of the old guard tests. Every mutmut run deletes it first.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
19. factory: started review as self.
20. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'` against the work item: no findings.

    - Acceptance criteria: each criterion has one parametrized test, and each test checks what its criterion says.
      - Criterion 1: `tests/test_hook_removed.py::test_the_hook_s_code_is_gone_and_the_kernel_s_guard_is_kept` covers both missing modules, the four removed names, the two `__all__` entries, `CONFINE_COMMAND == "factory-confine"` and the four kept names.
      - Criterion 2: `test_the_guard_settings_have_no_temporary_folder` checks the four fields in order, a build without `temporary_directory`, and the `ValidationError` with it. The constructor is reached through `type[BaseModel]`.
      - Criterion 3: `tests/application/test_agent_environment_item.py::test_the_agent_environment_checks_the_home_only` has all five rows with their exact details, including the "whatever PATH holds or whether it is there" side.
      - Criterion 4: `tests/entry/test_wiring_agent_environment.py` tests the pass and the missing-home failure through `machine_extras`, with an agent `PATH` that holds only `factory-confine`.
      - Criterion 5: `tests/application/test_undo.py::test_the_guard_refuses_exactly_what_the_undo_puts_back` now judges with `refusal`.
      - The factory's last `make check` was red on two rows of `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode` (entry 16). The coder's rerun was green (entry 18). This diff does not touch that test or what it reads; the flake is still open outside this story.
    - Architecture: the layers hold. The domain loses a constant, an error and a field. `agent_environment_item` in the application layer now checks `HOME` only, through the existing `_home_fault`. `_path_fault` stays for `confinement_item`. The wiring drops the adapter import and the re-exports. Neither deleted module is still referenced in `src` or `tests`. The `temporary_directory` names that remain belong to `InstanceSettings` and the confinement rules, not `GuardSettings`.
    - Security: the diff adds no silencing marker and no secret.
    - Quality: the comments in `confinement_item`, `_probe_request` and `production_environment` are rewritten as the Interface says, and no dead code is left. `pyproject.toml:17` still declares `factory-guard` and now points to a deleted module; removing it is the human's change 1, as the Description says.
    - Work item: the Description matches what was built, and the docs criterion (none, S0003) still holds.

    Earlier tests (item 6):
    - `tests/adapters/test_claude_guard.py` (D): the human's leave, decision 10 (deleted whole).
    - `tests/adapters/test_claude_guard_temporary.py` (D): the human's leave, decision 10 (deleted whole).
    - `tests/entry/test_guard.py` (D): the human's leave, decision 10 (deleted whole).
    - `tests/guard_support.py` (D): the human's leave, decision 10 (deleted whole).
    - `tests/application/test_undo.py` (M): the human's leave, decision 10. `judge` is replaced by `refusal`, and `_payload`, `json` and `Path` are removed. Within the leave.
    - `tests/test_model_configuration.py` (M): the human's leave, decision 10 (the two `claude_guard` `EXCEPTIONS` rows removed). Within the leave.
    - `tests/application/test_agent_environment_item.py` (M): the human's leave, decision 10, as the human's story narrows it in its Interface and criterion 3 (one parametrized test in place of decision 10's two names). Within the leave.
    - `tests/application/test_agent_run_probe.py` (M): the human's leave, decision 10. It now uses `confinement_item(lambda: LANDLOCK_MINIMUM_ABI, environment, find)` and expects `finds == ["factory-confine"]`, exactly as the decision says.
    - `tests/entry/test_wiring_extras_path.py` (M): the human's leave, decision 10 (the two `environment-*` rows removed), plus the standing leave to move a shared test helper (`_item` moved to `tests/wiring_support.py` as `machine_item`). The test keeps its name and what it checks.
    - `tests/entry/test_wiring_handlers.py` (M): the human's leave, decision 10. It now places and finds `factory-confine`, with the parameter `confine_present` and the ids `confine-present`/`confine-absent`, exactly as the decision says.
    - `tests/wiring_support.py` (M): the standing leave to move a shared test helper (it receives `machine_item`).

    Notes:
    - `tests/test_hook_removed.py:91`: criterion 2's rows are module-level functions (`_fields`, `_builds`, `_refuses_a_temporary_folder`) passed as callables. Rows of data with one assertion body would read more plainly.
