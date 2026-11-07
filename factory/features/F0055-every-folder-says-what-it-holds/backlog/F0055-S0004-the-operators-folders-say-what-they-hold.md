# The operator's folders say what they hold

## Description

This story writes the READMEs of the folders under `operator/` and `agents/`, in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. No code and no test changes.

## Interface

- New files, each in the form of feature decision 2 (`docs/project-guide/style.md`, *Folder READMEs*):
  - `agents/README.md`
  - `operator/bin/README.md`
  - `operator/claude/README.md`
  - `operator/job/README.md`
  - `operator/lib/README.md`
  - `operator/opencode/README.md`
  - `operator/skill/README.md`
  - `operator/template/README.md`
  - `operator/vm/README.md`
- Each README says what its folder holds in one sentence and links to the operator guide's page that explains it (for example `operator/vm/` to `docs/operator-guide/machine.md`, `operator/job/` to `docs/operator-guide/cloud-run.md`). A folder of scripts names each script in one line, from the script's own header comment. `operator/README.md` names each of these folders with a link to its README. `agents/README.md` says what the shipped agent files and their settings are and links to `docs/project-guide/agents.md`.
- `docs/checked-documents.txt` gains each new path.
- No code and no test changes. The story takes the docs route.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/`: <one sentence>.``. The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
2. Every name, path and link in these files exists (the document check finds nothing), and each file is on `docs/checked-documents.txt`.
3. `make documents` ends with `documents ok (<seconds> s)`.
4. `make check` stays green.
5. docs: the files of the Interface. `operator/README.md`: each subfolder's line links to its README. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal
