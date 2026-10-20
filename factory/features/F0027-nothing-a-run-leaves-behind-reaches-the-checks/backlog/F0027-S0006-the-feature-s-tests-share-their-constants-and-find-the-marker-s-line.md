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

- `tests/adapters/test_git_cli_ignored.py` and `tests/application/test_sealed_runs_ignored.py` lose their `CLEAN` and use `git_support.CLEAN_IGNORED`. `tests/application/test_tick_ignored.py` builds its expected detail as `f"{CLEAN_IGNORED} failed (exit 1)"`. `tests/domain/test_leftovers.py` and `tests/entry/test_leftovers.py` use `leftovers_support.ROOT` in place of the three constructions. This is the standing leave to move a shared test helper (`CLAUDE.md`, *Tests*).
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
