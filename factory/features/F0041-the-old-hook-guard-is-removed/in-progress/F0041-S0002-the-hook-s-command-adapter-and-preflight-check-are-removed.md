---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 348
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-20T10:52:01.792838Z'
  lease_duration: 60
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
