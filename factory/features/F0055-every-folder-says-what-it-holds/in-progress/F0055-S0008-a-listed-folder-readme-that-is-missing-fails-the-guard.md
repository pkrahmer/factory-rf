---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 640
comments_read: []
handed_over: null
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
