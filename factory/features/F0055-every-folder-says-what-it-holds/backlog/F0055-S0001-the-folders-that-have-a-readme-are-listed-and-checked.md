# The folders that have a README are listed and checked

## Description

The repository is to give every folder a reader would ask about a short `README.md` (feature decision 1). This story builds what keeps those READMEs true; the READMEs themselves come in the later stories. It adds one constant that lists every folder that must have a README, a guard over that list, and the document check's reading of those READMEs, so that they can be put on `docs/checked-documents.txt` and their names and links are checked like the guides'. It also teaches the documenter that it may write them. A README that is on the list but does not exist yet is no finding of the document check; the guard reports it, and the guard is written so that the later stories can turn it green one group at a time. Nothing else the check reads or prints changes.

## Interface

- `factory.shared.domain.folder_readmes` (domain, new):

  ```python
  FOLDER_READMES: Final[tuple[str, ...]]

  def readme_problems(folder: str, readme: str | None, subfolders: Sequence[str]) -> list[str]:
      """What a folder's README and its subfolders disagree on, one line each, sorted."""
  ```

  - `FOLDER_READMES` holds the paths, relative to the root, of every folder of feature decision 1, each ending in `/README.md`: `agents/README.md`, `docs/README.md`, `operator/bin/README.md`, `operator/claude/README.md`, `operator/job/README.md`, `operator/lib/README.md`, `operator/opencode/README.md`, `operator/skill/README.md`, `operator/template/README.md`, `operator/vm/README.md`, `security/README.md`, `src/factory/README.md`, the README of each of the eight packages under `src/factory/` (`agents`, `entry`, `hosting`, `machine`, `pipeline`, `shared`, `watching`, `work`), `tests/README.md`, `tests/support/README.md` and `tests/guards/README.md`, in this order.
  - `readme_problems`: `readme` `None` gives `["<folder>: no README.md"]`. Otherwise every name in `subfolders` that no line ``- `<name>/` `` followed by a sentence names gives `<folder>: <name>/ is not named`, and every such line whose name is not in `subfolders` gives `<folder>: <name>/ does not exist`. A README with no problem gives `[]`.
- `tests/guards/test_folder_readmes.py` (new): for each path of `FOLDER_READMES` whose README exists, `readme_problems` on the real folder gives `[]`, its subfolders read from the folder (hidden folders and `__pycache__` left out). A README that does not exist yet is skipped with its path in the reason, so the guard turns green group by group as the later stories write them. One test checks that every path of `FOLDER_READMES` ends in `/README.md` and names a folder that exists.
- `factory.entry.check_documents`: `_named_documents` also returns each path of `FOLDER_READMES` whose file exists, so the name check reads it and `docs/checked-documents.txt` may list it. A listed path of `FOLDER_READMES` that does not exist yet stays the finding `checked_list_findings` gives today.
- `agents/agents/documenter.md`: where it names the files the documenter may write, it also names the folder READMEs of `FOLDER_READMES` (`factory.shared.domain.folder_readmes`). The human's leave (feature decision 5): the tester changes the earlier tests that pin the documenter's text only so far as this one sentence requires, and any other earlier test whose only failure is this sentence; every changed test keeps its name and what it checks, and the entry names each one.
- The documenter's `write_paths` in `factory/pipeline.yml` are the human's change at this story's merge (feature.md, *The human's changes*), not this story's.

## Acceptance criteria

1. `readme_problems` gives these results, rows of one parametrized test: no README (`["<folder>: no README.md"]`); a README that names each subfolder (`[]`); a subfolder not named; a named subfolder that does not exist; both, sorted; a line ``- `x/` `` without a sentence, which counts as not naming `x/`.
2. Every path of `FOLDER_READMES` ends in `/README.md` and names a folder that exists in the repository (one test).
3. The guard of the Interface passes on today's repository, where none of the new READMEs exist yet, and skips each with its path.
4. With a README written for one listed folder in a copy of the minimal documents (`tests/support/minimal_documents_support.py`), the document check reads it: a missing module it names is a finding, reported while the README is unlisted and blocking once it is listed (rows of one test).
5. `agents/agents/documenter.md` names the folder READMEs among the files the documenter may write (one test).
6. `make check` stays green.
7. docs: `docs/project-guide/shared.md`, the document check: the reader learns which READMEs the check reads and where their list lives. `docs/project-guide/README.md`: the guard of the folder READMEs among the guards. `docs/project-guide/style.md`, a new section *Folder READMEs*: the form of a folder README (feature decision 2). `docs/decisions.md`: one entry for feature decisions 1 to 3, with the rejected option: a README in every folder, which would cost about 25 more files that all say the same.

## Smoke test

```bash
uv run python -c "from factory.shared.domain.folder_readmes import FOLDER_READMES, readme_problems; print(len(FOLDER_READMES), readme_problems('x', None, []))"
```
Expect: `23 ['x: no README.md']`

## Journal
