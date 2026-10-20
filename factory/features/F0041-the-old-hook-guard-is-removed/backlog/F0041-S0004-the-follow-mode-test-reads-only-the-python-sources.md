# The follow-mode test reads only the Python sources

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

`tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode` (F0006-S0006, its exception from F0011-S0005) reads every file under `src/factory` with `SRC.rglob("*")`, bytecode caches included, and fails when one holds `--follow` or `factory-last-line` outside `domain/documents.py` and its `domain/__pycache__/documents.*`. Under `make check` it failed twice during F0041-S0002 (coder entry 15, and the factory's stall in entry 16) and passed every time it ran alone and on the next `make check`; the diff did not touch the test or anything it reads. Nobody could quote the failure's `E` lines, because the stall's output kept only the `FAILED` lines and the coverage table, so the cause is not traced. Wherever the file it caught came from, it was not a source file: `grep` finds the two phrases under `src/` in `domain/documents.py` alone, and bytecode can only hold a phrase its source holds. This story makes the test read only the Python sources (`*.py`), so a file that a worker writes or removes under `src/` while the test runs (a bytecode cache, a temporary file) can no longer make it fail, and it still fails for any source module that names the follow mode. The test keeps its name and its two rows; nothing under `src/` changes. Leave: the test is another story's; changing it needs the human's leave, which `feature.md` does not give yet (to be added under the feature's decisions when this story is refined). Found by the coder of F0041-S0002 (entries 15 and 18) and owned by nobody since.

## Interface

No module under `src/factory/` changes; the coder has nothing to build.

`tests/entry/test_watch.py` (the tester, under the leave the human adds to `feature.md`):

```python
def _files_naming(root: Path, text: bytes) -> list[Path]:
    """The Python sources under `root` that hold `text`, the document check's list left out."""


@pytest.mark.parametrize("text", [b"--follow", b"factory-last-line"])
def test_no_source_file_knows_the_follow_mode(text: bytes) -> None: ...
```

- `_files_naming` reads the files `root.rglob("*.py")` gives, so a file in a `__pycache__` folder or a file whose name does not end in `.py` is never read.
- It leaves out `root / "domain" / "documents.py"`, whose list of replaced phrases has to name them; `_names_the_replaced_phrases` loses its `__pycache__` clause, which the `*.py` pattern makes unneeded.
- `test_no_source_file_knows_the_follow_mode` asserts `_files_naming(SRC, text) == []`.
- `test_the_follow_mode_scan_reads_only_python_sources` (new, in the same module): criterion 2, in `tmp_path`.

## Acceptance criteria

1. The scan of the real tree finds nothing (`test_no_source_file_knows_the_follow_mode`, rows `--follow` and `factory-last-line`, ids unchanged): `_files_naming(SRC, text)` is `[]`.
2. The scan reads Python sources only (rows of one parametrized test, a tree in `tmp_path` laid out as `src/factory` is, each row one file that holds `--follow`): `cli/run.py` is found (`[<root>/cli/run.py]`); `domain/documents.py` is not found (`[]`); `domain/__pycache__/watch.cpython-312.pyc` is not found (`[]`); `cli/notes.txt` is not found (`[]`); `cli/run.py.140000` (a temporary name) is not found (`[]`).
3. `make check` stays green.
4. docs: none. The test is not described in `README.md` or `docs/`.

## Smoke test

```bash
uv run pytest tests/entry/test_watch.py -k 'follow_mode_scan or knows_the_follow_mode' 2>&1 | tail -n 1 | sed 's/ in .*//'
```
Expect: `7 passed, 12 deselected` (the two rows of criterion 1 and the five of criterion 2; the count of deselected tests is the module's other tests and may differ by the ones added since)

```bash
grep -c 'rglob("\*")' tests/entry/test_watch.py
```
Expect: `0`

## Journal
