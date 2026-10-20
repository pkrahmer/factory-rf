---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 358
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T19:08:14.279485Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T19:08:14.285976Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-20T19:08:40.932315Z'
  stage: intake
  run: 388a832dedee41a0803c6214ee34f9ae
  blocked: question
---

# The tests start their own Python children without bytecode

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

Since F0027-S0003 the factory removes every git-ignored path of the checkout after each agent run and at every restore, as its own user and through the group. So a folder an agent's run leaves without group write stops the factory. F0027's acceptance (F0027-A0001) crashed twice that way. The restore's `git clean -X` could not remove `.venv/lib/python3.12/site-packages/__pycache__/` (`drwxr-sr-x agent`) and its `_virtualenv.cpython-312.pyc`. A Python child of the tests wrote them during an agent's `make check`, under the tests' umask `022` (`tests/conftest.py`), with an environment that no longer held the container's `PYTHONDONTWRITEBYTECODE=1`. `main` now exports `UV_COMPILE_BYTECODE=1` in the `Makefile` (fd0fcd0b), so uv writes `.venv`'s bytecode at its sync, group-writable. But a test child still writes bytecode for any module that has none yet, under `022`. The human named the three helper lines that start the test interpreter without `-B` (journal entry 6 of F0027-A0001): `tests/confine_support.py:114` (`write_script`), `tests/process_support.py:29` (`python_argv`) and `tests/adapters/test_claude_runtime_os_user.py:81` (the stand-in `sudo` of `_write_sudo`, a copy of `write_script`'s three lines). This story makes the two shared helpers start their child with `-B`, and makes `_write_sudo` write its stand-in through `write_script`. Every test that uses them keeps its name and checks the same thing. Eight other places write a script with the shebang `#!{sys.executable}`: the stand-ins of `claude` and `opencode`, an opencode wrapper, a file-modes stand-in, a slow provider-limit stand-in, a stand-in `git` and two git hooks. Their environment keeps `PYTHONDONTWRITEBYTECODE` today, but a later test that empties it would write bytecode again. So they get ` -B` too, and a structural test keeps every such shebang at `-B`. About twenty argv lists in `tests/` start `sys.executable` without `-B`, in an environment that keeps the variable. They stay as they are and are not checked: many sit inside code strings, so a text rule on them would be fuzzy, and `python_argv` is the helper for them. Nothing under `src/` changes.

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
- `tests/adapters/test_claude_runtime_os_user.py`, `_write_sudo`: its three lines that write and `chmod` the stand-in `sudo` become `return write_script(directory / "sudo", SUDO_SCRIPT)`, with `write_script` imported from `confine_support`. It returns the same path as before. The module's `import sys` goes, because nothing outside the text of `SUDO_SCRIPT` uses it then. The lines are a copy of the shared helper, but the change also gives the six modules that import `_write_sudo` a stand-in started with `-B`, so it is part of the leave below.
- Leave: `write_script`, `python_argv` and `_write_sudo` are other stories' helpers, and changing what they produce is beyond the standing leave. Before this story starts, the human grants it in F0027's `feature.md`, decision 16, with a line for S0004. The leave is exactly the three changes above; every test that uses them keeps its name and checks the same thing.
- The eight other shebang writers gain ` -B` after `{sys.executable}`, and nothing else in their modules changes: `tests/adapters/claude_stand_in.py:83`, `tests/adapters/opencode_stand_in.py:83` and `:270`, `tests/adapters/test_claude_runtime_file_modes.py:52`, `tests/adapters/test_claude_runtime_provider_limit.py:164`, `tests/git_support.py:165` (`write_executable`), `tests/adapters/test_git_cli_branches.py:104` and `tests/adapters/test_git_cli_writing.py:290` (the two hooks). This is part of the same leave in decision 16.
- New test module: `tests/test_test_children.py` (at the `tests/` root, since it tests no package module). Its structural test reads every `tests/**/*.py` and finds no `#!{sys.executable}` that ` -B` does not follow. Its pattern is a regular expression with escaped braces, so the module's own text does not match it. It reads no file under `src/`, so `[tool.mutmut]` stays as it is.

## Acceptance criteria

1. Each row writes a module `standin.py` (`x = 1`) in `tmp_path`, then starts a child of the test interpreter in `tmp_path` with the environment `{}` (no `PYTHONDONTWRITEBYTECODE`), under the tests' umask `022`. The child runs `import standin`. Rows: a script written by `write_script(tmp_path / "child", "import standin\n")` and run by its path, so `tmp_path/__pycache__` does not exist afterwards; `python_argv("import standin")`, the same; and the plain `[sys.executable, "-S", "-c", "import standin"]`, the side the helpers close, after which `tmp_path/__pycache__` exists. `-S` keeps that row's child from loading `site`: without it, the child would write `_virtualenv`'s bytecode into `.venv`'s `site-packages` under `022` whenever uv has not compiled it (a `.venv` that a plain `uv run` built), which is the folder this story closes. One parametrized test.
2. The stand-in `sudo` that `_write_sudo` writes has the first line `#!{sys.executable} -B` and mode `0755`. Every test in `tests/adapters/test_claude_runtime_os_user.py` keeps its name and checks the same thing.
3. No file under `tests/` writes a shebang of the test interpreter without `-B`. The structural test's scan finds none in the built tests. Its matcher, as rows of one parametrized test: the text `f"#!{sys.executable}\n"` is found, and `f"#!{sys.executable} -B\n"` is not.
4. `make check` stays green.
5. docs: `docs/decisions.md`, the entry *The factory removes the git-ignored paths after every agent run and at the restore*: one sentence says that the tests' shared helpers and every script the tests write for their own interpreter start it with `-B`, and that a structural test keeps the shebangs so. The reason: the tests run under umask `022`, and a bytecode folder written there by the agent's `make check` is one the factory's removal cannot remove. That stopped F0027's acceptance twice on 2026-10-20. `README.md`, `docs/operator-guide.md` and `docs/project-guide/`: none, since no behaviour of the factory changes.

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

```bash
grep -rnF '#!{sys.executable}\n' tests | wc -l
```
Expect: `0`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: 1. Criterion 3 and the smoke test contradict themselves. Criterion 3's matcher rows need the text `f"#!{sys.executable}\n"` as test data, so that the matcher can be shown to find it. If that text sits in `tests/test_test_children.py`, the structural scan reads `tests/**/*.py` and finds the text in that module. The third smoke test (`grep -rnF '#!{sys.executable}\n' tests | wc -l`, expecting `0`) counts it too. Your description says the module's own text does not match the pattern, but that is only true of the pattern's own line, not of the rows. Options: (a) the rows build the text from pieces, for example `"#!" + "{sys." + "executable}\n"` or `"#!{}\n".format("sys.executable")`, so that no source line holds the literal text. The scan and the grep then stay at zero. (b) The scan skips its own module, and the smoke test grep excludes it with `--exclude=test_test_children.py`. I would choose (a), with the criterion saying that no line of the module holds the literal text. Please say which one you want, and I will add it to criterion 3 and the smoke test.

   2. Minor, answer only if you disagree. Criterion 2 checks the stand-in `sudo`'s first line and mode. The Interface says `_write_sudo` returns the same path as before. The criterion does not test the path. I will read "same path" as `directory / "sudo"`, covered by the stand-in's location in the existing tests.

   Everything else holds. Format check passed. The three changed helpers and the eight shebang writers are at the named lines (I checked with grep). `import sys` is used outside `SUDO_SCRIPT` only inside the script text, so dropping it is right. The smoke test commands are runnable and none runs pytest, so no `-q` issue arises. The scope is within F0027's scope, and decision 16 grants the leave for S0004. No `src/` module changes, so the layers are untouched.
