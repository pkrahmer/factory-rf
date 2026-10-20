---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 358
comments_read: [6299016224]
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
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-20T19:10:00.309747Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-20T19:10:18.678730Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-20T19:10:36.879912Z'
  stage: intake
  run: a376326046fc4faa8a4fbddc4170ad12
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T19:10:57.833074Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-20T19:14:32.120436Z'
  stage: tests
  run: 6f1fc7645ca64da5a7fc03281a5fd94c
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-20T19:14:53.176077Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-20T19:17:52.832511Z'
  stage: doing
  run: 268f99553c7d4967abc86d15d32e2589
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-20T19:18:14.033488Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-20T19:18:58.396494Z'
  stage: review
  run: d41857ebf8cb4fe99cc73d74389a131e
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
3. No file under `tests/` writes a shebang of the test interpreter without `-B`. The structural test's scan finds none in the built tests. Its matcher, as rows of one parametrized test: the text `f"#!{sys.executable}\n"` is found, and `f"#!{sys.executable} -B\n"` is not. The rows build these two texts from pieces, so that no line of `tests/test_test_children.py` holds the literal text `#!{sys.executable}\n`; the scan reads that module like any other and finds nothing, and the third smoke test's grep stays at `0`.
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
4. 2026-10-20 human: Answers (2026-10-20):
   1. (a). The matcher rows build the text from pieces, and criterion 3 says that no line of the module holds the literal text; the scan reads its own module like any other, and the smoke test's grep stays at `0`.
   2. Agreed: "same path" is `directory / "sudo"`, as the existing tests use it.
5. factory: started intake as self.
6. intake: accepted
   Carried in from the human's answer (journal entry 4, answer 1, option a): criterion 3 now says the matcher rows build the two texts from pieces, so no line of `tests/test_test_children.py` holds the literal `#!{sys.executable}\n`. The scan reads its own module like any other, and the third smoke test's grep stays at `0`. Answer 2 (the "same path" is `directory / "sudo"`) needs no edit. The Description's meaning did not change.
   - Interface: concrete. It names `write_script` and `python_argv` with their exact outputs, `_write_sudo`'s replacement line, the eight shebang writers by file and line, and the new test module. No `src/` module changes.
   - Criteria: each is testable by one test function. Criterion 1 is one parametrized test with three rows, the third being the side the helpers close. Criterion 2 checks the first line and mode of the stand-in `sudo`. Criterion 3 covers both sides of the matcher, plus the scan of the built tests. The rules have a failing side: the plain shebang is found, the `-B` one is not, and the plain child does write `__pycache__`. Criteria 4 and 5 are the closing two.
   - Smoke test: the three commands are runnable. None runs pytest, so no `-q` issue arises. Each `Expect:` (`True`, `False`, `0`) can be checked against the output.
   - Architecture: only test helpers change. The new module sits at the `tests/` root because it tests no package module. The layers are untouched.
   - Scope: it is within F0027. Decision 16 grants the leave for exactly these helpers and stand-ins, and the story is listed as S0004 in the feature. No "Out of scope" item is touched.
7. factory: started tests as self.
8. tester: Every change in this story is a test change, so I made all of it here. The coder never edits tests (R9), and nothing under `src/` changes. The tests are green, not red. There is nothing left for the coder to implement, so the coder only needs to run `make check`. The `docs:` criterion goes to the documenter.

   Criterion → test:
   - criterion 1: tests/test_test_children.py::test_a_child_started_by_the_helpers_writes_no_bytecode (rows `write-script`, `python-argv`, `plain`; `plain` is `[sys.executable, "-S", "-c", ...]` and does write `__pycache__`)
   - criterion 2: tests/test_test_children.py::test_the_stand_in_sudo_starts_the_interpreter_without_bytecode (first line `#!{sys.executable} -B`, mode 0755). The existing tests in tests/adapters/test_claude_runtime_os_user.py keep their names and checks.
   - criterion 3: matcher rows in tests/test_test_children.py::test_the_scan_finds_a_shebang_without_the_flag (rows `plain` found, `bytecode-off` not found; both texts are built from pieces). Scan of the built tests: tests/test_test_children.py::test_no_test_writes_a_shebang_of_the_interpreter_without_the_flag (reads every `tests/**/*.py`, its own module included). The pattern is `#!\{sys\.executable\}(?! -B)`.
   - criterion 4: `make check`, not a test function.
   - criterion 5: docs, for the documenter stage.

   Changes to helpers under the leave in decision 16 of `feature.md`, as the Interface lists them (other stories' test files; I did not read `feature.md`):
   - tests/confine_support.py `write_script`: the shebang is now `#!{sys.executable} -B`.
   - tests/process_support.py `python_argv`: now returns `[sys.executable, "-B", "-c", code, *args]`.
   - tests/adapters/test_claude_runtime_os_user.py `_write_sudo`: now `return write_script(directory / "sudo", SUDO_SCRIPT)`, with `write_script` imported from `confine_support`. I removed `import sys`.
   - Added ` -B` to the shebang in each of these and changed nothing else in them: tests/adapters/claude_stand_in.py, tests/adapters/opencode_stand_in.py (two places), tests/adapters/test_claude_runtime_file_modes.py, tests/adapters/test_claude_runtime_provider_limit.py, tests/git_support.py, tests/adapters/test_git_cli_branches.py, tests/adapters/test_git_cli_writing.py.

   File created: tests/test_test_children.py.

   Modules the test runner could not import: none. `make test` was green with 99.17 % coverage, so the new tests pass already, because the helper changes they check are in place. `make lint` is green. The third smoke test's grep `grep -rnF '#!{sys.executable}\n' tests | wc -l` gives 0. The subprocess call in the new test carries `# noqa: S603` with a reason, as other test modules do. Nothing is open.

   `lint`: lint: green (0.8 s)
   `test`: test: green (68.3 s)
9. factory: started doing as self.
10. coder: I built nothing new and wrote no code. This story's changes are all test changes. The tester made them under decision 16's leave: the helpers `tests/confine_support.py` and `tests/process_support.py`, `_write_sudo` in `tests/adapters/test_claude_runtime_os_user.py`, the eight shebang writers, and the new `tests/test_test_children.py`. Nothing under `src/` changes.

    I ran `make check` on the committed branch and it passed, ending with `check: green` (test: green (69.0 s), coverage 99.17 %). `git diff --stat main` shows only the 11 files under `tests/`. The third smoke test's grep (`grep -rnF '#!{sys.executable}\n' tests | wc -l`) gives `0`.

    - **Main choice:** leave the working tree as it is. I rejected touching any test or helper, since the coder never edits tests (R9), and there was no code to implement.
    - **Refactor:** there was no diff of mine to refactor.
    - **Description:** the journal did not change its meaning. Answer 1 from the human (option a) is already in criterion 3.
    - **Noticed but did not touch:** nothing. The `docs:` criterion (`docs/decisions.md`) is the documenter's.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
11. factory: started review as self.
12. reviewer: no findings

    I read the work item and `git diff main...HEAD -- . ':!factory'`, which changes 11 files, all under `tests/`. Nothing under `src/` changes. I also read decision 16 in F0027's `feature.md` to check the leave.
    - Criterion 1: `tests/test_test_children.py::test_a_child_started_by_the_helpers_writes_no_bytecode` is one parametrized test with three rows. Each row passes `env={}`, and the umask is the tests' `022` from `tests/conftest.py`. The rows are `write-script` (no `__pycache__`), `python-argv` (no `__pycache__`) and `plain` with `-S` (writes `__pycache__`), so both sides of the rule are covered.
    - Criterion 2: `test_the_stand_in_sudo_starts_the_interpreter_without_bytecode` checks the stand-in's first line `#!{sys.executable} -B` and mode `0755`. `_write_sudo` is now `return write_script(directory / "sudo", SUDO_SCRIPT)`, which returns the same path, `directory / "sudo"`. `import sys` is gone. Six modules on `main` already import `_write_sudo`, so importing it into the new module follows an existing pattern.
    - Criterion 3: the matcher test is one parametrized test with two rows, `plain` (found) and `bytecode-off` (not found). Both texts are built from pieces. The scan test reads every `tests/**/*.py`, its own module included. The pattern escapes its braces and uses a lookahead for ` -B`, so this module's own text does not match it. I grepped `tests` for `#!`: every other shebang is `#!/bin/sh`, so no interpreter shebang is missing `-B`.
    - Criterion 4: the factory's `make check` after the coder was green (journal entry 10). The new `# noqa: S603` gives its reason beside it, and seven test modules on `main` already carry the same marker.
    - Architecture and security: nothing under `src/` changes, and no `nosec`, `nosemgrep` or baseline entry was added.
    - Work item: the Description matches what was built. The docs criterion still names the sentence the documenter must add to `docs/decisions.md`.

    Earlier tests (every changed file is status `M`, and each change is exactly the one decision 16's S0004 line names):
    - `tests/confine_support.py`: decision 16, S0004 (`write_script` shebang ` -B`).
    - `tests/process_support.py`: decision 16, S0004 (`python_argv` adds `"-B"`).
    - `tests/adapters/test_claude_runtime_os_user.py`: decision 16, S0004 (`_write_sudo` through `write_script`, `import sys` dropped).
    - `tests/adapters/claude_stand_in.py`: decision 16, S0004 (shebang ` -B`).
    - `tests/adapters/opencode_stand_in.py`: decision 16, S0004 (two shebangs ` -B`).
    - `tests/adapters/test_claude_runtime_file_modes.py`: decision 16, S0004 (shebang ` -B`).
    - `tests/adapters/test_claude_runtime_provider_limit.py`: decision 16, S0004 (shebang ` -B`).
    - `tests/git_support.py`: decision 16, S0004 (`write_executable` shebang ` -B`).
    - `tests/adapters/test_git_cli_branches.py`: decision 16, S0004 (hook shebang ` -B`).
    - `tests/adapters/test_git_cli_writing.py`: decision 16, S0004 (hook shebang ` -B`).
