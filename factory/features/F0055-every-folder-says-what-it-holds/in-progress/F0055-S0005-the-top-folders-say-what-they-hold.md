# The top folders say what they hold

## Description

This story writes the READMEs of `docs/` and `security/`, and the root `README.md`'s list of folders, in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. No code and no test changes.

## Interface

- New files, each in the form of feature decision 2 (`docs/project-guide/style.md`, *Folder READMEs*):
  - `docs/README.md`
  - `security/README.md`
- `docs/README.md` names the four documents and who reads which (the operator guide, the project guide, the decision log, the operator playbook) and names `runs/` as the human's. `security/README.md` says what the baselines and the semgrep rules are for and links to `CLAUDE.md`, *Checks*. The root `README.md` gains a short list of the top folders, one line each with a link to its README where one exists.
- `docs/checked-documents.txt` gains each new path.
- No code changes, and no test changes but this one leave of the human's: an earlier guard whose only failure is a `README.md` of this story standing in its folder may add that README to the entries it expects, keeping its name's purpose; the entry names each such test. The story takes the docs route.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/` <one sentence>.`` (no colon, as the guard and the style page write it). The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
2. Every name, path and link in these files exists (the document check finds nothing), and each file is on `docs/checked-documents.txt`.
3. `make documents` ends with `documents ok (<seconds> s)`.
4. `make check` stays green.
5. docs: the files of the Interface. `README.md`: the list of top folders. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal
