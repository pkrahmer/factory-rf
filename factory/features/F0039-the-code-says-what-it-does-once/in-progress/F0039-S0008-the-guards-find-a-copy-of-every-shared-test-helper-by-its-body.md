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
  started_at: '2026-10-21T08:37:29.100982Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T08:37:29.094997Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T08:37:29.100982Z'
  stage: intake
---

# The guards find a copy of every shared test helper by its body

<!-- proposed by feature acceptance of 2026-10-21; refine before starting -->

## Description

The feature's Goal and its decision 5 promise a guard that finds a copy of a shared test helper "by its body or its parameters, not by its name, so the next copy under a new name is found too". Only the definition guard of `tests/test_shared_definition.py` does that. The log reading rule in the same module matches the names `log_lines` and `_log_lines`. `tests/test_shared_branch_helpers.py` matches the name without one leading `_` together with the parameter annotations. So a copy with the very body of `log_lines`, `pushed`, `pushed_state`, `remote_document` or `push_state` passes both guards under another name. The feature's acceptance planted two such copies and both guards stayed green. A search by body over `tests/` on 2026-10-21 found one that is already there: `_branch_document(boundaries: Boundaries, checkout: GitCli)` of `tests/application/handlers/test_reject.py` (written by F0014) has the body of `branch_reading.remote_document` and reads the same `BRANCH` and `PATH` values. This story adds a guard that finds a copy of those five helpers by its body, whatever its name and parameters. It moves the one copy it finds to `remote_document` under the standing leave of `CLAUDE.md` (*Tests*). The tester does the work; no module under `src/factory/` changes and the coder has nothing to build. Unchanged: `tests/test_shared_definition.py`, `tests/test_shared_branch_helpers.py` and `tests/test_shared_fixtures.py` (their rules stay and still catch a copy by name), `error_posts`, which has no guard (decision 5), and every variant the feature's *Out of scope* names.

## Interface

No module under `src/factory/` changes.

`tests/test_shared_bodies.py` (new), the guard:

```python
SHARED: dict[str, str]  # helper name -> its module, relative to tests/


def body_of(function: ast.FunctionDef) -> str:
    """The function's statements, a leading docstring left aside, each as `ast.unparse` prints it."""


def shared_bodies(root: Path) -> dict[str, str]:
    """The body of each helper `SHARED` names, read with `ast` from its own module under `root`."""


def copies(source: str, bodies: Mapping[str, str]) -> list[str]:
    """The helpers that the top-level functions of `source` copy, by their body."""
```

- `SHARED` is `{"log_lines": "log_support.py", "pushed": "stage_run_support.py", "pushed_state": "stage_run_support.py", "remote_document": "branch_reading.py", "push_state": "branch_reading.py"}`.
- `body_of` joins the statements with a newline. A first statement that is a string constant is the docstring and is left out.
- A copy is a function at the top level of a module whose `body_of` equals a helper's body, whatever the function's name, parameters, annotations and decorators.
- A function in a class, or one whose body holds one more statement, is not a copy.
- The bodies come from the shared modules themselves, so a change to a shared helper changes what counts as a copy.
- The guard reads every `*.py` file under `tests/`, the guard's own module included.

`tests/application/handlers/test_reject.py` (standing leave): `_branch_document` is removed and its calls become `remote_document(boundaries, checkout)` from `branch_reading`. `_branch_state` stays and calls `remote_document`. Every test keeps its name and checks the same thing.

## Acceptance criteria

1. Each of the five helpers is written in one module (rows of one parametrized test over `tests/`, paths relative to `tests/`, sorted): `log_lines` → `["log_support.py"]`; `pushed` → `["stage_run_support.py"]`; `pushed_state` → `["stage_run_support.py"]`; `remote_document` → `["branch_reading.py"]`; `push_state` → `["branch_reading.py"]`.
2. The guard finds a copy by its body and nothing else (rows of one parametrized test, each a source text read by `copies` against `shared_bodies(TESTS)`). `def _the_log(tmp_path: Path) -> list[str]:\n    log = tmp_path / "state" / "factory.log"\n    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []\n` → `["log_lines"]`. The same with a docstring as its first statement → `["log_lines"]`. The same under the decorator `@pytest.fixture` → `["log_lines"]`. `def _branch_document(boundaries, checkout):\n    checkout.fetch()\n    text = checkout.show_file(f"origin/{BRANCH}", PATH)\n    assert text is not None\n    return boundaries.work_item_reader.parse(text)\n` → `["remote_document"]`. The `_the_log` body with `log.touch()` before the `return` → `[]`. `class Rig:\n    def log(self, tmp_path):` with the `_the_log` body → `[]`. `def log_lines(tmp_path):\n    return []\n` → `[]` (a name alone is not a copy for this guard).
3. `shared_bodies` reads each body from its module: `shared_bodies(TESTS)["log_lines"]` equals `body_of` of `log_support.log_lines`'s definition, read with `ast` from `tests/log_support.py`.
4. Every earlier test keeps its name and checks the same thing. The ids that `pytest --collect-only` lists for `tests/application/handlers/test_reject.py` are the same before and after the story, and all of them pass.
5. `make check` stays green.
6. docs: `docs/project-guide/README.md`, *Shared test helpers*: one sentence after the paragraph's second sentence. It says that the guards `tests/test_shared_*.py` fail on a copy of a shared helper, and that `test_shared_bodies.py` finds a copy of `log_lines`, `pushed`, `pushed_state`, `remote_document` and `push_state` by its body under any name. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none. Nothing an operator or a newcomer sees changes, and the decision is the feature's decision 5.

## Smoke test

```bash
uv run python - <<'PY'
import ast
from pathlib import Path
T = Path("tests")
def body(f):
    b = f.body[1:] if f.body and isinstance(f.body[0], ast.Expr) and isinstance(f.body[0].value, ast.Constant) else f.body
    return "\n".join(ast.unparse(s) for s in b)
shared = {"log_lines": "log_support.py", "pushed": "stage_run_support.py", "pushed_state": "stage_run_support.py", "remote_document": "branch_reading.py", "push_state": "branch_reading.py"}
bodies = {n.name: body(n) for name, mod in shared.items() for n in ast.parse((T / mod).read_text()).body if isinstance(n, ast.FunctionDef) and n.name == name}
hits = sorted(f"{p.relative_to(T)}::{n.name}" for p in T.rglob("*.py") for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef) and body(n) in bodies.values() and p.name not in set(shared.values()))
print(hits)
PY
```
Expect: one line, `[]` (before the story, `['application/handlers/test_reject.py::_branch_document']`)

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
TMPDIR="$d" uv run pytest --no-header --tb=short -p no:cacheprovider tests/test_shared_bodies.py tests/test_shared_definition.py tests/test_shared_branch_helpers.py tests/application/handlers/test_reject.py > "$d/out" 2>&1
echo "exit $?"
```
Expect: one line, `exit 0`

```bash
grep -c 'test_shared_bodies.py' docs/project-guide/README.md
```
Expect: one line, `1` (before the story, `0`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
