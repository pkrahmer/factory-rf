# The tests start their own Python children without bytecode

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

Since F0027-S0003 the factory removes every git-ignored path of the checkout after each agent run and at every restore, as its own user and through the group. So a folder an agent's run leaves without group write stops the factory. F0027's acceptance (F0027-A0001) crashed twice that way. The restore's `git clean -X` could not remove `.venv/lib/python3.12/site-packages/__pycache__/` (`drwxr-sr-x agent`) and its `_virtualenv.cpython-312.pyc`. A Python child of the tests wrote them during an agent's `make check`, under the tests' umask `022` (`tests/conftest.py`), with an environment that no longer held the container's `PYTHONDONTWRITEBYTECODE=1`. `main` now exports `UV_COMPILE_BYTECODE=1` in the `Makefile` (fd0fcd0b), so uv writes `.venv`'s bytecode at its sync, group-writable. But a test child still writes bytecode for any module that has none yet, under `022`. The human named the three helper lines that start the test interpreter without `-B` (journal entry 6 of F0027-A0001): `tests/confine_support.py:114` (`write_script`), `tests/process_support.py:29` (`python_argv`) and `tests/adapters/test_claude_runtime_os_user.py:81` (the stand-in `sudo` of `_write_sudo`, a copy of `write_script`'s three lines). This story makes the two shared helpers start their child with `-B`, and makes `_write_sudo` write its stand-in through `write_script`. Every test that uses them keeps its name and checks the same thing. About twenty-five other places in `tests/` start `sys.executable` without `-B`, in an environment that keeps `PYTHONDONTWRITEBYTECODE`. They stay as they are. Whether every child of the test interpreter must carry `-B`, as a rule with a structural test, is the human's question; this story does not decide it. Nothing under `src/` changes.

## Interface

No module under `src/factory/` changes. Test helpers (not tests of their own), changed:

```python
# tests/confine_support.py
def write_script(path: Path, script: str) -> Path: ...   # shebang `#!{sys.executable} -B`

# tests/process_support.py
def python_argv(code: str, *args: str) -> list[str]: ...  # [sys.executable, "-B", "-c", code, *args]
```

- `write_script` writes `#!{sys.executable} -B\n{script}` and sets mode `0755`, as before apart from ` -B`.
- `python_argv` returns `[sys.executable, "-B", "-c", code, *args]`.
- `tests/adapters/test_claude_runtime_os_user.py`, `_write_sudo`: its three lines that write and `chmod` the stand-in `sudo` become one call `write_script(directory / "sudo", SUDO_SCRIPT)`. It returns that path, as before. This part falls under `CLAUDE.md`'s standing leave: the lines are a copy of the shared helper.
- Leave: `write_script` and `python_argv` are other stories' shared helpers, and changing what they produce is beyond the standing leave. Before this story starts, the human grants it in F0027's `feature.md`, decision 16, with a line for S0004. The leave is exactly the two changes above; every test that uses them keeps its name and checks the same thing.
- New test module: `tests/test_test_children.py` (at the `tests/` root, since it tests no package module).

## Acceptance criteria

1. Each row writes a module `standin.py` (`x = 1`) in `tmp_path`, then starts a child of the test interpreter in `tmp_path` with the environment `{}` (no `PYTHONDONTWRITEBYTECODE`), under the tests' umask `022`. The child runs `import standin`. Rows: a script written by `write_script(tmp_path / "child", "import standin\n")` and run by its path, so `tmp_path/__pycache__` does not exist afterwards; `python_argv("import standin")`, the same; and the plain `[sys.executable, "-c", "import standin"]`, the side the helpers close, after which `tmp_path/__pycache__` exists. One parametrized test.
2. The stand-in `sudo` that `_write_sudo` writes has the first line `#!{sys.executable} -B` and mode `0755`. Every test in `tests/adapters/test_claude_runtime_os_user.py` keeps its name and checks the same thing.
3. `make check` stays green.
4. docs: `docs/decisions.md`, the entry *The factory removes the git-ignored paths after every agent run and at the restore*: one sentence says that the tests' shared helpers start every child of the test interpreter with `-B`. The reason: the tests run under umask `022`, and a bytecode folder written there by the agent's `make check` is one the factory's removal cannot remove. That stopped F0027's acceptance twice on 2026-10-20. `README.md`, `docs/operator-guide.md` and `docs/project-guide/`: none, since no behaviour of the factory changes.

## Smoke test

```bash
uv run -q python -B - <<'EOF'
import sys
sys.path.insert(0, "tests")
from process_support import python_argv
print(python_argv("pass")[:3] == [sys.executable, "-B", "-c"])
EOF
```
Expect: `True`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python -B - "$d" <<'EOF'
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, "tests")
from confine_support import write_script
d = Path(sys.argv[1])
(d / "standin.py").write_text("x = 1\n", encoding="utf-8")
script = write_script(d / "child", "import standin\n")
subprocess.run([str(script)], cwd=d, env={}, check=True)
print((d / "__pycache__").exists())
EOF
```
Expect: `False`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
