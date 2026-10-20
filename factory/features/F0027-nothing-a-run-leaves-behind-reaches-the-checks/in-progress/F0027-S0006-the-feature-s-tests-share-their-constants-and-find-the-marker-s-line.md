---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 360
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T19:31:48.534793Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T19:31:48.540844Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T19:32:17.437951Z'
  stage: intake
  run: 129a989c94d34fb1b4cb4252bab4011f
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T19:32:39.049289Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T19:35:13.894185Z'
  stage: tests
  run: 8efe07e8c21c4f259f5b4efa1fce45e1
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T19:35:35.121381Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T19:38:06.011877Z'
  stage: doing
  run: 9f7f77bd22e945c8912d5a271bb12599
---

# The feature's tests share their constants and find the marker's line

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0027's reviewers left three remarks on its own tests that were not findings, and four agents noticed the third one. First, `CLEAN = "git clean --quiet --force --force -d -X"` is defined twice: in `tests/adapters/test_git_cli_ignored.py:13` and in `tests/application/test_sealed_runs_ignored.py:21`. `tests/application/test_tick_ignored.py:83` spells the same text a third time, in its expected stop detail. Second, `Identity(uid=0, user="root", pid=11)` is built three times: in `tests/domain/test_leftovers.py:44` and `:47`, and in `tests/entry/test_leftovers.py:95`. Its sibling `AGENT` already lives in `tests/leftovers_support.py`. Third, `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` pins the `noqa: PLR0913` of `src/factory/entry/leftovers.py` at the literal line `32`. The test finds the line of every other entry by searching for it. So any edit above `def main(` makes the test red, although the marker is still where the human allowed it (F0027-S0001, entries 12, 14, 22, 24 and 26). This story moves the two constants to the shared support modules, under `CLAUDE.md`'s standing leave. It also makes that one entry find `main`'s `def` line the way the test finds its other entries. Every test keeps its name and checks the same thing. Nothing under `src/` changes.

## Interface

No module under `src/factory/` changes. Test helpers, changed:

```python
# tests/git_support.py
CLEAN_IGNORED = "git clean --quiet --force --force -d -X"

# tests/leftovers_support.py
ROOT = Identity(uid=0, user="root", pid=11)
```

- `tests/adapters/test_git_cli_ignored.py` and `tests/application/test_sealed_runs_ignored.py` lose their `CLEAN` and use `git_support.CLEAN_IGNORED`. `tests/application/test_tick_ignored.py` checks `stop.detail.startswith(f"{CLEAN_IGNORED} failed (exit 1)")`, the same prefix it checks today as a literal. `tests/domain/test_leftovers.py` and `tests/entry/test_leftovers.py` use `leftovers_support.ROOT` in place of the three constructions. This is the standing leave to move a shared test helper (`CLAUDE.md`, *Tests*).
- `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`: the entry `"entry/leftovers.py": {32: {"noqa: PLR0913"}}` takes its line number from a search of `src/factory/entry/leftovers.py` for the line that starts `def main(`, the way the test finds the lines of its other entries. Leave: this is beyond the standing leave. The human grants it in F0027's `feature.md`, decision 16, with a line for S0006, before this story starts. The test keeps its name, and its other entries and what it checks stay.
- No new test module.

## Acceptance criteria

1. `tests/` defines the text `git clean --quiet --force --force -d -X` once, as `CLEAN_IGNORED` in `tests/git_support.py`. `tests/adapters/test_git_cli_ignored.py` and `tests/application/test_sealed_runs_ignored.py` hold no `CLEAN` of their own, `tests/application/test_tick_ignored.py` builds its expected detail from `CLEAN_IGNORED`, and every test in the three keeps its name and its rows.
2. `tests/` builds `Identity(uid=0, user="root", pid=11)` once, as `ROOT` in `tests/leftovers_support.py`. `tests/domain/test_leftovers.py` and `tests/entry/test_leftovers.py` use it, and every test keeps its name and its rows.
3. `tests/test_process_search.py` holds no literal line number for `entry/leftovers.py`: its expected marker for that file is `{main_line: {"noqa: PLR0913"}}`, where `main_line` is the number of the line of `src/factory/entry/leftovers.py` that starts `def main(`, found by the same kind of search the test uses for `import_line`, `popen_line`, `exec_line` and `shm_line`. The test stays green, keeps its name, and its other entries are unchanged.
4. `make check` stays green.
5. docs: none. Only tests change, and no document names these constants or the test's line number.

## Smoke test

```bash
grep -rc "git clean --quiet --force --force -d -X" tests | grep -v ":0$"
```
Expect: `tests/git_support.py:1`

```bash
grep -c '{32: {"noqa: PLR0913"}}' tests/test_process_search.py || true
```
Expect: `0`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names concrete helpers (`CLEAN_IGNORED` in `tests/git_support.py`, `ROOT` in `tests/leftovers_support.py`), the five test modules that change, and the one `main_line` search in `tests/test_process_search.py`. No `src/` module changes.
   - Criteria: criteria 1 to 3 each name the exact definition, the users and the unchanged test names, so each can be checked on its own. The Interface states no new rule, validation or error, so no failing side is missing. The only behaviour it states is the `startswith` prefix of `test_tick_ignored.py`, which criterion 1 covers. The leave for the `test_process_search.py` change is the human's, in F0027 `feature.md` decision 16 (S0006 line). The other moves are under the standing leave in `CLAUDE.md`.
   - Smoke test: both commands are runnable grep calls with checkable `Expect:` lines. Neither runs pytest, so the `-q` rule does not apply. The second grep ends in `|| true`, so a count of 0 does not fail it.
   - Architecture: only files under `tests/` change, and they sit in the shared support modules `CLAUDE.md` describes. No layer is touched.
   - Scope: the story stays inside F0027's S0006 line and decision 16. It adds nothing to `feature.md`'s Out of scope.
4. factory: started tests as self.
5. tester: This story only changes tests, so I made the whole change in this stage. The coder has nothing left to write. No test is red: `make test` is green (59.6 s, coverage 99.17 %) and so is `make lint`.

   Criterion → test (each test keeps its name and rows):
   - criterion 1: `tests/adapters/test_git_cli_ignored.py`, `tests/application/test_sealed_runs_ignored.py` and `tests/application/test_tick_ignored.py`. The first two drop their own `CLEAN` and compare with `git_support.CLEAN_IGNORED`. The third checks `stop.detail.startswith(f"{CLEAN_IGNORED} failed (exit 1)")`. The smoke grep shows only `tests/git_support.py:1`.
   - criterion 2: `tests/domain/test_leftovers.py` (rows `root-root`, `root-agent`) and `tests/entry/test_leftovers.py` (row `root`) use `leftovers_support.ROOT`. `Identity(uid=0, user="root", pid=11)` is now built only in `tests/leftovers_support.py`.
   - criterion 3: `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` finds `main_line` with `next(...)` over the lines of `src/factory/entry/leftovers.py`, taking the one where `line.startswith("def main(")`. This is the same kind of search as `import_line` and the others. The expected entry is now `{main_line: {"noqa: PLR0913"}}`, and the other entries are unchanged.
   - criterion 4: `make check` is the coder's gate. Here only `make test` and `make lint` ran, both green.
   - criterion 5: docs: none.

   Files created: none (no new test module). Files changed:
   - `tests/git_support.py` (adds `CLEAN_IGNORED`)
   - `tests/leftovers_support.py` (adds `ROOT`)
   - `tests/adapters/test_git_cli_ignored.py`
   - `tests/application/test_sealed_runs_ignored.py`
   - `tests/application/test_tick_ignored.py`
   - `tests/domain/test_leftovers.py`
   - `tests/entry/test_leftovers.py`
   - `tests/test_process_search.py`

   Leave for these changes: the moves follow the standing leave under `CLAUDE.md` *Tests*. The change to `tests/test_process_search.py` relies on the human's leave in F0027 `feature.md` decision 16, as the Interface cites it. I did not read `feature.md` itself.

   Modules the test run could not import: none. Nothing under `src/` changed.

   `lint`: lint: green (0.6 s)
   `test`: test: green (59.6 s)
6. factory: started doing as self.
7. coder: I built nothing, because the tester already made the whole change and this story only touches tests. `make test` had no failing test to work from. I checked the tester's result as it stands in the working tree:
   - `make check` ends with `check: green`, with coverage at 99.17 %.
   - The first smoke grep prints only `tests/git_support.py:1`.
   - The second smoke grep prints `0`.
   - `git diff main -- src` is empty, so nothing under `src/` changed, as the Interface requires.

   Main choice: I left the tester's eight changed files under `tests/` as they are. The rejected alternative was to touch any of them, for example tidying the `main_line` search in `tests/test_process_search.py`. That would break R9 (the coder never edits tests), and none of the acceptance criteria needs it.

   Refactor: my diff is empty, so there was nothing to refactor.

   Description: no journal entry changed the meaning of the task, so `## Description` stays as it is.

   Noticed but did not touch: nothing.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
