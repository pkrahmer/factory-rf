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
  started_at: '2026-10-20T12:44:15.091299Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T12:44:15.085665Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T12:44:15.091299Z'
  stage: intake
---

# The follow-mode test reads only the Python sources

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

`tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode` (F0006-S0006, its exception from F0011-S0005) reads every file under `src/factory` with `SRC.rglob("*")`, bytecode caches included, and fails when one holds `--follow` or `factory-last-line` outside `domain/documents.py` and its `domain/__pycache__/documents.*`. Under `make check` it failed twice during F0041-S0002 (coder entry 15, and the factory's stall in entry 16) and passed when it ran alone and on the next `make check`; the diff did not touch the test or anything it reads. The stall's output kept only the `FAILED` lines and the coverage table, so nobody quoted the failure's `E` lines then; the pre-check (`planning/overnight/precheck/F0041-S0004-1.md`) traced the cause in a throwaway container. Each row of `tests/test_tests_umask.py::test_the_tests_umask_holds_whatever_umask_pytest_was_started_under` (F0033-S0001) starts a child `pytest` whose environment holds only `PATH`, `HOME` and `TMPDIR`, so the child writes bytecode for about a hundred modules under `src/factory/**/__pycache__/`, and its row `077` writes those files with mode `0600`. The factory's `make check` runs as `factory` and the coder's as `agent`, in one checkout shared through the group, so the next check of the other user cannot read them: `read_bytes` raises `PermissionError: [Errno 13] Permission denied: '.../src/factory/entry/__pycache__/wiring.cpython-312.pyc'` in both rows. Which files stay unreadable depends on which row wrote last, so the failure comes and goes. No phrase was ever found: `grep` finds the two phrases under `src/` in `domain/documents.py` alone, and bytecode can only hold a phrase its source holds. This story makes the test read only the Python sources (`*.py`), so a bytecode or temporary file under `src/`, readable or not, can no longer make it fail, and it still fails for any source module that names the follow mode. The test keeps its name and its two rows; nothing under `src/` changes. The umask test's child gets `PYTHONDONTWRITEBYTECODE=1`, which every other process in the container already has, so it writes no bytecode into the checkout at all; a bytecode folder of the agent's would also stop the factory's removal of ignored files (F0027-S0003). Leave: the test is another story's; `feature.md`, decision 14, lets the tester change it as the Interface says, and in nothing else. Found by the coder of F0041-S0002 (entries 15 and 18) and owned by nobody since.

## Interface

No module under `src/factory/` changes; the coder has nothing to build.

`tests/entry/test_watch.py` (the tester, under the leave of `feature.md`, decision 14):

```python
def _files_naming(root: Path, text: bytes) -> list[Path]:
    """The Python sources under `root` that hold `text`, the document check's list left out."""


@pytest.mark.parametrize("text", [b"--follow", b"factory-last-line"])
def test_no_source_file_knows_the_follow_mode(text: bytes) -> None: ...
```

- `_files_naming` reads the files `root.rglob("*.py")` gives, so a file in a `__pycache__` folder or a file whose name does not end in `.py` is never read.
- It leaves out `root / "domain" / "documents.py"`, whose list of replaced phrases has to name them. `_names_the_replaced_phrases(root: Path, path: Path) -> bool` takes the root it compares with (today it compares with `SRC`, so criterion 2's file `domain/documents.py` under `tmp_path` would be found), and it loses its `__pycache__` clause, which the `*.py` pattern makes unneeded.
- `test_no_source_file_knows_the_follow_mode` asserts `_files_naming(SRC, text) == []`.
- `test_the_follow_mode_scan_reads_only_python_sources` (new, in the same module): criterion 2, in `tmp_path`.

`tests/test_tests_umask.py` (the tester, under the leave of `feature.md`, decision 14):

- `test_the_tests_umask_holds_whatever_umask_pytest_was_started_under` gives its child the environment `PATH`, `HOME`, `TMPDIR` and `PYTHONDONTWRITEBYTECODE` (`"1"`); its name, its four rows and its assertions stay.

## Acceptance criteria

1. The scan of the real tree finds nothing (`test_no_source_file_knows_the_follow_mode`, rows `--follow` and `factory-last-line`, ids unchanged): `_files_naming(SRC, text)` is `[]`.
2. The scan reads Python sources only (rows of one parametrized test, a tree in `tmp_path` laid out as `src/factory` is, each row one file that holds `--follow`): `entry/run.py` is found (`[<root>/entry/run.py]`); `domain/documents.py` is not found (`[]`); `domain/__pycache__/watch.cpython-312.pyc` with mode `000` (as a file of the other user is) is not found (`[]`); `entry/notes.txt` is not found (`[]`); `entry/run.py.140000` (a temporary name) is not found (`[]`).
3. The umask test's child writes no bytecode (`test_the_tests_umask_holds_whatever_umask_pytest_was_started_under`, its four rows unchanged): the child's environment holds `PYTHONDONTWRITEBYTECODE` with the value `1`, beside `PATH`, `HOME` and `TMPDIR`, and every row passes.
4. `make check` stays green.
5. docs: none. The change is to a test only. `docs/decisions.md` (the entry of F0011-S0005, *The four documents are checked by a command, outside `make check`*) says that every other file under `src/` is still searched; it stays as it is, as the record of F0011 decision 21, as the entries written before a feature do.

## Smoke test

```bash
uv run pytest tests/entry/test_watch.py -k 'follow_mode_scan or knows_the_follow_mode' 2>&1 | tail -n 1 | sed 's/ in .*//'
```
Expect: `7 passed, 12 deselected` (the two rows of criterion 1 and the five of criterion 2; the count of deselected tests is the module's other tests and may differ by the ones added since)

```bash
grep -c 'rglob("\*")' tests/entry/test_watch.py
```
Expect: `0`

```bash
grep -c '"PYTHONDONTWRITEBYTECODE": "1"' tests/test_tests_umask.py
```
Expect: `1`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
