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
