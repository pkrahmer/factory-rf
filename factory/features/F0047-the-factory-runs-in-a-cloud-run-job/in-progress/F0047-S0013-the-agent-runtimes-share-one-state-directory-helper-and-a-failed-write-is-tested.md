---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 494
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T13:56:45.159335Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T13:56:45.165562Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-01T13:57:04.852436Z'
  stage: intake
  run: 2219ab4fc2e24c62923c5962f3f5328e
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-01T13:57:24.850003Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-01T14:04:03.975813Z'
  stage: tests
  run: 1952c2b98fa74ca782b8a7de160bba52
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-01T14:04:26.725541Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-01T14:10:42.446672Z'
  stage: doing
  run: 0b3acf7c3be04c1d948578f6fe8def13
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-01T14:11:03.025772Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-01T14:11:51.113182Z'
  stage: review
  run: 089d8b2ca26544fa9c26606ce145359e
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-01T14:12:11.680624Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-01T14:12:27.132809Z'
  stage: doing
  run: 226c6258f5714ff289a29a86547f8389
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-01T14:12:47.362649Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-01T14:18:45.072112Z'
  stage: tests
  run: 8083ea73f9c34ea0a92a6fd10be31697
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-01T14:19:05.522710Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-01T14:25:06.411317Z'
  stage: doing
  run: bee0ec18ac4647ab8362dbcdeca130ed
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-01T14:25:26.781179Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-11-01T14:25:53.516705Z'
  stage: review
  run: ed80a82c494847fb9e1c88d3dd085298
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-01T14:26:13.807216Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-11-01T14:26:33.967292Z'
  stage: docs
  run: 6afdd49e4a13483a8c8f5175997b3a93
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-01T14:26:54.964714Z'
  stage: smoke-test
- number: 21
  speaker: smoke-tester
  kind: result
  at: '2026-11-01T14:27:21.783760Z'
  stage: smoke-test
  run: 8aece8f72471470c89ee201698d9e365
---

# The agent runtimes share one state-directory helper, and a failed write is tested
<!-- proposed by feature acceptance of 2026-11-01; refine before starting -->

## Description

S0010 gave `OpencodeRuntime` a `_make_state_directory` that copies `ClaudeCodeRuntime._make_state_directory`: `mkdir(parents=True, exist_ok=True)`, and an `OSError` becomes `state_directory_error`. `CLAUDE.md` puts what the runtimes share in `factory.adapters.agent_launch`, and `state_directory_error` already lives there. S0010 also changed the earlier test row `state-missing` into `state-a-file`, which now fails at the `mkdir`. So the `OSError` branch of `OpencodeRuntime._write_files` (`src/factory/adapters/opencode_runtime.py:625-626`) has no test any more, and the same branch of `ClaudeCodeRuntime._write_files` (`src/factory/adapters/claude_runtime.py:422-423`) had none before. A full disk or a state folder the factory's user cannot write still reaches those lines. This story moves the `mkdir` into one helper in `agent_launch`, which both runtimes call. It also tests, for both runtimes, a state directory that exists but cannot be written. Unchanged: every message and every `AgentRuntimeError` detail, the order of the `mkdir` before the run files' `try`/`finally` (S0010's reason: the cleanup would otherwise hide the error), the runtimes' `_write_files`, and every earlier test. Left to a later story: a shared helper for the write itself, because the two runtimes write different files.

## Interface

`factory.adapters.agent_launch` (adapters):

```python
def make_state_directory(state_directory: Path) -> None:
    """Make `state_directory` with its parents; an `OSError` is `state_directory_error`."""
```

- A missing `state_directory` is made, with its missing parents.
- An existing directory is left as it is, and so are the files in it.
- An `OSError` of the `mkdir` (a file where the folder should be, a parent that cannot be written) raises `state_directory_error(state_directory, error)`, from the `OSError`: an `AgentRuntimeError` whose detail starts `cannot write the state directory <state_directory>: `.

`factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime` (adapters): each runtime's `_make_state_directory` is removed, and `run` calls `make_state_directory(self._state_directory)` at the place where it called the method. Nothing else in either module changes.

Tests (the tester writes them):

- `tests/adapters/test_agent_launch_state_directory.py`, for the helper;
- `tests/adapters/test_runtime_state_directory_write.py`, for both runtimes through their existing stand-ins (`tests/adapters/claude_stand_in.py`, `tests/adapters/opencode_stand_in.py`).

To make the write fail after the `mkdir` succeeds, the test gives a state directory that exists with mode `0o500`. It is skipped when the test runs with root's file rights, as `tests/application/test_tick_stop_records.py` does. `tests/adapters/test_opencode_runtime.py`, `tests/adapters/test_opencode_runtime_runs_folder.py` and the Claude Code runtime's tests pass unchanged.

Two notes of S0004's review, folded in by the human (2026-11-01), each under the human's leave over the named test and nothing else in its file:

- `tests/adapters/test_oauth_token.py`, the row `incomplete-read`: its expected detail is written out as a literal (what `fetch` gives for `http.client.IncompleteRead(b"")`), not computed with the code's own expression `str(CUT_SHORT) or type(CUT_SHORT).__name__`.
- `tests/test_hosting_search.py`: `SECOND` and `SECOND_CLIENT` are renamed to names that say what they hold (for example `ANOTHER_URLLIB_IMPORTER` and `ANOTHER_HTTP_CLIENT_IMPORTER`); the rows keep their ids and what they check.

## Acceptance criteria

1. `make_state_directory`, rows of one test:
   - `<tmp>/a/runs` with neither folder present is made, `a` included;
   - an existing `<tmp>/runs` that holds `keep.txt` is left with `keep.txt` and its text;
   - `<tmp>/state` that is a file raises `AgentRuntimeError` whose detail starts `cannot write the state directory <tmp>/state: `, and the file keeps its text.
2. A run of each runtime (rows `claude` and `opencode` of one test) whose state directory exists with mode `0o500` raises `AgentRuntimeError` whose detail starts `cannot write the state directory <state>: `. The stand-in runtime is never called, and the state directory holds no file afterwards. The rows are skipped with root's file rights.
3. A run of each runtime (rows `claude` and `opencode`) whose state directory is missing makes it and completes with `end_reason` `completed`, as before.
4. The row `incomplete-read` of `tests/adapters/test_oauth_token.py` states its expected detail as a literal; `tests/test_hosting_search.py` holds no name `SECOND` or `SECOND_CLIENT`, and its rows keep their ids.
5. The `AgentRuntimeError` that `make_state_directory` raises for `<tmp>/state` that is a file (criterion 1) has the `OSError` of the `mkdir` as its `__cause__`.
6. `make check` stays green.
7. docs: `docs/project-guide/agents.md`, under the two runtimes: the state directory is made by `agent_launch.make_state_directory`, which both call before they write a run's files. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, because no behaviour an operator sees changes.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; touch "$d/state"; uv run python -c "
import sys
from pathlib import Path
from factory.adapters.agent_launch import make_state_directory
from factory.domain.errors import AgentRuntimeError
root = Path(sys.argv[1])
make_state_directory(root / 'a' / 'runs')
print((root / 'a' / 'runs').is_dir())
try:
    make_state_directory(root / 'state')
except AgentRuntimeError as error:
    print(error.detail.startswith(f'cannot write the state directory {root}/state: '))
" "$d"
```
Expect: two lines, `True` and `True`.

```bash
uv run pytest tests/adapters/test_agent_launch_state_directory.py tests/adapters/test_runtime_state_directory_write.py 2>&1 | tail -1
```
Expect: one line that contains `passed` and contains neither `failed` nor `error`.

## Journal

1. 2026-11-01 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: `agent_launch.make_state_directory(state_directory: Path) -> None` is concrete. It sits next to the existing `state_directory_error` (agent_launch.py:319), and its three rules are stated: a missing directory is made with its parents, an existing one is left alone, and an OSError becomes the detail starting `cannot write the state directory <dir>: `. The runtimes' two `_make_state_directory` methods are removed and `run` calls the helper in their place. The two test notes name their files and the rows or names they change.
   - Criteria: each is testable by one test function. Criterion 1 has the passing rows (missing parent, existing folder with its file) and the failing row (a file where the folder should be, whose text is kept). Criterion 2 is the failing side for both runtimes: mode 0o500, the stand-in never called, no file left, skipped as root. Criterion 3 is the passing side for both runtimes. Criterion 4 covers both test notes, each under the human's leave. Criterion 5 is `make check` and criterion 6 is `docs:`, last. One small gap, not worth a question: the Interface says the error is raised "from the OSError", and no criterion tests the cause. The detail text is tested, which is what matters.
   - Smoke test: the first block is runnable. It makes `a/runs`, prints True, then the file case prints True, so two lines as the `Expect:` says. The second block runs pytest without `-q`, and `pyproject.toml` `addopts` already sets `-q`, so `tail -1` gives the summary line with `passed`. Both `Expect:` lines can be checked against the output.
   - Architecture: the helper goes in `factory.adapters.agent_launch`, where CLAUDE.md puts what the runtimes share, and both runtimes already import from that module. This removes a duplicate helper and adds no layer or dependency. The changes to `tests/adapters/test_oauth_token.py` and `tests/test_hosting_search.py` have the human's leave, given in the story.
   - Scope: this is the acceptance-proposed S0013 listed in feature.md, with decision 22's two folded-in notes. The story's Description says the run behaviour, messages and ordering are unchanged. A shared write helper is left to a later story, and nothing is in the feature's Out of scope.
4. factory: started tests as vm.
5. tester: Wrote tests for criteria 1–4, plus the two test changes the human allowed in the Interface.

   - criterion 1: tests/adapters/test_agent_launch_state_directory.py::test_make_state_directory_makes_a_missing_folder_keeps_an_existing_one_and_refuses_a_file (rows `missing-with-parent`, `existing-with-a-file`, `a-file`; each row checks the whole tree under its root afterwards, so `keep.txt` and the file `state` keep their text)
   - criterion 2: tests/adapters/test_runtime_state_directory_write.py::test_a_run_whose_state_directory_cannot_be_written_fails_before_the_call (rows `claude`, `opencode`; state made with mode 0o500 by the fixture `read_only_state`, which restores 0o755 afterwards; skipped when `os.geteuid() == 0`, as tests/application/test_tick_stop_records.py does; checks the detail prefix, that the stand-in recorded no call, and that the state directory is empty)
   - criterion 3: tests/adapters/test_runtime_state_directory_write.py::test_a_run_makes_its_missing_state_directory_and_completes (rows `claude`, `opencode`)
   - criterion 4: tests/adapters/test_oauth_token.py row `incomplete-read` now expects the literal "IncompleteRead(0 bytes read)" (what `str(http.client.IncompleteRead(b""))` gives). In tests/test_hosting_search.py, `SECOND` became `ANOTHER_URLLIB_IMPORTER` and `SECOND_CLIENT` became `ANOTHER_HTTP_CLIENT_IMPORTER`. Row ids and checks are unchanged. Both changes are under the human's leave in the Interface (2026-11-01), and nothing else in those files changed.

   Files created: tests/adapters/test_agent_launch_state_directory.py, tests/adapters/test_runtime_state_directory_write.py. Earlier test files changed: tests/adapters/test_oauth_token.py and tests/test_hosting_search.py, as listed under criterion 4.

   Module the test run could not import: tests/adapters/test_agent_launch_state_directory.py fails with an ImportError, because `make_state_directory` does not exist yet in `factory.adapters.agent_launch`. The runtime tests (criteria 2 and 3) import only names that already exist. They describe behaviour the runtimes' own `_make_state_directory` and `_write_files` already have, so they are expected to pass both before and after the refactor. They are the regression guard for moving `mkdir` into the helper, not red tests.

   The Interface also says the error is raised "from the OSError". No criterion asks for that, so it is not tested (intake noted the same). `make lint` is green.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/adapters/test_agent_launch_state_directory.py - ImportError while importing test module '/work/checkout/tests/adapters/test_agent_launch_state_directory.py'.
6. factory: started doing as vm.
7. coder: I added `make_state_directory(state_directory)` to `src/factory/adapters/agent_launch.py`, next to `state_directory_error`. It calls `mkdir(parents=True, exist_ok=True)`, and an `OSError` raises `state_directory_error(state_directory, exc) from exc`. I removed `_make_state_directory` from `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`. Each `run` now calls `make_state_directory(self._state_directory)` at the same place, before the run files' `try`/`finally`. Each module also imports the helper. No other code changed. `make check` is green: the new helper tests pass, and so do both rows of the runtime tests for criteria 2 and 3 (the checks ran as uid 1001, so the mode-0o500 rows were not skipped).

   Main choice: the helper takes only the path and raises the error itself, as the Interface states. I rejected having it return the error for the caller to raise (the shape of Claude's `_state_error`), because then both runtimes would repeat the `try`/`except`.

   Refactor pass: I read the diff and found nothing to change.

   Noticed but not touched: `ClaudeCodeRuntime._state_error` (`claude_runtime.py`) now has one caller, `_write_files`. It could be inlined the way `OpencodeRuntime._write_files` calls `state_directory_error` directly, but the Interface says nothing else in either module changes. The remaining coverage gap in `opencode_runtime.py` (line 633, the `_resume` branch with no time left) predates this story and is unrelated. The journal did not change the meaning of the task.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 42 known, 0 gone
8. factory: started review as vm.
9. reviewer: 1. criterion 5 added: it needs its test. The Interface says `make_state_directory` raises `state_directory_error` "from the `OSError`", and the code does this with `raise ... from exc` (`src/factory/adapters/agent_launch.py:329`). No criterion or test covered it, and intake (entry 3) and the tester (entry 5) both named the gap. The new criterion 5 says the `AgentRuntimeError` for `<tmp>/state` that is a file has the `mkdir`'s `OSError` as its `__cause__`. Criteria 6 (`make check`) and 7 (`docs:`) were renumbered. Fix: the tester pins the cause in `tests/adapters/test_agent_launch_state_directory.py`, for example by checking `isinstance(error.__cause__, OSError)` in the row `a-file`. No change under `src/` is needed.

   Checked and found sound:
   - Criteria 1 to 4 each have a test that checks what the criterion says. Criterion 2 works for both runtimes because both stand-ins record their calls in `calls.jsonl` beside them, so `read_calls(tmp_path / "bin")` covers the `opencode` row too. Mode `0o500` lets the `mkdir` succeed and makes `_write_files` fail, which is the uncovered branch the Description names. The root skip matches `tests/application/test_tick_stop_records.py:47`.
   - Architecture: the helper is in `agent_launch`, as `CLAUDE.md` asks for code the runtimes share. Both duplicate `_make_state_directory` methods are removed, and each runtime calls the helper at the same place, before the run files' `try`.
   - Security: no suppression marker was added.
   - `ClaudeCodeRuntime._state_error` now has one caller. I left it, because the Interface says nothing else in either module changes.
   - The local `_tree` in the new helper test is not a copy of `tests/take_support.py:tree`, which also records file modes, and those modes depend on the umask.
   - The journal records `check: green` and `duplicates: 0 new`.

   Earlier tests:
   - tests/adapters/test_oauth_token.py: the human's leave, named in the story's Interface (2026-11-01). Only the row `incomplete-read` changed: its expected detail is now the literal `"IncompleteRead(0 bytes read)"`.
   - tests/test_hosting_search.py: the human's leave, named in the story's Interface (2026-11-01). Only `SECOND` was renamed (now `ANOTHER_URLLIB_IMPORTER`) and `SECOND_CLIENT` (now `ANOTHER_HTTP_CLIENT_IMPORTER`). Row ids and checks are unchanged.
10. factory: started doing as vm.
11. coder: The reviewer's latest entry (9) adds criterion 5, and only its test is missing. Criterion 5: the `AgentRuntimeError` that `make_state_directory` raises for `<tmp>/state` that is a file has the `OSError` of the `mkdir` as its `__cause__`. The code already does this with `raise state_directory_error(state_directory, exc) from exc` (`src/factory/adapters/agent_launch.py`). I changed no code. The tester should pin the cause in `tests/adapters/test_agent_launch_state_directory.py`, row `a-file`, for example by checking `isinstance(error.__cause__, OSError)`. The journal does not change the meaning of the task beyond adding that criterion, which the reviewer has already written into the Description.
12. factory: started tests as vm.
13. tester: I wrote the test for criterion 5, the one the reviewer added (entry 9), which the coder's entry 11 says needs only its test. No other test changed.

    - criterion 5: tests/adapters/test_agent_launch_state_directory.py::test_a_refused_state_directory_keeps_the_mkdir_error_as_its_cause. It puts a file at `<tmp>/state` with the same setup helper the row `a-file` of criterion 1 uses, calls `make_state_directory(<tmp>/state)` and checks that the `AgentRuntimeError`'s `__cause__` is an `OSError`.

    I made it a test function of its own, not an extra check in the row `a-file`. It is a separate criterion, and the role asks for one test per criterion.

    Earlier mapping, unchanged: criterion 1 → test_make_state_directory_makes_a_missing_folder_keeps_an_existing_one_and_refuses_a_file; criterion 2 → tests/adapters/test_runtime_state_directory_write.py::test_a_run_whose_state_directory_cannot_be_written_fails_before_the_call; criterion 3 → tests/adapters/test_runtime_state_directory_write.py::test_a_run_makes_its_missing_state_directory_and_completes; criterion 4 → the edits under the human's leave to tests/adapters/test_oauth_token.py (row `incomplete-read`) and tests/test_hosting_search.py (renamed constants).

    Files created: none in this run. I added the new function to tests/adapters/test_agent_launch_state_directory.py, which this story's earlier tests stage created.

    Modules the test run could not import: none. The code is already in place, so the new test passes: `make test` is green (164.5 s, coverage 99.58 %) and `make lint` is green.

    `lint`: lint: green (0.2 s)
    `test`: test: green (163.7 s)
14. factory: started doing as vm.
15. coder: Round 1: the only finding (entry 9) was the missing test for criterion 5. The tester added it in entry 13: `tests/adapters/test_agent_launch_state_directory.py::test_a_refused_state_directory_keeps_the_mkdir_error_as_its_cause`. The code already raises `state_directory_error(state_directory, exc) from exc` (`src/factory/adapters/agent_launch.py`), so I changed no code this round. The working tree is clean, and `make check` is green (coverage 99.58 %).

    What I built, from round 0, unchanged: `make_state_directory` in `src/factory/adapters/agent_launch.py`. Both `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py` call it in place of their removed `_make_state_directory`, at the same place before the run files' `try`/`finally`.

    Main choice, unchanged: the helper raises the error itself. I rejected having it return the error for each caller to raise, because then both runtimes would repeat the `try`/`except`.

    Refactor pass: no new diff this round, so nothing to change.

    Noticed but not touched, as in entry 7: `ClaudeCodeRuntime._state_error` now has one caller. I left it because the Interface says nothing else in either module changes.

    The journal added criterion 5 and changed nothing else in the meaning of the task. The reviewer already wrote that criterion into the Description.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
16. factory: started review as vm.
17. reviewer: no findings

    I read the whole diff against criteria 1 to 7 and the Interface. The round 0 finding (criterion 5, the cause) is closed.
    - Criterion 1: `tests/adapters/test_agent_launch_state_directory.py::test_make_state_directory_makes_a_missing_folder_keeps_an_existing_one_and_refuses_a_file` has the three rows the criterion names (`missing-with-parent`, `existing-with-a-file`, `a-file`). Each row checks the whole tree under its root afterwards, so the text of `keep.txt` and of the file `state` is checked, and the detail prefix is checked on the failing row.
    - Criterion 2: `tests/adapters/test_runtime_state_directory_write.py::test_a_run_whose_state_directory_cannot_be_written_fails_before_the_call` has the rows `claude` and `opencode`. It checks the detail prefix, that no call was made, and that the state directory is empty. `read_calls(tmp_path / "bin")` works for both rows because both stand-ins write `calls.jsonl` next to themselves (`tests/adapters/claude_stand_in.py:46`, `tests/adapters/opencode_stand_in.py:58`). The test is skipped as root, and the fixture sets the mode back to 0o755 afterwards. Mode 0o500 lets the `mkdir` succeed and makes the write in `_write_files` fail, which is the branch the Description says had no test.
    - Criterion 3: `test_a_run_makes_its_missing_state_directory_and_completes` has both rows and checks `state.is_dir()` and `end_reason == "completed"`.
    - Criterion 4: `incomplete-read` now expects the literal `"IncompleteRead(0 bytes read)"`. `SECOND` and `SECOND_CLIENT` are renamed, and the row ids are unchanged.
    - Criterion 5: `test_a_refused_state_directory_keeps_the_mkdir_error_as_its_cause` checks that `__cause__` is an `OSError`.
    - `make check`: green after the coder (entries 7 and 15), and `duplicates: 0 new`.
    - Architecture: `make_state_directory` sits in `factory.adapters.agent_launch` next to `state_directory_error` (`src/factory/adapters/agent_launch.py:324`). Both `_make_state_directory` copies are gone. Each `run` calls the helper at the same place, before the run files' `try`/`finally` (`claude_runtime.py:365`, `opencode_runtime.py:590`). Nothing else in the runtimes changed.
    - Security: no suppression markers, no strings built into commands.
    - Quality: the helper has a docstring and raises `from exc`. `ClaudeCodeRuntime._state_error` now has one caller, `_write_files`. I left it because the Interface says nothing else in either module changes.
    - Work item hygiene: the Description matches what was built. The journal records the main choice: the helper raises the error itself rather than returning it. The docs criterion (7) still names what the documenter must write in `docs/project-guide/agents.md`.

    Earlier tests:
    - tests/adapters/test_oauth_token.py: changed under the human's leave given in the story's Interface (2026-11-01). Only the expected detail of the row `incomplete-read` changed.
    - tests/test_hosting_search.py: changed under the human's leave given in the story's Interface (2026-11-01). Only `SECOND` was renamed (now `ANOTHER_URLLIB_IMPORTER`) and `SECOND_CLIENT` (now `ANOTHER_HTTP_CLIENT_IMPORTER`). Row ids and checks are unchanged.
18. factory: started docs as vm.
19. documenter: Changed one file, `docs/project-guide/agents.md`, in three places:
    - The `agent_launch` helper list now describes `make_state_directory`. It makes the folder with its parents, leaves an existing folder and its files alone, and raises `state_directory_error` from the `mkdir`'s `OSError`. Both runtimes call it before they write a run's files.
    - The Claude Code runtime's line about the files under `state_directory` now names the helper.
    - The opencode paragraph said the runtime makes its state directory with `_make_state_directory`, a method this story removed. It now names `agent_launch.make_state_directory`. I kept the sentences about the order before the `try` and why.

    Cross-read and found current against the diff: `README.md` and `docs/operator-guide.md`. Neither mentions the removed method, and no behaviour an operator sees changed. I did not touch `docs/decisions.md`; the docs criterion says none, and I did not read it.

    I ran no examples, because I wrote none. I did not run `make check`, because I changed only a document.

    Stale text I saw and did not touch: none. The coder's note stands: `ClaudeCodeRuntime._state_error` now has one caller. That is the coder's code and was left out of scope.

    No findings for the coder. The code matches the Interface and the criteria.

    `check`: check: green (not run again: passed on tree e8f95cf0f330 at 2026-11-01T14:22:11Z)
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok
20. factory: started smoke-test as vm.
21. smoke-tester: I ran both smoke-test commands from the repository root, exactly as written and in order. I ran them as uid 1001, so the mode-0o500 rows of criterion 2 ran and were not skipped. No findings.

    Command 1 (the `make_state_directory` script on a temporary directory):
    ```
    Bytecode compiled 4164 files in 63ms
    True
    True
    ```
    The command exited with 0. It met its `Expect:` line: the script printed two lines, `True` and `True`. The first line is not the script's: it is uv's own note about compiling bytecode.

    Command 2 (`uv run pytest tests/adapters/test_agent_launch_state_directory.py tests/adapters/test_runtime_state_directory_write.py 2>&1 | tail -1`):
    ```
    8 passed in 0.07s
    ```
    It met its `Expect:` line: one line that contains `passed` and contains neither `failed` nor `error`.

    Read against the acceptance criteria, the smoke test contradicts none of them:
    - Criterion 1: the run shows a missing folder made with its parent, and a file in the folder's place refused with the detail prefix `cannot write the state directory <tmp>/state: `.
    - Criteria 1, 2, 3 and 5: their tests are among the 8 that passed.
    - Criterion 4: a grep finds no `SECOND` or `SECOND_CLIENT` in `tests/test_hosting_search.py`.
    - Criterion 7 (docs): `docs/project-guide/agents.md` names `agent_launch.make_state_directory` in the helper list (line 43), for the Claude Code runtime (line 64) and for the opencode runtime (line 114). No `_make_state_directory` is left in `src` or `docs`.
    - Criterion 6 (`make check`): I did not run it in this stage. The factory's own check after the stage is the gate for it.
