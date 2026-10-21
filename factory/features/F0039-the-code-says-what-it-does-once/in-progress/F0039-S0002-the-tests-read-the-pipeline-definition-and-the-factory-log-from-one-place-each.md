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
  started_at: '2026-10-21T00:47:26.677128Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T00:47:26.670498Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T00:47:26.677128Z'
  stage: intake
---

# The tests read the pipeline definition and the factory log from one place each

## Description

Sixteen test modules define `_definition(boundaries)` with the body of the `definition` fixture of `tests/conftest.py`, `return boundaries.pipeline_reader.parse(PIPELINE_YAML)`, and five define `_log_lines(tmp_path)` with the body of `log_support.log_lines`. `tests/test_shared_fixtures.py` looks only for the spelling `def definition(boundaries: Boundaries)`, so it finds none of them, and every new module copies its neighbour. This story, the tester's under the standing leave of `CLAUDE.md` (*Tests*), adds one shared function for the definition, `pipeline_definition` in a new `tests/definition_support.py`, which the `definition` fixture calls too; replaces the sixteen copies with it (or with the fixture) and the five copies with `log_support.log_lines`; and adds a guard that finds a copy by its body under any name (the feature's decision 5). Every earlier test keeps its name and checks the same thing. Unchanged: the variants with other parameters or another definition, and `tests/test_shared_fixtures.py`. No module under `src/factory/` changes; the coder has nothing to build. The other copied helpers are S0003's.

## Interface

No module under `src/factory/` changes.

`tests/definition_support.py` (new):

```python
def pipeline_definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition, read through the boundaries' reader."""
```

- It returns `boundaries.pipeline_reader.parse(PIPELINE_YAML)` (`PIPELINE_YAML` from `git_support`).

`tests/conftest.py`: the `definition` fixture keeps its name, signature and docstring and returns `pipeline_definition(boundaries)`.

The modules whose `_definition(boundaries: Boundaries) -> PipelineDefinition` is removed, its calls becoming `pipeline_definition(boundaries)` or the `definition` fixture: `tests/application/handlers/test_closed.py`, `tests/application/handlers/test_hand_over.py`, `tests/application/handlers/test_run.py`, `tests/application/test_after_agent.py`, `tests/application/test_board_reader.py`, `tests/application/test_no_state_refusals.py`, `tests/application/test_question_causes_recorded.py`, `tests/application/test_stall_labels.py`, `tests/application/test_stalls.py`, `tests/application/test_tick_stale_branch.py`, `tests/application/test_watcher.py`, `tests/application/test_work_items.py`, `tests/entry/test_watch.py`, `tests/entry/test_wiring_acceptance.py`, `tests/entry/test_wiring_handlers.py` and `tests/entry/test_wiring_human_handlers.py`.

The modules whose `_log_lines(tmp_path: Path)` is removed, its calls becoming `log_lines(tmp_path)` from `log_support`: `tests/application/test_pipeline_loading.py`, `tests/application/test_pipeline_loading_yaml_fault.py`, `tests/application/test_stop_records_service.py`, `tests/application/test_tick_disk.py` and `tests/application/test_tick_stale_branch.py`. A module constant such as `LOG` stays while another line uses it.

Left as they are: the `_definition` helpers with a text parameter or another definition (`test_claims.py`, `handlers/test_closed_send_back.py`, `test_task.py`, `test_stage_finish.py`, `handlers/test_comment_handler.py`, `handlers/test_lookups.py`, `handlers/test_questions.py`), the inline reads of the definition inside other functions, and `_log_lines(state_directory)` of `tests/entry/test_run.py`.

`tests/test_shared_definition.py` (new), the guard:

- A copy of the definition is a function at the top level of a module whose body, a leading docstring left aside, is the one statement `return boundaries.pipeline_reader.parse(PIPELINE_YAML)`, compared as `ast.unparse` prints it, whatever the function's name.
- A copy of the log reading is a function at the top level of a module named `log_lines` or `_log_lines` whose only parameter is `tmp_path`.
- The guard reads every `*.py` file under `tests/` (the guard's own module included), parsed with `ast`.

## Acceptance criteria

1. `pipeline_definition(boundaries)` equals the `definition` fixture's value for the same `boundaries`, and its `acceptance_stage` is `acceptance`.
2. Each shared reading is written in one module (rows of one parametrized test): the modules under `tests/` that hold a copy of the definition are exactly `["definition_support.py"]`; those that hold a copy of the log reading are exactly `["log_support.py"]` (paths relative to `tests/`, sorted).
3. The guard finds a copy by its body, under any name, and nothing else (rows of one parametrized test, each a source text the guard's functions read): `def _definition(boundaries: Boundaries) -> PipelineDefinition:\n    return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n` is a copy of the definition; `def read_it(boundaries):\n    """Read it."""\n    return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n` is one; `def _definition(boundaries, text):\n    return boundaries.pipeline_reader.parse(text)\n` is not; `def _log_lines(tmp_path):\n    return []\n` is a copy of the log reading; `class Rig:\n    def log_lines(self):\n        return []\n` is not; `def _log_lines(state_directory):\n    return []\n` is not.
4. Every earlier test keeps its name and checks the same thing: the tests that `pytest --collect-only` lists in the twenty modules the Interface names are, after the story, the same ids as before it, and all of them pass.
5. `make check` stays green.
6. docs: `docs/project-guide/README.md`, *Shared test helpers*: one line for the new module in the list, in its alphabetical place after `crash_support.py`, in the form of the other lines: `` - `definition_support.py`: `pipeline_definition`, the test remote's pipeline definition read through the boundaries' reader, which the `definition` fixture returns too, for helpers that take no fixtures. `` `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, nothing an operator or a newcomer sees changes and no decision is taken.

## Smoke test

```bash
uv run python - <<'PY'
import ast
from pathlib import Path
body = "return boundaries.pipeline_reader.parse(PIPELINE_YAML)"
found = set()
for path in Path("tests").rglob("*.py"):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef):
            rest = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
            if (len(rest) == 1 and ast.unparse(rest[0]) == body) or (node.name in ("log_lines", "_log_lines") and [a.arg for a in node.args.args] == ["tmp_path"]):
                found.add(path.as_posix())
print(sorted(found))
PY
```
Expect: one line, `['tests/definition_support.py', 'tests/log_support.py']` (before the story it lists 22 modules, `tests/conftest.py` among them)

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
TMPDIR="$d" uv run pytest --no-header --tb=short -p no:cacheprovider tests/test_shared_definition.py tests/test_shared_fixtures.py tests/application/test_board_reader.py tests/application/test_tick_disk.py > "$d/out" 2>&1
echo "exit $?"
```
Expect: one line, `exit 0`

```bash
grep -c '^- `definition_support.py`: `pipeline_definition`' docs/project-guide/README.md
```
Expect: one line, `1` (before the story, `0`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
