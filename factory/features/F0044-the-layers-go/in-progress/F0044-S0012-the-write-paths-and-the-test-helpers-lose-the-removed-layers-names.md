---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 456
comments_read: []
handed_over: null
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
