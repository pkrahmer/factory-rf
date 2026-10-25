---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 456
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T20:49:05.725322Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T20:49:05.732280Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T20:49:25.382137Z'
  stage: intake
  run: 1885233b036e46639b4264ebd2851dc2
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T20:49:45.712822Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T20:53:25.456841Z'
  stage: tests
  run: ee9e4662e05d40298b40f9d8939a0953
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T20:53:46.032189Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-25T20:56:25.783407Z'
  stage: doing
  run: aa079c481a3a4c36ac5ee3c2ffefa8c5
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-25T20:56:46.553967Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-25T20:57:30.549752Z'
  stage: review
  run: c7e90b722ac44ba69af3cb1ee1fde9a9
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-25T20:57:51.039362Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-25T20:58:13.181126Z'
  stage: doing
  run: 492a7f6c74664c048b8291003dd09f0f
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-25T20:58:33.443307Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-25T21:01:11.506938Z'
  stage: tests
  run: 1c353b0afaa0463799d49f91da7fab35
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-25T21:01:32.309430Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-25T21:04:10.918835Z'
  stage: doing
  run: 7e0150668ece43cb979a192adfea0d08
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-25T21:04:32.426481Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-25T21:05:20.385171Z'
  stage: review
  run: 8c3a0f5668044c0e9dc8e3d90c6d48b9
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-25T21:05:40.777799Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-25T21:06:21.865171Z'
  stage: docs
  run: 6a3c6802722a4a3d96bd74837530b775
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-25T21:06:42.624671Z'
  stage: smoke-test
- number: 21
  speaker: smoke-tester
  kind: result
  at: '2026-10-25T21:07:07.222389Z'
  stage: smoke-test
  run: 0341a9e4d53940f1becea69dba7818cc
---

# The write paths and the test helpers lose the removed layers' names

<!-- proposed by feature acceptance of 2026-10-25; refine before starting -->

## Description

F0044 removed the kernel's write guard and the sealed runs, but four names of them are left on code that serves the mechanism that replaced them. The DTO of the write paths is still `GuardSettings` (`factory.domain.agent_runs`), and `refusal` takes it as `guard`. The project guide's file on the write paths and the take is still `docs/project-guide/write-guard.md`. Two shared test helpers that every runtime and run test imports are still `tests/confine_support.py` and `tests/sealed_run_support.py`. `confine_support.Layout` also keeps the field `temporary_root`, which no test reads since the wrapper's run folder went in F0044-S0001. A later reader who meets these names looks for a guard, a confinement or a seal that no longer exists, against the feature's goal of one mechanism instead of eight. This story renames them and drops the unused field. Every behaviour stays as it is: the same fields, the same refusal rule, the same helpers with the same contents. The rule of the write paths (`refusal`, `PROTECTED_PATHS`) keeps its meaning; F0044 put it out of scope as a behaviour, and this story changes only names. The records contract is untouched, because `GuardSettings` is in none of its schemas. Test modules named after a removed layer whose tests check behaviour that still exists (`tests/application/test_sealed_runs_runner.py`, `tests/application/test_probe_nested_repository.py`, `tests/test_kernel_guard_removed.py`) keep their names; renaming them is left to the human.

## Interface

`factory.domain.agent_runs` (`domain`): `GuardSettings` becomes `WritePathSettings`, with the same docstring, fields (`root: AbsolutePath`, `write_paths: list[str]`, `protected_paths: list[str]`) and configuration. No alias under the old name stays.

```python
class WritePathSettings(BaseModel):
    """Where an agent may write: the root, write paths and protected paths."""

def refusal(path: str, settings: WritePathSettings) -> str | None: ...           # factory.domain.write_paths
def is_refused(path: str, settings: WritePathSettings, work_item_path: str) -> bool: ...  # factory.application.take
class WritePathService:
    def at(self, stage_start: StageStart, work_item_path: str) -> WritePathSettings: ...  # factory.application.write_paths
```

- `factory.domain.write_paths.refusal`: the parameter `guard` becomes `settings`; the result for every path is unchanged.
- `factory.application.take` and `factory.application.write_paths` import `WritePathSettings`; nothing else in them changes.
- No module under `src/factory` names `GuardSettings`.

Tests (the leave is decision 42 of `feature.md`):

- Renamed whole, with the same contents: `tests/confine_support.py` becomes `tests/run_layout_support.py`, and `tests/sealed_run_support.py` becomes `tests/agent_run_support.py`. Every importer changes its import line only: `tests/conftest.py`, `tests/podman_support.py`, `tests/zfs_support.py`, `tests/test_test_children.py`, `tests/adapters/test_agent_launch_login.py`, `tests/adapters/test_calls_as_the_factory_user.py`, `tests/adapters/test_opencode_runtime_launch.py`, `tests/adapters/test_runtimes_without_wrapper.py`, `tests/adapters/test_claude_runtime_no_hook.py`, `tests/application/test_container_environment.py`, `tests/application/test_sealed_runs_runner.py`, `tests/application/test_probe_nested_repository.py`.
- `run_layout_support.Layout` loses `temporary_root`, and `build_layout` stops making `<tmp_path>/tmp`. The module docstring and the class docstring stop naming a temporary root.
- `GuardSettings` becomes `WritePathSettings` in `tests/application/test_write_paths_guard.py`, `tests/application/test_write_paths.py`, `tests/domain/test_agent_runs.py`, `tests/domain/test_project_agent_paths.py`, `tests/domain/test_write_paths.py` and `tests/domain/test_nested_claude_paths.py`. In `tests/test_kernel_guard_removed.py` and `tests/test_hook_removed.py` the same rename applies; their rows that check that no guard field and no `GuardSettingsInvalid` remains keep what they check.
- New: `tests/test_removed_layer_names.py`, carrying criteria 1 and 2.
- Every changed test keeps its name and checks the same thing.

## Acceptance criteria

1. The renamed names (rows of one parametrized test): `factory.domain.agent_runs` has the attribute `WritePathSettings` and not `GuardSettings`. `WritePathSettings.model_fields` lists `root`, `write_paths` and `protected_paths`, in that order. `inspect.signature(factory.domain.write_paths.refusal).parameters` lists `path` and `settings`, and does not list `guard`.
2. No module under `src/factory` holds the word `GuardSettings`, and none under `tests/` imports `confine_support` or `sealed_run_support` (rows of one parametrized test over the files' text). A file under `src/factory` that a row of the test writes with `GuardSettings` in it, under `tmp_path` and given to the same search function, is found. This is the failing side.
3. The rule is unchanged (rows of one parametrized test): with `WritePathSettings(root=Path("/work/checkout"), write_paths=["src/*"], protected_paths=["factory/pipeline.yml"])`, `refusal("src/a.py", settings)` is `None`. `refusal("docs/a.md", settings)` and `refusal("factory/pipeline.yml", settings)` each give the refusal text that `refusal` gives today for those paths.
4. `run_layout_support.Layout` has the fields `checkout`, `home`, `state`, `stand_in` and `shell_bin`, and no field `temporary_root`. `build_layout(tmp_path)` makes no folder `tmp_path / "tmp"`.
5. `make check` stays green.
6. docs: `docs/project-guide/write-guard.md` is renamed to `docs/project-guide/write-paths.md`, and the index `docs/project-guide/README.md` and every link to it in `docs/` follow. In the index's *Shared test helpers*, the lines of `confine_support.py` and `sealed_run_support.py` name the new modules. In the project guide, every `GuardSettings` becomes `WritePathSettings`. `docs/decisions.md` keeps its history: the entries name `GuardSettings` as they were written, and none changes. `README.md` and `docs/operator-guide.md`: none, because neither names these.

## Smoke test

```bash
uv run python -c 'import factory.domain.agent_runs as m, inspect, factory.domain.write_paths as w; print(hasattr(m, "WritePathSettings"), hasattr(m, "GuardSettings"), list(inspect.signature(w.refusal).parameters))'
```
Expect: `True False ['path', 'settings']`

```bash
for f in tests/confine_support.py tests/sealed_run_support.py docs/project-guide/write-guard.md tests/run_layout_support.py tests/agent_run_support.py docs/project-guide/write-paths.md; do [ -e "$f" ] && echo "present $f" || echo "gone $f"; done
```
Expect: six lines: `gone tests/confine_support.py`, `gone tests/sealed_run_support.py`, `gone docs/project-guide/write-guard.md`, `present tests/run_layout_support.py`, `present tests/agent_run_support.py`, `present docs/project-guide/write-paths.md`

```bash
grep -rl "GuardSettings" src/factory --include=*.py | wc -l
```
Expect: `0`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`factory.domain.agent_runs.WritePathSettings`, `factory.domain.write_paths.refusal(path, settings)`, `take.is_refused`, `WritePathService.at`) and lists the renamed test helpers, every importer and every test that changes. I checked `tests/confine_support.py` itself: `Layout` has the fields `checkout`, `home`, `state`, `temporary_root`, `stand_in` and `shell_bin`, so dropping `temporary_root` leaves the five fields criterion 4 names. The Interface states no behaviour (conversion, format, ordering or default) that lacks a criterion.
   Criteria: each can be tested by one test function. Criteria 1 and 2 are parametrized rows. Criterion 2 has its failing side: a planted `src/factory` file that contains `GuardSettings` must be found. Criterion 3 covers the passing path and both refusals, so the rule's unchanged behaviour has both sides. Criterion 4 has the field list, the absence of `temporary_root`, and the absent `tmp` folder. Criteria 5 (`make check`) and 6 (`docs:`) are last. The leave for the tests that change is decision 42 of `feature.md`.
   Smoke test: three runnable commands with no pytest call, so the `-q` rule does not apply. Each `Expect:` can be checked against the output: `True False ['path', 'settings']`, six present/gone lines, and `0`.
   Architecture: a rename within `factory.domain` and `factory.application`, with no new layer, interface or dependency. The docs and test helpers are within the write paths of the documenter and the tester. `docs/decisions.md` keeps its history.
   Scope: within F0044's goal of removing the removed layers' names. The refusal rule is unchanged, which matches "Out of scope" in `feature.md`. The three test modules named after removed layers keep their names. Decision 42 of `feature.md` adds this story and gives the leave.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1–4 and carried out the test renames the Interface lists. Decision 42 of `feature.md` gives the leave for them.

   Criterion → test:
   - criterion 1: tests/test_removed_layer_names.py::test_the_write_paths_carry_their_new_names (rows: new-name, old-name, fields, refusal-parameters, refusal-no-guard)
   - criterion 2: tests/test_removed_layer_names.py::test_no_file_holds_a_removed_layer_s_name (rows: source-guard-settings, tests-confine, tests-sealed, planted-is-found; the last row writes `src/factory/planted.py` holding `GuardSettings` under tmp_path, and that file must be found. This is the failing side.)
   - criterion 3: tests/test_removed_layer_names.py::test_the_rule_of_the_write_paths_is_unchanged (rows: writable → None, outside → "docs/a.md is outside the write paths of this stage.", protected → "factory/pipeline.yml is owned by the human; a change there is a question.", which are the texts `refusal` gives today)
   - criterion 4: tests/test_removed_layer_names.py::test_the_run_layout_has_no_temporary_root
   - criteria 5 and 6: none (make check; docs for the documenter)

   Files created: tests/test_removed_layer_names.py; tests/run_layout_support.py (was tests/confine_support.py; `temporary_root` and the `tmp` folder are dropped, and the docstrings no longer name a temporary root); tests/agent_run_support.py (was tests/sealed_run_support.py, contents unchanged). Both old files are removed.

   Earlier test files I changed, under the leave of decision 42:
   - Import line only: tests/conftest.py, tests/podman_support.py, tests/zfs_support.py, tests/test_test_children.py, tests/adapters/test_agent_launch_login.py, test_calls_as_the_factory_user.py, test_opencode_runtime_launch.py, test_runtimes_without_wrapper.py, test_claude_runtime_no_hook.py, tests/application/test_container_environment.py, test_sealed_runs_runner.py, test_probe_nested_repository.py. Ruff's isort moved each renamed import to its sorted place within the same import block.
   - `GuardSettings` → `WritePathSettings`: tests/application/test_write_paths_guard.py, tests/application/test_write_paths.py, tests/domain/test_agent_runs.py (ruff format rewrapped one line), tests/domain/test_project_agent_paths.py, tests/domain/test_write_paths.py, tests/domain/test_nested_claude_paths.py, tests/test_kernel_guard_removed.py, tests/test_hook_removed.py. In test_hook_removed.py the `GuardSettingsInvalid` row (id settings-error) is kept as it was. The guard-settings row now checks that `WritePathSettings` is present. All test names and ids are unchanged.

   `make test` fails for the right reason: collection ImportErrors in the modules that import `WritePathSettings` from `factory.domain.agent_runs`, which does not exist yet (among them tests/domain/test_write_paths.py, test_project_agent_paths.py, tests/test_hook_removed.py, tests/test_kernel_guard_removed.py, and the new module). The module the runner could not import is `factory.domain.agent_runs.WritePathSettings`; the module itself exists but lacks the name. `make lint` is green.

   Open for the coder: rename `GuardSettings` in src (agent_runs, write_paths, take, write_paths service) and rename `refusal`'s parameter `guard` to `settings`. One note: tests/adapters/test_runtimes_without_wrapper.py keeps its rows that check the runtimes' `__init__` has no `temporary_root` parameter. Those rows are about the runtimes, not the Layout, so I left them.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/test_kernel_guard_removed.py - ImportError while importing test module '/work/checkout/tests/test_kernel_guard_removed.py'.
6. factory: started doing as self.
7. coder: I renamed `GuardSettings` to `WritePathSettings` in `src/factory/domain/agent_runs.py` and changed its importers: `src/factory/domain/write_paths.py`, `src/factory/application/take.py` and `src/factory/application/write_paths.py`. The new class has the same docstring, fields and configuration as the old one, and no alias under the old name remains. `refusal`'s parameter `guard` is now `settings`, and its body is unchanged. In `WritePathService.at` the docstring now says "The write path settings of the claimed stage" instead of "The guard settings", so it matches the new name. A search for `guard` across `src/factory` now finds nothing.

   `make check` is green, and the tester's tests pass unchanged.

   Main choice: I only renamed names and changed nothing else. The alternative I rejected was moving `WritePathSettings` from `agent_runs` into `factory.domain.write_paths`, next to the rule that reads it. That would put the model beside its rule, but the Interface keeps it in `factory.domain.agent_runs`, and the move would be a restructuring outside this story.

   Refactor: I read the diff and there was nothing to change.

   The journal changed nothing in the meaning of the task, so `## Description` is as it was. The records contract is untouched, because `GuardSettings` is in none of its schemas.

   Noticed, not touched:
   - The project guide's `docs/project-guide/write-guard.md` and its mentions of `GuardSettings`. Criterion 6 gives those to the documenter.
   - The test modules named after removed layers, which the Description leaves to the human.

   `check`: check: green
   `duplicates`: duplicates: 8 new, 35 known, 3 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item. Criteria 1 to 4 each have a parametrized test in `tests/test_removed_layer_names.py`, and each test checks what its criterion says. Criterion 2's failing side is the `planted-is-found` row. Criterion 3 checks the writable path and both refusal texts. Criterion 4 checks the five fields and that `tmp` is not created. The coder's `make check` was green (entry 7).

   The `src/factory` change only renames names. `WritePathSettings` keeps the docstring, fields and config of `GuardSettings`. `refusal`'s body is unchanged apart from the parameter. No `GuardSettings`, `confine_support` or `sealed_run_support` is left under `src` or `tests`. The only remaining hits are the `GuardSettingsInvalid` row and the runtimes' `temporary_root` rows, which the Interface keeps. Architecture and security groups hold: the change is within the layers, adds no marker and no dependency.

   The Description matches what was built, and criterion 6 still describes what the documenter has to do.

   Findings:
   1. `tests/test_removed_layer_names.py:23` (`_files_holding`) copies `search_support.modules_matching` (`tests/search_support.py:10`): same regex compile, `rglob("*.py")`, read and sorted relative paths. The only difference is a root parameter. `SOURCE` at line 15 also rebuilds `source_search.SRC` (`tests/source_search.py:8`). Fix: give `modules_matching` a root argument that defaults to `TESTS`, so its earlier callers stay unchanged. Then use it for all four rows (the planted row's tmp root included, so criterion 2's "same search function" still holds), and import `SRC` from `source_search`. This is the tester's change. If the tester judges that adding a parameter to `search_support` goes beyond the standing leave, it is a question to the human.

   Earlier tests changed. The leave for all of them is the human's decision 42 in `feature.md`, which names S0012's Interface:
   - tests/confine_support.py → tests/run_layout_support.py: decision 42 (renamed whole, `temporary_root` and the `tmp` folder dropped, docstrings changed to match)
   - tests/sealed_run_support.py → tests/agent_run_support.py: decision 42 (renamed whole, unchanged)
   - tests/conftest.py: decision 42 (import line)
   - tests/podman_support.py: decision 42 (import line)
   - tests/zfs_support.py: decision 42 (import line)
   - tests/test_test_children.py: decision 42 (import line)
   - tests/adapters/test_agent_launch_login.py: decision 42 (import line)
   - tests/adapters/test_calls_as_the_factory_user.py: decision 42 (import line)
   - tests/adapters/test_opencode_runtime_launch.py: decision 42 (import line)
   - tests/adapters/test_runtimes_without_wrapper.py: decision 42 (import line)
   - tests/adapters/test_claude_runtime_no_hook.py: decision 42 (import line)
   - tests/application/test_container_environment.py: decision 42 (import line)
   - tests/application/test_sealed_runs_runner.py: decision 42 (import line)
   - tests/application/test_probe_nested_repository.py: decision 42 (import line)
   - tests/application/test_write_paths_guard.py: decision 42 (`GuardSettings` → `WritePathSettings`)
   - tests/application/test_write_paths.py: decision 42 (`GuardSettings` → `WritePathSettings`)
   - tests/domain/test_agent_runs.py: decision 42 (`GuardSettings` → `WritePathSettings`, reformatted)
   - tests/domain/test_project_agent_paths.py: decision 42 (`GuardSettings` → `WritePathSettings`)
   - tests/domain/test_write_paths.py: decision 42 (`GuardSettings` → `WritePathSettings`)
   - tests/domain/test_nested_claude_paths.py: decision 42 (`GuardSettings` → `WritePathSettings`)
   - tests/test_kernel_guard_removed.py: decision 42 (`GuardSettings` → `WritePathSettings`, row ids kept)
   - tests/test_hook_removed.py: decision 42 (`GuardSettings` → `WritePathSettings`; the `GuardSettingsInvalid` row is kept as it was)
10. factory: started doing as self.
11. coder: Round 1. The reviewer's only finding (entry 9, finding 1) is about tests and asks for no code change, so I changed no code. The `src/factory` rename from entry 7 stays as it was.

    The change for the tester: in `tests/test_removed_layer_names.py`, remove the copied helper `_files_holding` (line 23) and the rebuilt `SOURCE` constant (line 15). Instead, give `search_support.modules_matching` (`tests/search_support.py:10`) a `root` argument that defaults to `TESTS`, so its earlier callers stay unchanged. Then use it for all four rows of `test_no_file_holds_a_removed_layer_s_name`, the planted row's `tmp_path` root included, so that criterion 2's "same search function" still holds. Import `SRC` from `source_search` (`tests/source_search.py:8`) in place of `SOURCE`.

    I checked the finding against the code. `_files_holding` repeats what `modules_matching` already does: it compiles the regex, runs `rglob("*.py")`, reads each file and returns sorted relative paths. Only the root parameter is new. `SOURCE` rebuilds `source_search.SRC`. One thing for the tester to settle: `modules_matching` takes a required `leave_out` argument and compiles with `re.DOTALL` as well as `re.MULTILINE`. The anchored import patterns of criterion 2 should behave the same under `DOTALL`, but the tester should check that.

    The standing leave in `CLAUDE.md` covers moving a shared helper. Adding a parameter to `search_support` may go beyond that leave, and the reviewer said so. If the tester judges that it does, it is a question to the human.

    The journal did not change the meaning of the task, so `## Description` is as it was. I noticed nothing else and touched nothing else.
12. factory: started tests as self.
13. tester: Round 1, test change: the reviewer's finding 1 (entry 9), which the coder passed on in entry 11. No human answer was needed. The change folds a copy of a shared helper back into that helper, which falls under the standing leave in `CLAUDE.md`. Every earlier caller keeps its name and its checks.

    What I changed:
    - `tests/search_support.py`: `modules_matching(pattern, leave_out, root: Path = TESTS)` now takes an optional `root`. Paths are given relative to `root`, and the docstring says so. Its three earlier callers (`tests/test_shared_test_helpers.py`, `tests/test_docker_path_removed.py`, `tests/test_opencode_shared_steps.py`) pass no root, so they search `tests` exactly as before. I did not edit those three files.
    - `tests/test_removed_layer_names.py`: removed the copied `_files_holding` and the rebuilt `SOURCE`. It now imports `SRC` from `source_search` and `TESTS` and `modules_matching` from `search_support`. All four rows of `test_no_file_holds_a_removed_layer_s_name` go through `modules_matching(pattern, THIS, root_of(tmp_path))`, the planted `tmp_path` row included. So criterion 2's "same search function" still holds, and its failing side is still the `planted-is-found` row.
    - The `re.DOTALL` question from entry 11: the patterns of criterion 2 (`GuardSettings`, and `^\s*(?:from|import)\s+<module>\b`) contain no `.`, so `DOTALL` changes nothing for them. `leave_out=THIS` keeps the test's own source out of the search, and none of its rows would match it anyway.

    Criterion → test (unchanged):
    - criterion 1: tests/test_removed_layer_names.py::test_the_write_paths_carry_their_new_names
    - criterion 2: tests/test_removed_layer_names.py::test_no_file_holds_a_removed_layer_s_name
    - criterion 3: tests/test_removed_layer_names.py::test_the_rule_of_the_write_paths_is_unchanged
    - criterion 4: tests/test_removed_layer_names.py::test_the_run_layout_has_no_temporary_root
    - criteria 5 and 6: no test (criterion 5 is `make check`, criterion 6 is the documenter's)

    No files created. I changed one earlier test file, `tests/search_support.py`, under the standing leave for shared test helpers. Every module imported fine, since the code already exists. `make test` is green with 99.55 % coverage, and `make lint` is green.

    `lint`: lint: green (0.2 s)
    `test`: test: green (60.7 s)
14. factory: started doing as self.
15. coder: Round 1, after the tester's change. In entry 13 the tester made the test change from the reviewer's finding 1 (entry 9): `tests/search_support.py` `modules_matching` now takes a `root` argument, and `tests/test_removed_layer_names.py` uses it and `source_search.SRC` in place of its own copies. That finding asked for no code change, so I changed no code. The `src/factory` rename from entry 7 stays as it was: `src/factory/domain/agent_runs.py`, `src/factory/domain/write_paths.py`, `src/factory/application/take.py`, `src/factory/application/write_paths.py`.

    Main choice: I left the code as it was and did not touch the tester's change. The alternative was to look at the test side again, and I rejected it because changing tests is not the coder's job.

    Refactor: no new diff of mine to read, so nothing to change.

    `make check`: the first run stopped at `make sast` with `Error 139` (a segfault, `Makefile:51: sast`). A second `make sast` on its own was green (1.9 s), and the full `make check` after it was green: lint, types, layers, sast, secrets, licenses, test (61.2 s), `check: green`. The segfault looks like a crash in the tool, not something from this work item. I note it in case it comes back.

    The journal did not change the meaning of the task, so `## Description` is as it was.

    Noticed, not touched: as before, `docs/project-guide/write-guard.md` and the `GuardSettings` mentions in the project guide. Criterion 6 gives those to the documenter.

    `check`: check: green
    `duplicates`: duplicates: 8 new, 35 known, 3 gone
16. factory: started review as self.
17. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'` against the work item. I read the code itself rather than the earlier entries.

    no findings

    What I checked:
    - Criteria 1 to 4 each have a parametrized test in `tests/test_removed_layer_names.py`, and each test checks what its criterion says. Criterion 1 is covered by the rows new-name, old-name, fields, refusal-parameters and refusal-no-guard. Criterion 2 is covered by source-guard-settings, tests-confine, tests-sealed and planted-is-found. The planted-is-found row is the failing side, and it goes through the same `search_support.modules_matching` as the other three rows. Criterion 3 checks the writable path and both refusal texts, and those texts match `refusal` in `src/factory/domain/write_paths.py`. Criterion 4 checks the five fields and that no `tmp` folder is made.
    - The coder's `make check` was green (entry 15). The one-off `make sast` segfault in that entry was followed by a green rerun and a green full check.
    - Round 0's finding 1 is fixed. The copied `_files_holding` and the rebuilt `SOURCE` are gone. The test now uses `modules_matching(..., root)` and `source_search.SRC`.
    - `src/factory`: names only. `WritePathSettings` keeps the docstring, fields and config. `refusal(path, settings)` keeps its body. `take.is_refused` and `WritePathService.at` change only the type and one docstring word. No alias is left, and no `GuardSettings` is left under `src`. No import of `confine_support` or `sealed_run_support` is left under `tests`.
    - Groups 2 and 3 hold: the layers are unchanged, and there is no new dependency, marker or baseline entry.
    - Group 5 holds: the Description matches what was built, and criterion 6 still describes the documenter's work (the guide's file rename, its index lines, `GuardSettings` in the guide).

    Earlier tests changed:
    - tests/confine_support.py → tests/run_layout_support.py: decision 42 of `feature.md` (renamed whole; `temporary_root`, the `tmp` folder and the docstrings' temporary root dropped)
    - tests/sealed_run_support.py → tests/agent_run_support.py: decision 42 (renamed whole, R100)
    - tests/conftest.py: decision 42 (import line)
    - tests/podman_support.py: decision 42 (import line)
    - tests/zfs_support.py: decision 42 (import line)
    - tests/test_test_children.py: decision 42 (import line)
    - tests/adapters/test_agent_launch_login.py: decision 42 (import line)
    - tests/adapters/test_calls_as_the_factory_user.py: decision 42 (import line)
    - tests/adapters/test_opencode_runtime_launch.py: decision 42 (import line)
    - tests/adapters/test_runtimes_without_wrapper.py: decision 42 (import line; its `temporary_root` rows are about the runtimes and stay)
    - tests/adapters/test_claude_runtime_no_hook.py: decision 42 (import line)
    - tests/application/test_container_environment.py: decision 42 (import line)
    - tests/application/test_sealed_runs_runner.py: decision 42 (import line)
    - tests/application/test_probe_nested_repository.py: decision 42 (import line)
    - tests/application/test_write_paths_guard.py: decision 42 (`GuardSettings` → `WritePathSettings`)
    - tests/application/test_write_paths.py: decision 42 (`GuardSettings` → `WritePathSettings`)
    - tests/domain/test_agent_runs.py: decision 42 (`GuardSettings` → `WritePathSettings`, rewrapped)
    - tests/domain/test_project_agent_paths.py: decision 42 (`GuardSettings` → `WritePathSettings`)
    - tests/domain/test_write_paths.py: decision 42 (`GuardSettings` → `WritePathSettings`)
    - tests/domain/test_nested_claude_paths.py: decision 42 (`GuardSettings` → `WritePathSettings`)
    - tests/test_kernel_guard_removed.py: decision 42 (`GuardSettings` → `WritePathSettings`, row ids kept)
    - tests/test_hook_removed.py: decision 42 (`GuardSettings` → `WritePathSettings`; the guard-settings row now checks that `WritePathSettings` is present; the `GuardSettingsInvalid` row is unchanged)
    - tests/search_support.py: the standing leave for shared test helpers. `modules_matching` gains an optional `root` that defaults to `TESTS`, so the new test uses the shared helper instead of a copy. Its three earlier callers (`test_shared_test_helpers.py`, `test_docker_path_removed.py`, `test_opencode_shared_steps.py`) are unchanged and check the same thing. A judgement call for the human to see at approval: this extends the shared helper rather than only moving it there, and it is the narrowest change that avoids the copy round 0 counted as a finding.
18. factory: started docs as self.
19. documenter: Docs, round 1. Only documents changed, so I did not run `make check`; the factory's check after this stage decides.

    Files changed:
    - `docs/project-guide/write-guard.md` → `docs/project-guide/write-paths.md` (git mv): the criterion 6 rename. Inside it `GuardSettings` is now `WritePathSettings`, `refusal(path, guard)` is `refusal(path, settings)`, and `guard.protected_paths` is `settings.protected_paths`, as the code has them. The history lines about the kernel's write guard stay, because that is what F0044 removed.
    - `docs/project-guide/README.md`: the index entry names `write-paths.md`. In *Shared test helpers*, `confine_support.py` is now `run_layout_support.py` and `sealed_run_support.py` is now `agent_run_support.py`.
    - `docs/project-guide/stage-environment.md`, `docs/project-guide/git-and-hosting.md`: their links to `write-guard.md` now point to `write-paths.md`.
    - `docs/project-guide/agents.md`: the *AgentRunRequest* bullet no longer lists `guard: optional GuardSettings`. `AgentRunRequest` has no such field (`src/factory/domain/agent_runs.py:84`); it has `resume_session`, which the bullet now names.
    - `docs/project-guide/stages.md`: `TaskContext` has no `GuardSettings` field and `compose` sets no `guard` (`src/factory/application/task.py:33`). I removed both claims, and I wrote "the `WritePathSettings`" in launch step 7 and dropped "guard" from step 8.

    I departed from the letter of criterion 6 in the last two files: it says every `GuardSettings` becomes `WritePathSettings`, but in `agents.md` and `stages.md` the text was wrong beyond the name, so I removed it. If the human wants the field described, the code would have to gain it first.

    `docs/decisions.md` is unchanged, as the criterion says. `README.md` and `docs/operator-guide.md` hold none of the old names, and I cross-read them against the diff. A search of `README.md`, `docs/project-guide/` and the operator guide finds no `GuardSettings`, `write-guard`, `confine_support` or `sealed_run_support`.

    Stale text I noticed and did not touch, because it is not about the names this story renames:
    - `docs/operator-guide.md:701` says `agent-run-probe` runs "with … a guard that gives no write path". The guard went with F0044, so this probably needs rewording.
    - `docs/operator-playbook.md:116` has the row "An agent's write refused under the guard". The playbook is the human's file.
    - `docs/operator-playbook.md:32` and `:94` call F0019 "the write guard by the kernel", which is history.
    - `docs/project-guide/README.md:60` says "a later guard calls `modules_assigning`", which is loose wording about test guards and not a stale name.

    No findings for the coder.

    `check`: check: green (not run again: passed on tree 92c6af88fac5 at 2026-10-25T21:03:03Z)
    `secrets`: secrets: green (1.7 s)
    `documents`: documents ok
20. factory: started smoke-test as self.
21. smoke-tester: I ran the three smoke test commands from the repository root, as written and in order. All three met their `Expect:` lines. I fixed nothing.

    Command 1: the module attributes and the parameters of `refusal`
    ```
    True False ['path', 'settings']
    ```
    (uv also printed `Bytecode compiled 4164 files in 90ms` before this line.) Met: `True False ['path', 'settings']`.

    Command 2: which files are gone and which are present
    ```
    gone tests/confine_support.py
    gone tests/sealed_run_support.py
    gone docs/project-guide/write-guard.md
    present tests/run_layout_support.py
    present tests/agent_run_support.py
    present docs/project-guide/write-paths.md
    ```
    Met: the six lines match the expectation exactly.

    Command 3: `GuardSettings` under `src/factory`
    ```
    0
    ```
    Met: `0`.

    Checking the acceptance criteria against the code:
    - Criterion 4: `run_layout_support.Layout` has exactly the fields `checkout`, `home`, `state`, `stand_in` and `shell_bin`.
    - No file under `docs/project-guide/` still contains `write-guard`, `GuardSettings`, `confine_support` or `sealed_run_support`.
    - Under `tests/`, the only remaining mentions of `confine_support`, `sealed_run_support` and `temporary_root` are in tests that check those names are gone (`tests/test_removed_layer_names.py`, `tests/adapters/test_runtimes_without_wrapper.py`).

    The smoke test contradicts no criterion. I did not run `make check` (criterion 5) here; the factory's checks cover it.

    Findings: none.
