# The operator's folders say what they hold

## Description

This story writes the READMEs of the folders under `operator/` and `agents/`, in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. `operator/template/` gets no README, because an operator copies that folder into a new project and its README would land there (the human, 2026-11-07); this story takes it off the list, its only change to the code.

## Interface

- New files, each in the form of feature decision 2 (`docs/project-guide/style.md`, *Folder READMEs*):
  - `agents/README.md`
  - `operator/bin/README.md`
  - `operator/claude/README.md`
  - `operator/job/README.md`
  - `operator/lib/README.md`
  - `operator/opencode/README.md`
  - `operator/skill/README.md`
  - `operator/vm/README.md`
- Each README says what its folder holds in one sentence and links to the operator guide's page that explains it (for example `operator/vm/` to `docs/operator-guide/machine.md`, `operator/job/` to `docs/operator-guide/cloud-run.md`). A README lists no files: a file line is no part of the form, and what each script does stays in the guide page it links to. `operator/README.md` names each of these folders with a link to its README. `agents/README.md` says what the shipped agent files and their settings are and links to `docs/project-guide/agents.md`.
- `docs/checked-documents.txt` gains each new path, and `operator/README.md`, which S0001 made a document of the check. If the check finds something in `operator/README.md` once it is listed, this story fixes it.
- `factory.shared.domain.folder_readmes.FOLDER_READMES` loses `operator/template/README.md` and holds 22 paths. `operator/README.md`'s line for `template/` says what the folder is for and that it carries no README of its own.
- The tester writes no test that needs a README of this story to exist or to be listed: the coder may not write them, the docs stage writes them after review, and the guard skips a README that does not exist yet. The READMEs are checked by the guard once they exist, by the document check and by the reviewer.
- No other code change, and no change to earlier tests but this one leave of the human's, besides any earlier test whose only failure is the list's new length or the missing path, which may follow it: an earlier guard whose only failure is a `README.md` of this story standing in its folder may add that README to the entries it expects, keeping its name's purpose; the entry names each such test. The story takes the code route for its one change to the list.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/` <one sentence>.`` (no colon, as the guard and the style page write it). The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
2. Every name, path and link in these files exists (the document check finds nothing), and each file is on `docs/checked-documents.txt`.
3. `make documents` ends with `documents ok (<seconds> s)`.
4. `FOLDER_READMES` holds 22 paths and not `operator/template/README.md` (one test).
5. `make check` stays green.
6. docs: the files of the Interface. `operator/README.md`: each subfolder's line links to its README. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal
