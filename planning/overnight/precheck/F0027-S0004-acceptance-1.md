# Pre-check F0027-S0004 (the story F0027-A0001 proposed), round 1: the tests start their own Python children without bytecode

This file is not `F0027-S0004-1.md`: that name holds the round-1 pre-check of the withdrawn S0004 (`kept_ignored`), so this one takes another name.

I checked the story against `factory/story-form.md`, `CLAUDE.md` (*Tests*, the standing leave), F0027's `feature.md` (decisions 16 and 19, *Stories*, *The human's answers*), the acceptance record `done/F0027-A0001-acceptance.md` (point 4 and journal entry 6) and the bisection note `planning/overnight/group-write-2026-10-20.md`. The code is today's `main` at `c84d2321` (pulled; nothing newer). The `Makefile` exports `UV_COMPILE_BYTECODE := 1` since fd0fcd0b.

## What I ran

Throwaway containers of `factory-self-factory` (`--network none --cpus 2`), one at a time, on an LF copy of `HEAD` (`git -c core.autocrlf=false archive`, without `image/secrets`) under `C:/Users/pasca/AppData/Local/Temp/pc27b`. They ran as the image's user `factory` under umask `022`, with the image's `/opt/factory/.venv/bin/python` and the copy's `src` on `PYTHONPATH`. The running instance and its `.venv` were not touched. The copy is deleted.

**Form check.** `python -m factory.entry.check_story` on the story: `ok`, exit 0.

**Smoke blocks.**

| Block | Today's code | With the three lines changed as the story says |
|---|---|---|
| 1, `python_argv("pass")[:3] == [sys.executable, "-B", "-c"]` | `False` | `True` (the Expect) |
| 2, an env-less child of `write_script` imports `standin`, then `__pycache__` exists? | `True` | `False` (the Expect); the child's first line was `#!/opt/factory/.venv/bin/python -B` |

So both blocks tell the built code from today's.

**The plain row of criterion 1 writes into `.venv` itself.** I made a writable venv with uv's `_virtualenv.pth` and `_virtualenv.py` copied in, and no bytecode for them. Then, under umask `022`, a child with `env={}` ran `import standin` in a temporary folder:

| Child | `tmp/__pycache__` | `site-packages/__pycache__` |
|---|---|---|
| `[python, "-c", "import standin"]` (the story's plain row) | yes | **`drwxr-xr-x`**, written by the child's `site` |
| `[python, "-S", "-c", "import standin"]` | yes | none |
| `[python, "-B", "-c", "import standin"]` | no | none |

With `make test`, `UV_COMPILE_BYTECODE=1` has already compiled `_virtualenv`, so the plain row writes nothing there. But a `.venv` that a plain `uv run` built, without `make`'s export (an agent's `uv run pytest <module>`, which `CLAUDE.md` allows, or the smoke tester's first `uv run`), has no such bytecode. Then the story's own plain row writes exactly the folder that stopped the acceptance. `-S` keeps the row's meaning (no `-B`, no variable, so `standin`'s bytecode is written) and loads no `site`. This is required edit 2.

## Names, lines and the tests it changes

- `tests/confine_support.py:114` is `write_script`'s `path.write_text(f"#!{sys.executable}\n{script}", ...)`. Exact.
- `tests/process_support.py:29` is `python_argv`'s `return [sys.executable, "-c", code, *args]`. Exact.
- `tests/adapters/test_claude_runtime_os_user.py:81` is in `_write_sudo` (line 69): `path = directory / "sudo"`, the `write_text` at 81 and the `chmod` at 82. Exact. It is a copy of `write_script` except for `write_script`'s `mkdir`, which `_write_sudo` already does itself at line 72. After the change the module's `import sys` (line 4) is unused: the other `sys.` lines (42 to 54) lie inside the text `SUDO_SCRIPT`. So ruff's `F401` asks for its removal, and the leave must name it.
- Six modules import `_write_sudo` (`test_claude_runtime_api_login`, `_login`, `_sudo_time_limit`, `test_opencode_confinement`, `test_opencode_runtime_launch`, `test_opencode_sudo_time_limit`). About twenty modules use `write_script` or `python_argv`. No test reads the first line of a written script or compares a `python_argv` list with a literal, so none of them changes what it checks (grep over `tests/` for `#!{sys`, `splitlines()[0]` and `"-c"`).
- `tests/test_test_children.py` does not exist yet. The `tests/` root is right for it (`CLAUDE.md`, *Tests*: a module outside the layers).
- The story calls the `_write_sudo` change the standing leave. It is a copy of the shared helper, so the move fits. But it also changes what six other modules' stand-in does (`-B`), and it drops an import. I would put it in decision 16 with the other two (required edit 1 and feature.md edit C), so that no reviewer has to weigh it.

## Coverage of the bisection's writers

The bisection found 59 tests in 13 modules that write the folder. Every one goes through the three lines:

- Cause 1, the stand-in `sudo` with `env={}`: `_write_sudo` (line 81), and `write_script` for `test_claude_runtime_confinement.py:185`, `tests/leftovers_runtime_support.py:81` and `:89`, and the probe and confine stand-ins. Covered.
- Cause 2, the login shell's command with a narrow environment: `tests/adapters/test_agent_launch_login.py:58-67` writes it with `write_script`. Covered.
- Cause 3, `python -c` with a replaced environment: `python_argv` in `test_process.py:66` and `test_process_streaming.py:262-267`. Covered.

The bisection verified that the three changes leave the full `make test`, as `agent`, without a folder `git clean -X` cannot remove. The grandchildren that `test_process.py:92`, `test_process_session.py:27` and `test_process_streaming.py:24` start with `[sys.executable, '-c', ...]` inherit an environment that keeps `PYTHONDONTWRITEBYTECODE` (their parent runs with `env=None`), so they write nothing.

The bisection names eight more writers of the shebang `#!{sys.executable}` that do not write today, because their environment keeps the variable: `tests/adapters/claude_stand_in.py:83`, `tests/adapters/opencode_stand_in.py:83` and `:270`, `tests/adapters/test_claude_runtime_file_modes.py:52`, `tests/adapters/test_claude_runtime_provider_limit.py:164`, `tests/git_support.py:165` (`write_executable`) and the two git hooks `tests/adapters/test_git_cli_branches.py:104` and `tests/adapters/test_git_cli_writing.py:290`. Today `grep -rnF '#!{sys.executable}\n' tests` finds ten lines: these eight and the two of this story. The bisection's production note (`src/factory/entry/wiring.py:296`, `-I` without `-B`) is outside this story and is not needed for the stop.

## A structural guard: recommended, the cheap one, shebangs only

The bisection sketches two guards.

1. **A text rule** over `tests/**/*.py`. For the shebang form it is exact and simple: no `#!{sys.executable}` that ` -B` does not follow. For the argv form (`[sys.executable, ...]` without `"-B"`) it is fuzzy: many such lists sit inside code strings (`'-c'` in single quotes, as in the grandchild lines above), and about twenty of them are harmless. A rule there would need exceptions.
2. **A guard on the effect**, a `pytest_sessionfinish` hook that fails the run when a `__pycache__` appeared under the checkout or `purelib`. It catches every form, but it must run only in the xdist controller, only when the variable was set at the start, and it walks `.venv` twice. Since `UV_COMPILE_BYTECODE=1` compiles the site-packages, it would also need to watch new files, not only new folders. That is a lot of cleverness for a test helper.

I recommend option 1, for shebangs only, as part of this story (optional edits 3 to 6, and feature.md edit C'). It costs eight one-word edits (` -B`) in other stories' modules and one scan test. It catches the form that leaked (stand-ins started behind an emptied environment), and `python_argv` already carries the argv form. Its pattern is a regular expression with escaped braces, so its own text does not match. It reads only `tests/`, so `[tool.mutmut]` stays as it is and *The human's changes* stays true ("no story adds a structural test that reads the source"). The argv form stays unchecked; the story's Description says so. If the human prefers the smallest story, the story as drafted, with the required edits, is complete for the stop.

## Verdict

**Accepted with two required edits** (the leave's wording and the plain row's `-S`). The four optional edits 3 to 6 add the shebang guard (recommended). Decision 16 needs a line for S0004 before the story starts (feature.md edits B and C, required), and *Stories* needs the three new stories (edit A, required).

The leave in plain words: the tester may make `write_script` and `python_argv` start their child with `-B`, may make `_write_sudo` write its stand-in through `write_script` (and drop the unused `import sys`), and nothing else in those three modules. With the guard: also add ` -B` to the eight other shebang lines, and nothing else in their modules.

### The story file

Edit 1 (required, Interface). Replace

```markdown
- `tests/adapters/test_claude_runtime_os_user.py`, `_write_sudo`: its three lines that write and `chmod` the stand-in `sudo` become one call `write_script(directory / "sudo", SUDO_SCRIPT)`. It returns that path, as before. This part falls under `CLAUDE.md`'s standing leave: the lines are a copy of the shared helper.
- Leave: `write_script` and `python_argv` are other stories' shared helpers, and changing what they produce is beyond the standing leave. Before this story starts, the human grants it in F0027's `feature.md`, decision 16, with a line for S0004. The leave is exactly the two changes above; every test that uses them keeps its name and checks the same thing.
```

with

```markdown
- `tests/adapters/test_claude_runtime_os_user.py`, `_write_sudo`: its three lines that write and `chmod` the stand-in `sudo` become `return write_script(directory / "sudo", SUDO_SCRIPT)`, with `write_script` imported from `confine_support`. It returns the same path as before. The module's `import sys` goes, because nothing outside the text of `SUDO_SCRIPT` uses it then. The lines are a copy of the shared helper, but the change also gives the six modules that import `_write_sudo` a stand-in started with `-B`, so it is part of the leave below.
- Leave: `write_script`, `python_argv` and `_write_sudo` are other stories' helpers, and changing what they produce is beyond the standing leave. Before this story starts, the human grants it in F0027's `feature.md`, decision 16, with a line for S0004. The leave is exactly the three changes above; every test that uses them keeps its name and checks the same thing.
```

Edit 2 (required, Acceptance criteria, criterion 1). Replace

```markdown
and the plain `[sys.executable, "-c", "import standin"]`, the side the helpers close, after which `tmp_path/__pycache__` exists. One parametrized test.
```

with

```markdown
and the plain `[sys.executable, "-S", "-c", "import standin"]`, the side the helpers close, after which `tmp_path/__pycache__` exists. `-S` keeps that row's child from loading `site`: without it, the child would write `_virtualenv`'s bytecode into `.venv`'s `site-packages` under `022` whenever uv has not compiled it (a `.venv` that a plain `uv run` built), which is the folder this story closes. One parametrized test.
```

Edits 3 to 6 (optional together: the shebang guard, recommended).

Edit 3 (optional, Description). Replace

```markdown
About twenty-five other places in `tests/` start `sys.executable` without `-B`, in an environment that keeps `PYTHONDONTWRITEBYTECODE`. They stay as they are. Whether every child of the test interpreter must carry `-B`, as a rule with a structural test, is the human's question; this story does not decide it.
```

with

```markdown
Eight other places write a script with the shebang `#!{sys.executable}`: the stand-ins of `claude` and `opencode`, an opencode wrapper, a file-modes stand-in, a slow provider-limit stand-in, a stand-in `git` and two git hooks. Their environment keeps `PYTHONDONTWRITEBYTECODE` today, but a later test that empties it would write bytecode again. So they get ` -B` too, and a structural test keeps every such shebang at `-B`. About twenty argv lists in `tests/` start `sys.executable` without `-B`, in an environment that keeps the variable. They stay as they are and are not checked: many sit inside code strings, so a text rule on them would be fuzzy, and `python_argv` is the helper for them.
```

Edit 4 (optional, Interface). Replace

```markdown
- New test module: `tests/test_test_children.py` (at the `tests/` root, since it tests no package module).
```

with

```markdown
- The eight other shebang writers gain ` -B` after `{sys.executable}`, and nothing else in their modules changes: `tests/adapters/claude_stand_in.py:83`, `tests/adapters/opencode_stand_in.py:83` and `:270`, `tests/adapters/test_claude_runtime_file_modes.py:52`, `tests/adapters/test_claude_runtime_provider_limit.py:164`, `tests/git_support.py:165` (`write_executable`), `tests/adapters/test_git_cli_branches.py:104` and `tests/adapters/test_git_cli_writing.py:290` (the two hooks). This is part of the same leave in decision 16.
- New test module: `tests/test_test_children.py` (at the `tests/` root, since it tests no package module). Its structural test reads every `tests/**/*.py` and finds no `#!{sys.executable}` that ` -B` does not follow. Its pattern is a regular expression with escaped braces, so the module's own text does not match it. It reads no file under `src/`, so `[tool.mutmut]` stays as it is.
```

Edit 5 (optional, Acceptance criteria, criteria 3 and 4). Replace

```markdown
3. `make check` stays green.
4. docs: `docs/decisions.md`, the entry *The factory removes the git-ignored paths after every agent run and at the restore*: one sentence says that the tests' shared helpers start every child of the test interpreter with `-B`.
```

with

```markdown
3. No file under `tests/` writes a shebang of the test interpreter without `-B`. The structural test's scan finds none in the built tests. Its matcher, as rows of one parametrized test: the text `f"#!{sys.executable}\n"` is found, and `f"#!{sys.executable} -B\n"` is not.
4. `make check` stays green.
5. docs: `docs/decisions.md`, the entry *The factory removes the git-ignored paths after every agent run and at the restore*: one sentence says that the tests' shared helpers and every script the tests write for their own interpreter start it with `-B`, and that a structural test keeps the shebangs so.
```

Edit 6 (optional, Smoke test, after the second block). Add

````markdown
```bash
grep -rnF '#!{sys.executable}\n' tests | wc -l
```
Expect: `0`
````

(Today it prints `10`.)

### feature.md

Edit A (required, *Stories*). Replace

```markdown
- S0001: A program ends every other process of the user it runs as
- S0002: The agent runtimes end the agent's leftover processes after every call
- S0003: The factory removes the git-ignored files after every agent run and at the restore
```

with

```markdown
- S0001: A program ends every other process of the user it runs as
- S0002: The agent runtimes end the agent's leftover processes after every call
- S0003: The factory removes the git-ignored files after every agent run and at the restore
- S0004: The tests start their own Python children without bytecode (proposed by F0027-A0001; first, since it removes the cause of the acceptance's two crashes)
- S0005: The documents say what an ignored path the factory cannot remove does (proposed by F0027-A0001)
- S0006: The feature's tests share their constants and find the marker's line (proposed by F0027-A0001)
```

Edit B (required, decision 16: the ID S0004 now names two stories). Replace

```markdown
    - S0004: withdrawn (decision 3).
```

with

```markdown
    - S0004 of round 1 (`kept_ignored`): withdrawn (decision 3). The S0004 that F0027-A0001 proposed is another story; its leave is below.
```

Edit C (required, decision 16: the S0004 leave; the two S0001 bullets also get four spaces, so that they stay inside item 16). Replace

```markdown
   - S0001, `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: its expected set gains `"factory.entry.leftovers"`; its name and everything else stay (the human, 2026-10-20, answering the coder's question 7).
   - S0001, `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`: its expected markers gain `"entry/leftovers.py": {<main's def line>: {"noqa: PLR0913"}}`, the one marker allowed for `main`'s six parameters; its name and everything else stay (the human, 2026-10-20).
```

with

```markdown
    - S0001, `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: its expected set gains `"factory.entry.leftovers"`; its name and everything else stay (the human, 2026-10-20, answering the coder's question 7).
    - S0001, `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`: its expected markers gain `"entry/leftovers.py": {<main's def line>: {"noqa: PLR0913"}}`, the one marker allowed for `main`'s six parameters; its name and everything else stay (the human, 2026-10-20).
    - S0004 (F0027-A0001's story, the tests start their own Python children without bytecode): `tests/confine_support.py::write_script` writes the first line `#!{sys.executable} -B` in place of `#!{sys.executable}`, and `tests/process_support.py::python_argv` returns `[sys.executable, "-B", "-c", code, *args]`. In `tests/adapters/test_claude_runtime_os_user.py`, the three lines of `_write_sudo` that write and `chmod` the stand-in `sudo` become `return write_script(directory / "sudo", SUDO_SCRIPT)`; the module imports `write_script` from `confine_support` and drops `import sys`, which nothing else in it uses then. Nothing else in the three modules changes, and every test that uses these helpers keeps its name, its rows and what it checks. The reason: the tests run under umask `022`, and a child whose environment a test replaces loses `PYTHONDONTWRITEBYTECODE`, so these three lines wrote the bytecode folder that stopped the acceptance twice (F0027-A0001, journal entry 6).
```

Edit C' (optional, with story edits 3 to 6: the guard). In the S0004 bullet of edit C, replace

```markdown
Nothing else in the three modules changes, and every test that uses these helpers keeps its name, its rows and what it checks.
```

with

```markdown
The eight other writers of the shebang `#!{sys.executable}` gain ` -B` after it: `tests/adapters/claude_stand_in.py:83`, `tests/adapters/opencode_stand_in.py:83` and `:270`, `tests/adapters/test_claude_runtime_file_modes.py:52`, `tests/adapters/test_claude_runtime_provider_limit.py:164`, `tests/git_support.py:165`, `tests/adapters/test_git_cli_branches.py:104` and `tests/adapters/test_git_cli_writing.py:290`. Nothing else in these modules changes, and every test that uses these helpers and stand-ins keeps its name, its rows and what it checks.
```

Edit D (optional, decision 19). Replace

```markdown
So S0001's child runs with `-I -B`, and any later test that starts an isolated Python child does the same. (S0001, S0003)
```

with

```markdown
So S0001's child runs with `-I -B`, and any later test that starts an isolated Python child does the same. A child whose environment a test replaces (`env={}` or a dict of its own) loses `PYTHONDONTWRITEBYTECODE` too: three helper lines started such children without `-B`, and their bytecode folder in `.venv` stopped F0027's acceptance twice. S0004 adds `-B` there. (S0001, S0003, S0004)
```
