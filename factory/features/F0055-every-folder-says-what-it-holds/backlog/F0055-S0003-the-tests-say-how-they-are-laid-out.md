# The tests say how they are laid out

## Description

This story writes the READMEs of `tests/`, `tests/support/` and `tests/guards/`, in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. No code and no test changes.

## Interface

- New files, each in the form of feature decision 2 (`docs/project-guide/style.md`, *Folder READMEs*):
  - `tests/README.md`
  - `tests/support/README.md`
  - `tests/guards/README.md`
- `tests/README.md` says that the tests mirror the package (`tests/<area>/<layer>/`), names each special folder in one line (`support/`, `guards/`, `agent_files/`, `entry/`, `operator_scripts/`, `vm/`) and each area folder in one line, and links to `CLAUDE.md`, *Tests*. `tests/support/README.md` says in one sentence that the folder holds the shared test helpers and links to `docs/project-guide/README.md`, *Shared test helpers*, which keeps the full list of modules and fixtures (feature decision 4). `tests/guards/README.md` says in one sentence that the folder holds the guards and links to the project guide's section on the guards. Neither lists its modules: a module line is no part of the form, and the detail stays in the guide.
- `docs/checked-documents.txt` gains each new path.
- No code and no test changes. The story takes the docs route.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/`: <one sentence>.``. The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
2. Every name, path and link in these files exists (the document check finds nothing), and each file is on `docs/checked-documents.txt`.
3. `make documents` ends with `documents ok (<seconds> s)`.
4. `make check` stays green.
5. docs: the files of the Interface. `docs/project-guide/README.md` keeps its list of shared test helpers unchanged. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal
