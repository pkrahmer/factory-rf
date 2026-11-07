---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 640
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T14:53:57.108425Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T14:53:57.115729Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T14:54:17.059914Z'
  stage: intake
  run: ce19b8efcc704376b197045219973e65
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T14:54:22.836784Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-07T14:55:08.081227Z'
  stage: tests
  run: 1c224e6efbb64ff5928a4a34ad4cbbfe
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T14:55:14.269133Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-07T14:59:26.801759Z'
  stage: doing
  run: 0296d9a54f3946eeb3a2f1c5d48602b1
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T14:59:31.657840Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-07T15:00:04.673177Z'
  stage: review
  run: 783eae4bf42e4150b755db2b0fdc3c14
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T15:00:09.870533Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-11-07T15:04:29.038158Z'
  stage: docs
  run: 0ec81675f2f8486bac6b98a35849d523
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T15:04:33.892180Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-11-07T15:05:00.611144Z'
  stage: smoke-test
  run: 0ded7499e5d244d4b6d3750b15936aa3
- number: 14
  speaker: factory
  kind: done
  at: '2026-11-07T15:05:50.484367Z'
  stage: approval
---

# A listed folder README that is missing fails the guard

## Description

The guard over the folder READMEs skips a README on `FOLDER_READMES` that has no file, so that the stories that wrote the READMEs could turn it green group by group. Every README on the list now exists, but the skip stayed: deleting `src/factory/agents/README.md` or `security/README.md` leaves `make check` green, with the guard reporting the two skips. Only `make documents`, a check of the docs stages and not of `make check`, notices it (a listed path with no file). This story makes the guard fail on a listed README with no file, with the finding `<folder>: no README.md` that `readme_problems` already gives for a missing README. It changes no code under `src/`, no README and nothing the document check reads. `tests/guards/test_test_folder_readmes.py`, which pins that the three test-folder READMEs exist, becomes redundant with this guard; this story leaves it as it is (removing it would be the human's call).

## Interface

- `tests/guards/test_folder_readmes.py` (written by F0055-S0001), a new private helper:

```python
def _listed_readme_problems(root: Path, path: str) -> list[str]
```

- `_listed_readme_problems` reads `<root>/<path>`; a path with no file is read as `None`, so it gives `["<folder>: no README.md"]`, where `<folder>` is `path` without `/README.md`.
- A README that exists gives what `readme_problems` gives for it, with the subfolders read by `_subfolders` from `<root>/<folder>`.
- `test_a_folder_readme_agrees_with_its_folder` calls `_listed_readme_problems(ROOT, path)` for every path of `FOLDER_READMES`, asserts `[]`, and skips none. Its module docstring says that every listed folder README exists and agrees with its folder.
- The human's leave (2026-11-07): the tester changes `tests/guards/test_folder_readmes.py::test_a_folder_readme_agrees_with_its_folder` and the module's docstring only so far as dropping the skip requires; the test keeps its name and checks the same agreement, and a listed README with no file now fails it. Any other earlier test whose only failure is this change may follow it.
- No change under `src/`, and no change to `FOLDER_READMES`.

## Acceptance criteria

1. `_listed_readme_problems` gives these results on a folder `x` under `tmp_path`, rows of one parametrized test: a README in the form that names its one subfolder `y/` gives `[]`; no `README.md` gives `["x: no README.md"]`; a README in the form that does not name the subfolder `y/` gives `["x: y/ is not named"]`.
2. `test_a_folder_readme_agrees_with_its_folder` has no skip: run on the repository, every row of `FOLDER_READMES` passes and none is skipped.
3. `make check` stays green.
4. docs: `docs/project-guide/shared.md`, *The folder READMEs*: the reader learns that the guard fails on a listed README with no file, instead of skipping it.

## Smoke test

```bash
uv run pytest -rs tests/guards/test_folder_readmes.py 2>&1 | tail -1 | grep -c skipped
```
Expect: `0`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git clone --quiet . "$d/r" && rm "$d/r/security/README.md"
here=$(pwd); cd "$d/r" && uv run --project "$here" pytest -o addopts= tests/guards/test_folder_readmes.py 2>&1 | grep -q 'security: no README.md' && echo missing-fails
```
Expect: `missing-fails`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names the private helper `_listed_readme_problems(root: Path, path: str) -> list[str]` in `tests/guards/test_folder_readmes.py`. It gives the missing-file result, the existing-README result through `readme_problems` and `_subfolders`, and the changed test. The human's leave (2026-11-07) for the test change is in the Interface.
   - Criteria: criterion 1 is one parametrized test with three rows (a README that names `y/` gives `[]`, a missing README gives `["x: no README.md"]`, a README that does not name `y/` gives `["x: y/ is not named"]`). Both messages match `src/factory/shared/domain/folder_readmes.py` (lines 108 and 133). Criterion 2 covers the no-skip rule: its failing side is the missing-README row of criterion 1, and its passing side is the run on the repository. Criteria 3 and 4 are the two closing ones.
   - Smoke test: both commands are runnable. `addopts` is `-q`, and the first command adds no `-q`, so the last line is the summary and `grep -c skipped` can give 0. The second command uses `-o addopts=` and a clone with `security/README.md` removed. Each `Expect:` can be checked against the output.
   - Docs criterion: names what the reader must know (the guard fails on a listed README with no file instead of skipping it) and dictates no sentences. The page and section exist: `docs/project-guide/shared.md`, *The folder READMEs*.
   - Architecture: the change is test-only under `tests/guards/`, with no change to `src/`, and the guard stays in the layout CLAUDE.md describes.
   - Scope: the story is inside F0055's folder-README guard (S0001). It leaves `tests/guards/test_test_folder_readmes.py` alone, and the Description says so. It changes nothing in `FOLDER_READMES`.

   Route: `tests`. The Interface changes only a test file, which the documenter may not write.
4. factory: started tests as vm.
5. tester: Tests written. All of this story's code is in one test file, so the tests are green now rather than red.

   - criterion 1: tests/guards/test_folder_readmes.py::test_a_listed_readme_gives_its_problems_and_a_missing_one_fails, with three rows on `x` under `tmp_path`, each with the subfolder `y/`:
     - `names-its-subfolder`: a README in the form that names `y/` gives `[]`.
     - `no-readme`: no `README.md` gives `["x: no README.md"]`.
     - `subfolder-not-named`: a README in the form that does not name `y/` gives `["x: y/ is not named"]`.
   - criterion 2: tests/guards/test_folder_readmes.py::test_a_folder_readme_agrees_with_its_folder. It now only asserts `_listed_readme_problems(ROOT, path) == []` for every path in `FOLDER_READMES`, with no skip.
   - criterion 3 (`make check`) and criterion 4 (docs) have no test of their own.

   Files: I created none. I changed only `tests/guards/test_folder_readmes.py`, under the human's leave of 2026-11-07 named in the Interface:
   - The module docstring now says that every listed folder README exists, agrees with its folder and keeps the README's form.
   - `test_a_folder_readme_agrees_with_its_folder` keeps its name, checks the same agreement and no longer skips.
   - I added the private helper `_listed_readme_problems(root, path)` exactly as the Interface describes it. A missing file is read as `None` and handed to `readme_problems`, and the subfolders are read by `_subfolders(root / folder)`.
   - I added two module constants, `NAMING_README` and `SILENT_README`, as the data for the criterion-1 test.

   Why the helper is mine: it lives in a test module, and the coder never edits tests (R9). Intake routed the story to this stage for that reason, so writing it here is the only way the Interface gets built.

   Result: no test fails before an implementation, because there is no implementation outside the tests. One run of `uv run pytest -q tests/guards/test_folder_readmes.py`: 31 passed, no skips. `make lint` is green. Every module the tests import already exists, so none was missing.

   Left open for the coder: no change under `src/` is called for. The coder's `make check` is all that remains.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: No code change. The story's whole Interface sits in a test module, and the tester already built it there: `_listed_readme_problems` and the unskipped `test_a_folder_readme_agrees_with_its_folder` are in `tests/guards/test_folder_readmes.py`. The Interface rules out any change under `src/` or to `FOLDER_READMES`, so I had nothing to implement, and the working tree is unchanged.

   - Checked: `make check` ends with `check: green` (test: green, coverage 99.22 %). `uv run pytest -rs tests/guards/test_folder_readmes.py` ends with `31 passed` and no skips, which is what the first smoke test expects.
   - Main choice: hand forward with an empty diff. The alternative I rejected was adding a helper under `src/factory/shared/domain/folder_readmes.py` (a function that reads a listed README). The Interface forbids changes under `src/`, and that would duplicate the test helper.
   - Refactor step: no diff of mine to read, so nothing to change.
   - Noticed, not touched: the Description already says `tests/guards/test_test_folder_readmes.py` is now redundant with this guard. Removing it is the human's call. The journal did not change the task's meaning, so `## Description` stays as it is.

   `check`: check: green
   `duplicates`: duplicates: 6 new, 39 known, 4 gone
8. factory: started review as vm.
9. reviewer: no findings

   What I read: the work item, and `git diff main...HEAD -- . ':!factory' ':!uv.lock'`. Only `tests/guards/test_folder_readmes.py` changed, and there is no change under `src/`.

   - Group 1, acceptance criteria:
     - Criterion 1 is `test_a_listed_readme_gives_its_problems_and_a_missing_one_fails`. It has three parametrized rows on `x/y` under `tmp_path`: `names-its-subfolder` gives `[]`, `no-readme` gives `["x: no README.md"]`, and `subfolder-not-named` gives `["x: y/ is not named"]`. The expected messages match `src/factory/shared/domain/folder_readmes.py:108,133`.
     - Criterion 2 is `test_a_folder_readme_agrees_with_its_folder`. It now only asserts `_listed_readme_problems(ROOT, path) == []`, with no skip.
     - The Interface's rules are both covered. The missing file is read as `None` (the `no-readme` row). An existing README goes through `readme_problems` with the subfolders from `_subfolders(root / folder)` (the other two rows). The folder is `path` without `/README.md`.
     - The coder's journal entry 7 shows `make check` green.
   - Group 2, architecture: the change is test-only, under `tests/guards/`, with no change to `src/` or `FOLDER_READMES`, as the Interface requires.
   - Group 3, security: no markers, no secrets, no shell built from strings.
   - Group 4, quality:
     - `_listed_readme_problems` reuses `readme_problems` and `_subfolders`, so no logic is copied. No such helper exists under `src/`: `readme_problems` is called nowhere else.
     - The new README constants are not copies of `FOLDER_README_TEXT` in `tests/entry/test_check_documents_folder_readmes.py`, which is different text built for a different check.
     - The module docstring was updated.
   - Group 5, work item hygiene: the Description matches what was built, including the note that `tests/guards/test_test_folder_readmes.py` is left alone. The journal explains the choices: the helper sits in a test module, so the tester built it, and the coder handed on an empty diff and said why. The docs criterion still names what the reader must learn.
   - Documents: the diff changes no document.

   Earlier tests:
   - `tests/guards/test_folder_readmes.py` (written by F0055-S0001) was changed under the human's leave of 2026-11-07, named in the story's Interface. Within that leave, the skip was dropped from `test_a_folder_readme_agrees_with_its_folder`, which keeps its name and checks the same agreement, and the module docstring was updated. Everything else in the file is added: the private helper, the README constants and the new criterion-1 test.
10. factory: started docs as vm.
11. documenter: Changed one file:
    - `docs/project-guide/shared.md`, *The folder READMEs*, the guard bullet. It said the guard runs on every listed README that exists and skips one that does not. It now says the guard runs on every listed README, and that a listed README with no file fails with `<folder>: no README.md` and nothing is skipped. I checked this against the diff of `tests/guards/test_folder_readmes.py` (`_listed_readme_problems`, and the test with no skip).

    `make documents` ended with `documents ok (60.9 s)`. I ran no `make check`, because I changed only a document.

    Cross-read and found current:
    - the other bullets of *The folder READMEs* (the name check, `FOLDER_READMES`, `readme_problems`)
    - `README.md`
    - `docs/operator-guide/`

    I found no other text about skipping a folder README.

    Noticed and not touched: `tests/guards/test_test_folder_readmes.py` is now redundant with this guard. The story leaves it for the human to decide.

    No findings for the coder. There is no `decisions.md` entry, because the story names no lasting decision.

    `check`: check: green
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok (59.1 s)
12. factory: started smoke-test as vm.
13. smoke-tester: Smoke test passed with no findings. I ran both commands from the repository root exactly as written, in order.

    Command 1: `uv run pytest -rs tests/guards/test_folder_readmes.py 2>&1 | tail -1 | grep -c skipped`
    ```
    0
    ```
    It met `Expect: 0`. The summary line it read was `31 passed in 0.03s`, with no skips. (`grep -c` exits 1 when the count is 0; the output is what the expectation checks.)

    Command 2: I cloned to a `mktemp -d` directory that cleans itself up with its own `trap`, removed `security/README.md`, and ran the guard with `-o addopts=`:
    ```
    missing-fails
    ```
    It met `Expect: missing-fails`, so the guard reported `security: no README.md` and failed.

    Checked against the acceptance criteria:
    - Criterion 1: not contradicted. Command 2 shows a listed README with no file giving `<folder>: no README.md`.
    - Criterion 2: not contradicted. Command 1 ran every row of `FOLDER_READMES` on the repository: all passed and none was skipped.
    - Criterion 3: not contradicted. I did not run `make check` because the smoke test does not call it. The factory's checks after the doing and docs stages recorded `check: green`.
    - Criterion 4: not contradicted. `docs/project-guide/shared.md:212`, under *The folder READMEs*, says that a listed README with no file fails the guard with `<folder>: no README.md` and that nothing is skipped.

    Findings: none.

    Still open, as earlier entries say: `tests/guards/test_test_folder_readmes.py` now does the same job as this guard, and whether to remove it is the human's call. I left nothing behind in `/tmp`.
14. factory: done (pull request merged); cost: 6 runs, 5.4 min, 37 turns, 162235 tokens in (597903 more from cache), 10452 out, $1.40
