---
stage: docs
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 637
comments_read: [6707675447]
handed_over: null
claim:
  instance: vm
  stage: docs
  started_at: '2026-11-07T13:44:17.078397Z'
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
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-07T13:38:29.910335Z'
  stage: doing
  run: 2b841eabef9f4edab2037cfc3fe54092
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T13:38:35.455575Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-07T13:39:15.614954Z'
  stage: review
  run: 98bfd562db5d4183b6db2bb1f1c06ebc
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T13:39:20.386346Z'
  stage: doing
- number: 11
  speaker: coder
  kind: question
  at: '2026-11-07T13:39:40.439799Z'
  stage: doing
  run: e958306d40914ea186a126247f661a2c
  blocked: question
- number: 12
  speaker: human
  kind: comment
  at: '2026-11-07T13:41:27.140871Z'
  stage: doing
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-07T13:41:29.525121Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-07T13:43:36.867408Z'
  stage: doing
  run: dcca117d5c2c44e5b7468ae1d48eda60
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-07T13:43:42.333212Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-11-07T13:44:12.149654Z'
  stage: review
  run: 7f45b9c1d7ba42f18cedf61adb6ef8f8
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-07T13:44:17.078397Z'
  stage: docs
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
7. coder: Removed `operator/template/README.md` from `factory.shared.domain.folder_readmes.FOLDER_READMES` (`src/factory/shared/domain/folder_readmes.py`), so the list now holds 22 paths. That was the story's only code change. The tester's `tests/shared/domain/test_folder_readmes_list.py` passes, and `make check` is green (`check: green`, coverage 99.21 %).

   - Main choice: I deleted the one entry and changed nothing else. I rejected keeping the path and adding a skip for it in the guard, because the Interface says the list loses the path.
   - No earlier test failed because of the new length or the missing path, so the human's leave was not used and no earlier test needs changing.
   - Refactor: the diff is one deleted line, so there was nothing to change.
   - Left for the docs stage, as the Interface says: the eight READMEs (`agents/README.md` and `operator/{bin,claude,job,lib,opencode,skill,vm}/README.md`), the new `docs/checked-documents.txt` entries (with `operator/README.md`), and the `template/` and subfolder link lines in `operator/README.md`. I did not write any of them.
   - The journal did not change the task's meaning, so the Description is unchanged.

   `check`: check: green
   `duplicates`: duplicates: 6 new, 39 known, 4 gone
8. factory: started review as vm.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (one line deleted in `src/factory/shared/domain/folder_readmes.py`, one new test module `tests/shared/domain/test_folder_readmes_list.py`) against the work item.

   - Group 1, acceptance criteria: criterion 4 has its test, `test_the_folder_readme_list_leaves_out_the_template_folder`. It pins the length (22) and the removed path in one assertion, which covers the failing side the Interface names. The tuple now holds 22 entries without `operator/template/README.md`. Criteria 1 to 3 and 6 belong to the docs stage and the guard, as the Interface says. The guard `tests/guards/test_folder_readmes.py` already skips a README that does not exist yet and checks each one that does. The coder's `make check` was green (journal entry 7).
   - Group 2, architecture: the change stays in the shared domain constant. No new imports and no wiring.
   - Group 3, security: nothing relevant. No markers, no secrets.
   - Group 4, quality: the module docstring is present, and the names say what they are. `make duplicates` reports 6 new findings, but they cannot come from this diff, which only deletes a line of `src/`.
   - Group 5, work item hygiene: the journal explains the choice (delete the entry rather than add a guard skip), and the Description matches what was built. The docs criterion misses one document, see finding 1.

   Findings:
   1. `factory/features/F0055-every-folder-says-what-it-holds/in-progress/F0055-S0004-the-operators-folders-say-what-they-hold.md`, criterion 6, against `docs/project-guide/shared.md:207`.
      - What is wrong: `shared.md:207` says `FOLDER_READMES` lists "every folder README of the repository, 23 in all". After this story the list holds 22, and `operator/template/` on purpose has no README. Criterion 6 does not name `shared.md`, so the documenter, who writes from that criterion, will leave the project guide wrong. The document check does not catch a count.
      - Fix: add to criterion 6 something like "`docs/project-guide/shared.md`: `FOLDER_READMES` lists 22 paths, and `operator/template/` carries none because an operator copies that folder into a new project".
      - Related: `docs/decisions.md:1653` also says "the 23 paths". The criterion's "`docs/decisions.md`: none" came from the human, so it stays as is unless the human says otherwise.

   Earlier tests: none. `git diff --name-status main...HEAD` shows only the added test module under `tests/`; no test file that `main` already holds was changed, renamed or deleted.
10. factory: started doing as vm.
11. coder: Round 1: I could not address the reviewer's one finding (entry 9), so I changed nothing.

    The finding asks that criterion 6 also name `docs/project-guide/shared.md`. Line 207 of that page says `FOLDER_READMES` lists "every folder README of the repository, 23 in all". After this story the list holds 22, because `operator/template/` deliberately has no README. The fix belongs in the work item's `## Description`, but the coder's write paths in the pipeline definition do not include `{work_item}`; they are `src/*`, `agents/*` and the `operator/*` folders. `shared.md` is the documenter's file, so I cannot correct the page myself either. The code is unchanged since entry 7: one entry removed from `src/factory/shared/domain/folder_readmes.py`, and `make check` was green then.

    The options I see:
    1. You add to criterion 6 something like: "`docs/project-guide/shared.md`: `FOLDER_READMES` lists 22 paths, and `operator/template/` carries none because an operator copies that folder into a new project." Then I send the item on to review with no code change.
    2. You let the item go on as it is and leave the fix to the docs stage. The documenter writes from criterion 6, so it would likely miss `shared.md` unless a journal entry names it.
    3. You also decide on `docs/decisions.md:1653` ("the 23 paths"). Criterion 6 now says "`docs/decisions.md`: none", and that came from you.

    I would choose option 1. On `decisions.md`, I would keep the entry as it is, because a decision log records what was decided at the time.

    Noticed but not touched: `make duplicates` reported 6 new findings in the last run. They cannot come from this story's one deleted line.
12. 2026-11-07 human: Option 1, and decisions.md stays as it is. Criterion 6 also names docs/project-guide/shared.md: FOLDER_READMES lists 22 paths, and operator/template/ carries none, because an operator copies that folder into a new project. The documenter fixes that sentence at the docs stage. The coder sends the item on to review with no code change; the reviewer reads this answer as part of criterion 6.
13. factory: started doing as vm.
14. coder: Round 1: following the human's answer (entry 12), I am sending the item on to review with no code change.

    - The answer: option 1. Criterion 6 now also names `docs/project-guide/shared.md`, which should say that `FOLDER_READMES` lists 22 paths and that `operator/template/` carries no README, because an operator copies that folder into a new project. The documenter fixes that sentence at the docs stage. `docs/decisions.md` stays as it is.
    - Description: I did not rewrite it. The coder's write paths do not include the work item, so the added part of criterion 6 lives in journal entry 12. The reviewer and the documenter read it there.
    - Code: unchanged since entry 7. One entry is removed from `src/factory/shared/domain/folder_readmes.py`, and the list now holds 22 paths. The working tree is clean.
    - Refactor: nothing to change.
    - `make check`: green again on this run (`check: green`, coverage 99.21 %).

    Noticed but not touched: the earlier `make duplicates` run reported 6 new findings. They cannot come from this story's one deleted line.

    `check`: check: green (not run again: passed on tree b97df92e9a1b at 2026-11-07T13:36:30Z)
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
15. factory: started review as vm.
16. reviewer: Round 1 review. I reviewed `git diff main...HEAD -- . ':!factory'` against the work item and the human's answer in entry 12. The diff has two changes: one line deleted from `src/factory/shared/domain/folder_readmes.py`, and the new test module `tests/shared/domain/test_folder_readmes_list.py`.

    - **Group 1, acceptance criteria:** pass.
      - Criterion 4: `FOLDER_READMES` now holds 22 paths, and `operator/template/README.md` is not among them; I read the tuple on the branch. `test_the_folder_readme_list_leaves_out_the_template_folder` checks both the length and the missing path in one assertion, and that also covers the failing side the Interface names.
      - Criteria 1 to 3 and 6 belong to the docs stage, as the Interface says. The guard `tests/guards/test_folder_readmes.py:42` skips a README that does not exist yet and checks each one that does. `test_every_listed_readme_is_a_readme_of_a_folder_that_exists` still holds for the shorter list.
      - `operator/template/README.md` is no longer named anywhere in `src`, `tests`, `docs/checked-documents.txt` or `operator/README.md`, except in the new test.
      - The coder's `make check` was green (entries 7 and 14).
    - **Group 2, architecture:** pass. The change stays in a shared domain constant, with no new import and no wiring.
    - **Group 3, security:** pass. No secrets and no silencing markers.
    - **Group 4, quality:** pass. The module docstring is present and the names say what they are. The 6 new `make duplicates` findings cannot come from a deleted tuple line.
    - **Group 5, work item hygiene:** pass.
      - The journal gives the main choice: delete the entry, rather than keep it and skip it in the guard.
      - The Description matches what was built.
      - The finding from round 0 (`docs/project-guide/shared.md:207` still says "23 in all") is settled by the human's answer in entry 12. Criterion 6 also names `shared.md`, which should say that `FOLDER_READMES` lists 22 paths and that `operator/template/` carries no README because an operator copies that folder into a new project. `docs/decisions.md` stays as it is.
      - I did not write that addition into the text of criterion 6: the human said the reviewer reads entry 12 as part of criterion 6, and my role lets me correct only the Description. The documenter must read entry 12 together with criterion 6.
    - **Documents:** the diff changes no document.

    no findings

    Earlier tests: none. `git diff --name-status main...HEAD` shows only the added test module under `tests/`; no test file that `main` already holds was changed, renamed or deleted.
17. factory: started docs as vm.
