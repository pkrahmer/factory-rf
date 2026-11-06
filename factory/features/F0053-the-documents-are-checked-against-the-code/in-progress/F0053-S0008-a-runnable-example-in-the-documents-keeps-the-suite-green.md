---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 593
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-06T11:41:17.936338Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T11:40:54.929037Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T11:40:54.936100Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T11:41:12.322650Z'
  stage: intake
  run: 3db6db9d613343e99367272a983ab60b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T11:41:17.936338Z'
  stage: tests
---

# A runnable example in the documents keeps the suite green
## Description

The document check runs a document's `console` blocks (S0003, S0006), and the documenter's rules ask for every command to be shown as one (S0005). But no document can hold one today. The shared test fixture `documents` (`tests/conftest.py`) copies the real documents into a folder under `tmp_path` that is no git repository. There the `checkout` and `instance` fixtures cannot be prepared, so one `console` block in any document the check reads turns five rows of `test_the_operator_guide_folder_is_checked_per_file` red. S0003's docs stage stalled on exactly this, and `docs/project-guide/style.md` now shows its own examples as `text` blocks. The feature acceptance reproduced it: one `console` block (`$ echo hi` / `hi`) appended to `docs/project-guide/shared.md` in a clone gave `5 failed, 7 passed`. This story makes the copy a git repository with one commit of the copied files, so that both fixtures can be prepared and a real example in a real document runs in the tests as it does in `make documents`. It also turns the two demonstration blocks of the style page back into `console` blocks, so that the page's own examples are checked. The product code stays as it is. Rejected: filtering the example lines out of the earlier test's comparison, which still fails for a listed file, where a fixture that cannot be prepared blocks.

## Interface

- `tests/conftest.py`, the fixture `documents` (moved there by F0053-S0002): after copying, it makes `root` a git repository holding every copied file in one commit, through `run_git` and `commit_all` of `tests/support/git_support.py`. It keeps its name and returns the same folder.
- The tests that use `documents` (`tests/entry/test_check_documents*.py`) keep their names and what they check. A test that now needs a git repository where it changes a file (a `change` that edits a document) commits that change before it calls `main`, or the fixture's commit is enough because the checkout fixture exports the committed state. The tester names each such test.
- This changes tests that F0053-S0002 and F0053-S0003 wrote, beyond the standing leave. Feature decision 6 gives the leave.
- No module under `src/` changes.

## Acceptance criteria

1. With the fixture `documents`, a `console` block (`$ echo hi` / `hi`) appended to a copied `docs/project-guide/shared.md` and committed gives no finding for that block, and every row of `test_the_operator_guide_folder_is_checked_per_file` passes (one test, two rows: the block in an unlisted page and the block in `docs/project-guide/style.md`, which is listed).
2. A `console` block whose output differs (`$ echo one` / `two`) in the listed `docs/project-guide/style.md` of the copy fails `main` with `docs/project-guide/style.md:<line>: the example printed one` and exit status 1. The same block in an unlisted page is printed under `Report (not checked yet):`, and the exit status is 0 (rows of one test).
3. `git -C <root> status --porcelain` in the copy the fixture returns prints nothing, and `git -C <root> rev-parse --is-inside-work-tree` prints `true`.
4. `make check` stays green.
5. docs: `docs/project-guide/style.md`, *Runnable examples*: the demonstration blocks are `console` blocks again and are run by `make documents`. The reader learns that a document's examples run in the tests' copies too, so a wrong example fails the suite only in a listed file. `docs/project-guide/shared.md`, *The document check*: none, the machinery is unchanged.

## Smoke test

```bash
grep -c '^```console' docs/project-guide/style.md
```
Expect: a number greater than `0`

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

```bash
uv run pytest tests/entry/test_check_documents_operator_guide.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete pieces, the `documents` fixture in `tests/conftest.py`, `run_git` and `commit_all` in `tests/support/git_support.py` (both exist), and the `tests/entry/test_check_documents*.py` files (they exist). `src/` is unchanged and the leave for the earlier tests is given by feature decision 6.
   - Criteria: 1 and 2 are each testable by one parametrized test, and rule 2 covers both sides (listed file fails with the message and exit 1, unlisted file reports and exits 0). 3 covers both git properties of the fixture. 4 is the `make check` criterion. Each is testable without further decisions.
   - Smoke test: the three commands are runnable. The pytest command passes no `-q`, and `pyproject.toml` already sets `addopts = "-q ..."`, so `tail -1 | grep -c passed` meets the summary line. Each `Expect:` can be checked against the output.
   - Docs criterion: it names what the reader must know (the examples run in the tests' copies, and a wrong example fails the suite only in a listed file). It dictates no sentences.
   - Architecture: only test code changes. The fixture stays in `tests/conftest.py` and reuses the shared git helpers instead of a new copy.
   - Scope: it is within F0053 (runnable examples, S0003/S0006) and outside its "Out of scope". The changes to the S0002 and S0003 tests are covered by decision 6.
4. factory: started tests as vm.
