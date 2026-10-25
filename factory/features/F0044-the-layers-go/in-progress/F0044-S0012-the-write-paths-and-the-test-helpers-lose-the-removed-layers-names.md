---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-25T20:49:05.732280Z'
  lease_duration: 60
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
