# The tests say how they are laid out

## Description

This story writes the READMEs of `tests/`, `tests/support/` and `tests/guards/`, in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. No code and no test changes.

## Interface

- New files, each in the form of feature decision 2 (`docs/project-guide/style.md`, *Folder READMEs*):
  - `tests/README.md`
  - `tests/support/README.md`
  - `tests/guards/README.md`
- `tests/README.md` says that the tests mirror the package (`tests/<area>/<layer>/`), names each special folder in one line (`support/`, `guards/`, `agent_files/`, `entry/`, `operator_scripts/`, `vm/`) and each area folder in one line, and links to `CLAUDE.md`, *Tests*. `tests/support/README.md` takes over the list of shared test helpers that `docs/project-guide/README.md`, *Shared test helpers*, holds today (feature decision 4): one line per support module, what it offers, from the module's own docstring. The project guide's section then holds one sentence that links to it. `tests/guards/README.md` names each guard module in one line: what it protects.
- `docs/checked-documents.txt` gains each new path.
- No code and no test changes. The story takes the docs route.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/`: <one sentence>.``. The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
2. Every name, path and link in these files exists (the document check finds nothing), and each file is on `docs/checked-documents.txt`.
3. `make documents` ends with `documents ok (<seconds> s)`.
4. `make check` stays green.
5. docs: the files of the Interface. `docs/project-guide/README.md`, *Shared test helpers*: one sentence that links to `tests/support/README.md`, with the list moved there, no helper dropped. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal
