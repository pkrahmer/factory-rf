---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 637
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-07T13:34:16.540566Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T13:33:16.297508Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T13:33:16.304504Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T13:33:41.984501Z'
  stage: intake
  run: 93060367fc564c0bb881aa6e36fcae59
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T13:33:46.646940Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-07T13:34:11.461903Z'
  stage: tests
  run: 196f4835ebe74815bfcf2852c16850e5
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T13:34:16.540566Z'
  stage: doing
---

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

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names eight concrete README paths, each with the guide page it links to (for example `operator/vm/` to `machine.md`, `operator/job/` to `cloud-run.md`). The one code change is named: `factory.shared.domain.folder_readmes.FOLDER_READMES` loses `operator/template/README.md`, which I confirmed is in the list now. The `operator/README.md` line for `template/` is specified. The leave for earlier guards is bounded and has to be named in the entry.
   - Criteria: each is testable. 1 is the guard's shape check per README, with the subfolder line format. 2 and 3 are the document check. 4 is one test of the list's length (22) and of the removed path. 5 is the usual `make check`. The failing side of the list rule is covered by "not `operator/template/README.md`". Behaviours in the Interface that only the docs stage can show (the `template/` line text, each subfolder line linking its README) sit under criterion 6, which names them. They fall under the document check and the reviewer, as the Interface says.
   - Smoke test: `uv run python -m factory.entry.check_documents | tail -1` is runnable and has no pytest `-q` problem. Its `Expect:` line gives the `documents ok (<seconds> s)` pattern, which the output can be checked against.
   - Docs criterion: criterion 6 names the files and what must be true of them (each subfolder line links to its README; `docs/decisions.md` none). It dictates no sentences.
   - Architecture: the folders `operator/bin`, `claude`, `job`, `lib`, `opencode`, `skill`, `template` and `vm` exist, and `agents/` holds `agents/` and `settings.json`. The operator guide pages the story names exist, and `docs/project-guide/agents.md` is on the checked list. The one code change stays in the shared domain constant.
   - Scope: this is S0004 of F0055 and matches the feature's story list and decision 11. It stays out of the feature's out-of-scope folders (`agents/agents/`, `operator/skill/kumpel/`, `operator/template/factory/`, the commands folders). The route is `tests`, because the story changes the code constant.
4. factory: started tests as vm.
5. tester: Wrote one test, for criterion 4, the story's only code change. As the Interface says, no test needs one of this story's READMEs to exist or to be listed.

   - criterion 1: no new test. The existing guard `tests/guards/test_folder_readmes.py::test_a_folder_readme_agrees_with_its_folder` covers it. It is parametrized over `FOLDER_READMES` and skips a README that does not exist yet. Criterion 1 is met when the docs stage writes the READMEs and the guard skips none of them.
   - criterion 2: no test. The document check (`make documents`) and the reviewer cover it, as the Interface says.
   - criterion 3: no test. It is the docs stage's check `make documents`.
   - criterion 4: `tests/shared/domain/test_folder_readmes_list.py::test_the_folder_readme_list_leaves_out_the_template_folder`. It checks in one assertion that the list holds exactly 22 paths and not `operator/template/README.md`.
   - criterion 5: `make check`, the coder's.
   - criterion 6: docs stage.

   Files created: `tests/shared/domain/test_folder_readmes_list.py`. No earlier test changed.

   Test run: `uv run pytest -q tests/shared/domain/test_folder_readmes_list.py` fails with an AssertionError for the right reason: the list still has 23 entries, `operator/template/README.md` among them. Every module imported; nothing failed to import. `make lint`: green.

   Open: no earlier test checks the list's length or the template path, so I found none that the human's leave would need to change.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
