---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 636
comments_read: [6707209251, 6707304987, 6707415610]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-07T13:22:52.688212Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T12:53:07.765734Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T12:53:07.773191Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-07T12:53:39.103633Z'
  stage: intake
  run: 0ce00804ad524f8ba09e3b96104c90cf
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-07T12:55:25.780069Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-07T12:55:28.225516Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-07T12:55:45.064772Z'
  stage: intake
  run: e4932ebc626d4609bc95cb4b56754b86
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T12:55:50.184206Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-07T13:01:26.419269Z'
  stage: tests
  run: dc58e30d11574fc58d5f328e36a3614e
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-07T13:01:31.482798Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-07T13:02:05.843573Z'
  stage: doing
  run: 9a70c9c27b9f444295896f3576a82069
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-07T13:05:57.651319Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T13:06:00.155966Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-07T13:11:45.051599Z'
  stage: doing
  run: 0ef0e8bb853847a2afda9d7f81202afd
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T13:11:50.177574Z'
  stage: review
- number: 15
  speaker: reviewer
  kind: question
  at: '2026-11-07T13:12:50.927568Z'
  stage: review
  run: bf3958f6364c47ee904394dc00c555e9
  blocked: question
- number: 16
  speaker: human
  kind: comment
  at: '2026-11-07T13:16:41.897216Z'
  stage: review
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-07T13:16:44.322393Z'
  stage: review
- number: 18
  speaker: reviewer
  kind: result
  at: '2026-11-07T13:17:24.077030Z'
  stage: review
  run: bd77f179cfd64f12aa49aa0ff9296eba
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-07T13:17:29.095008Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-11-07T13:22:47.188370Z'
  stage: doing
  run: e1c462e63f544799b5895616d976a405
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-07T13:22:52.688212Z'
  stage: review
---

# The tests say how they are laid out

## Description

This story writes the READMEs of `tests/`, `tests/support/` and `tests/guards/`, in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. No code and no test changes.

## Interface

- New files, each in the form of feature decision 2 (`docs/project-guide/style.md`, *Folder READMEs*):
  - `tests/README.md`
  - `tests/support/README.md`
  - `tests/guards/README.md`
- `tests/README.md` says that the tests mirror the package (`tests/<area>/<layer>/`), names each special folder in one line (`support/`, `guards/`, `agent_files/`, `entry/`, `operator_scripts/`, `vm/`) and each area folder in one line, and links to `CLAUDE.md`, *Tests*. `tests/support/README.md` says in one sentence that the folder holds the shared test helpers and links to `docs/project-guide/README.md`, *Shared test helpers*, which keeps the full list of modules and fixtures (feature decision 4). `tests/guards/README.md` says in one sentence that the folder holds the guards and links to `docs/project-guide/README.md`, *The files*. Neither lists its modules: a module line is no part of the form, and the detail stays in the guide.
- `docs/checked-documents.txt` gains each new path.
- No code changes, and no test changes but this one leave of the human's: an earlier guard whose only failure is a `README.md` of this story standing in its folder may add that README to the entries it expects, keeping its name's purpose; this includes `tests/guards/test_tests_layout.py::test_the_root_holds_only_conftest_and_packages` and any other check of that file or another earlier guard. The tester runs the guards with the three READMEs in place to find every such check, and its entry names each. The story takes the tests route.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/` <one sentence>.`` (no colon, as the guard and the style page write it). The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
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

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: 1. Route conflict with the test change. `tests/guards/test_tests_layout.py::test_the_root_holds_only_conftest_and_packages` asserts that the files in `tests/` are exactly `["conftest.py"]`, so the new `tests/README.md` makes it fail. The Interface grants a leave to change such a guard, but the story takes the docs route, which has no tests stage, and the documenter's write paths (`factory/pipeline.yml`) hold no `tests/*` path beyond the three READMEs. Nobody on that route can make the change, so `make check` cannot go green. Options: (a) route the story `tests`: the tester adds `README.md` to the expected entries of that one test, and the criteria and Interface drop "docs route" (I would choose this); (b) the human changes the test in the story's branch before it starts. Please also say whether the same guard has other checks that trip on a `README.md` in `tests/`, `tests/support/` or `tests/guards/`. I looked only at the root-files test.
   2. The Interface says `tests/guards/README.md` links to "the project guide's section on the guards", but `docs/project-guide/README.md` has no such section. The guards are described in a bullet under *The files* (line 66) and in the paragraphs after it. The document check resolves heading references (S0006), so the link needs a heading that exists. Which one should it be: *The files*, or a new *Guards* section? A new section would be a docs change that criterion 5 doesn't name, since it says the guide's list stays unchanged. I would choose linking *The files*.
   3. Criterion 1 requires at least one link to a guide page, and it says `tests/support/README.md` links to *Shared test helpers*. That heading exists, so this part is fine. The criteria never name which heading `tests/README.md` links to besides `CLAUDE.md`, *Tests*. Please confirm that link target alone is enough.

   Findings of the form check: none (passed). The other checks look fine. The Interface is concrete, the smoke test is runnable, and `addopts` doesn't matter because the smoke test doesn't call pytest. The docs criterion dictates no sentences. The architecture and the scope fit feature decisions 2, 4 and 6.
4. 2026-11-07 human: 1. (a): the story goes to tests. The tester adds README.md to the expected entries of test_the_root_holds_only_conftest_and_packages, and of any other check of tests/guards/test_tests_layout.py or another earlier guard whose only failure is one of this story's three READMEs, under the leave in the Interface; the entry names each. Drop 'docs route' from the Interface and criteria. The tester runs the guards with the three READMEs in place to find every such check.
   2. Link *The files* in docs/project-guide/README.md. No new section.
   3. Yes: CLAUDE.md, *Tests*, alone is enough for tests/README.md.
5. factory: started intake as vm.
6. intake: accepted, on the tests route, with the human's answers (journal entry 4) carried in.
   - Interface: concrete. It names the three README paths, the `docs/checked-documents.txt` entries and the link targets (`CLAUDE.md` *Tests*, the guide's *Shared test helpers* and, from answer 2, *The files*). From answers 1 and 2 I changed two things in the story: the last Interface bullet now says the tests route, names `test_the_root_holds_only_conftest_and_packages` and says the tester runs the guards to find every other such check; the guards link now reads `docs/project-guide/README.md`, *The files*. The Description and the criteria never said "docs route", so nothing else changed.
   - Criteria: each is testable. Criterion 1 is the guard `tests/guards/test_folder_readmes.py`, which covers both sides (the subfolder lines are present and true). Criterion 2 is the document check and the checked list. Criterion 3 is `make documents`. The criteria hold no rule with an untested failing side.
   - Smoke test: `uv run python -m factory.entry.check_documents | tail -1` is runnable, it calls no pytest, and its Expect line is checkable.
   - Docs criterion: it names the files and what the guide keeps unchanged, and dictates no sentences.
   - Architecture: the READMEs stand beside the test folders, with no code or layer change; this fits feature decisions 2, 4 and 6.
   - Scope: within the feature's S0003, and not in its Out of scope. The only test change is the human's leave for earlier guards.
7. factory: started tests as vm.
8. tester: Wrote the tests for the acceptance criteria and made the guard change that the human's leave allows (Interface; journal entry 4). The tests are red on purpose.

   Criterion → test:
   - criterion 1 (each README exists, its form and subfolder lines, guard skips none): `tests/guards/test_test_folder_readmes.py::test_a_test_folder_readme_is_written_so_its_guard_does_not_skip_it`, one row per README. The form itself is checked by the existing guard `tests/guards/test_folder_readmes.py::test_a_folder_readme_agrees_with_its_folder`. Its rows `tests/README.md`, `tests/support/README.md` and `tests/guards/README.md` are already in `FOLDER_READMES`, and the guard skips a row only when the file is missing, which the new test rules out.
   - criterion 2 (each file on `docs/checked-documents.txt`): `tests/guards/test_test_folder_readmes.py::test_a_test_folder_readme_is_on_the_checked_documents`, one row per README. No test of mine checks "the document check finds nothing". CLAUDE.md forbids tests that run the document check on the real documents, so that half is left to `make documents` (criterion 3).
   - criterion 3 (`make documents`), criterion 4 (`make check`), criterion 5 (docs): these are checks and the docs criterion, so they have no test.

   Earlier guard changed under the leave:
   - `tests/guards/test_tests_layout.py::test_the_root_holds_only_conftest_and_packages` now expects `["README.md", "conftest.py"]` in the root of `tests/`. I also rewrote the module docstring's first line so it still says what the file checks.

   How I found every such check: I put three stand-in READMEs at the three paths, ran all of `tests/guards`, then deleted them. The only failure was the test above. With them in place, `test_folder_readmes.py` passed all three rows without skipping. I also searched `tests/` outside `guards/` for tests that list the root of `tests/` or read `checked-documents.txt`, and found only `tests/support/guide_files_support.py` and `tests/guards/test_document_tests_write_their_documents.py`. Neither failed.

   Files: created `tests/guards/test_test_folder_readmes.py`; changed `tests/guards/test_tests_layout.py`.

   Run of the files I wrote or changed, plus the existing guard: 7 failures, all for the right reason. The READMEs are missing, they are not on `docs/checked-documents.txt`, and `test_the_root_holds_only_conftest_and_packages` fails because `README.md` is not in `tests/` yet. The test runner could import every module. `make lint` is green.

   Open for the next stages: the three READMEs and the `docs/checked-documents.txt` lines are inside the documenter's write paths, not the coder's. So the coder has no code to write, and these tests turn green only after the docs stage. The story should pass through doing with no code change.

   `lint`: lint: green (0.2 s)
9. factory: started doing as vm.
10. coder: I stopped before writing anything. Nothing in this story can be fixed from the coder's write paths, so the doing stage's gate (`make check`) can't go green and a `review` decision would just stall here.

    What I checked: I ran `uv run pytest -q tests/guards/test_test_folder_readmes.py tests/guards/test_tests_layout.py tests/guards/test_folder_readmes.py`. It gave 7 failures, the ones the tester expected:
    - `test_a_test_folder_readme_is_written_so_its_guard_does_not_skip_it`, rows `tests/README.md`, `tests/support/README.md`, `tests/guards/README.md`: the files are missing.
    - `test_a_test_folder_readme_is_on_the_checked_documents`, the same three rows: the paths are not in `docs/checked-documents.txt`.
    - `test_the_root_holds_only_conftest_and_packages`: it now expects `README.md` in `tests/`.

    To make them pass, someone has to write `tests/README.md`, `tests/support/README.md`, `tests/guards/README.md` and three lines in `docs/checked-documents.txt`. According to `factory/pipeline.yml`, the coder's write paths are `src/*`, `agents/*` and `operator/...`. None of these files are in them. They are all in the documenter's write paths, and the documenter runs only after review. The doing stage checks `make check`, so the red tests hold the work item at doing before docs ever runs. The tester's entry 8 already pointed out that the story should pass through doing with no code change, but the gate does not allow that.

    Options I see:
    (a) You commit the three READMEs and the three `docs/checked-documents.txt` lines on `work-item/F0055-S0003` yourself, and doing runs again with nothing to write. The docs stage then checks the wording.
    (b) You give the coder these four paths for this story, by changing `factory/pipeline.yml`. That is a pipeline file, so only you can change it. I would then write the READMEs from the code and docstrings.
    (c) You send the story back to the docs-only route (intake → docs-only → tests are its stages). The documenter writes the READMEs and the list first, and the tests turn green after them. Today the tests route puts the red tests in front of a stage that cannot satisfy them.

    I would choose (c): it is the route whose order matches the work, a documents-only change with a guard that follows it. (a) is the quickest if you'd rather not reroute.

    Noticed, not touched: the tester's changes in `tests/guards/test_test_folder_readmes.py` and `tests/guards/test_tests_layout.py` look right for the criteria. I made no change to the working tree.
11. 2026-11-07 human: (b). The human changed factory/pipeline.yml on main: for this story only, the coder may write tests/README.md, tests/support/README.md, tests/guards/README.md and docs/checked-documents.txt. Write the three READMEs from the code and docstrings in the form of style.md, *Folder READMEs* (and the Interface: tests/support/README.md and tests/guards/README.md are pointers to the guide's sections and list no modules), add the three lines to the checked list, and run make check and make documents before you end. The docs stage reviews the wording.
12. factory: started doing as vm.
13. coder: I wrote the three test-folder READMEs and added them to the checked list. This follows the human's answer (b) in journal entry 11, which lets the coder write these four paths for this story only. I changed no code and no test.

    What I built:
    - `tests/README.md`: the opening says the suite mirrors the package as `tests/<area>/<layer>/`, next to a few special folders. It links to `CLAUDE.md`, *Tests*. It has one line for each of the 13 direct subfolders: the six special folders and the seven area folders. I took each special folder's line from its `__init__.py` docstring.
    - `tests/support/README.md`: one sentence, taken from the folder's `__init__.py` docstring. It links to `docs/project-guide/README.md`, *Shared test helpers*. It lists no modules.
    - `tests/guards/README.md`: one sentence, from its `__init__.py` docstring and the guards folder's description in `CLAUDE.md` *Tests*. It links to `docs/project-guide/README.md`, *The files*. It lists no modules.
    - `docs/checked-documents.txt`: the three paths are added at the end.

    Checks:
    - `tests/guards/test_test_folder_readmes.py`, `tests/guards/test_tests_layout.py` and `tests/guards/test_folder_readmes.py` pass.
    - `test_folder_readmes.py` skips none of the three new READMEs. Its 11 skips are other folders' READMEs that are not written yet.
    - `make documents` ended with `documents ok (59.2 s)`.
    - `make check` ended with `check: green`.

    Main choice: in `tests/README.md` the seven area folders each get the same plain line ("the tests of the <area> area, one folder per layer"). I rejected repeating what each area holds, as `src/factory/README.md` does. That would duplicate the package README, and the form wants the detail kept in the guides.

    Refactor: nothing to change; the diff is four short documents.

    The docs stage reviews the wording, as the human said. I noticed nothing else and touched nothing else.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
14. factory: started review as vm.
15. reviewer: Review, round 0. Groups 1 to 4 are clean. Two document problems trace back to the human's answers and the docs criterion, and no stage can fix them without the human's word. That is why I'm asking instead of sending the story to doing.

    Findings:
    1. `tests/guards/README.md:3`: the README says "[The project guide], *The files*, says what the guards keep." That is false. *The files* in `docs/project-guide/README.md:31-57` describes the guide's own pages and names only one guard (`test_project_guide_files.py`). The guards are described under *Shared test helpers*: the `tests/guards/` bullet at `docs/project-guide/README.md:64` and the layout-guard paragraph at line 72. The link comes from the human's answer 2 (journal entry 4). That answer accepted intake's claim that the guards bullet sits under *The files* "(line 66)", but that bullet is in *Shared test helpers*, which starts at line 59. Fix: link *Shared test helpers*, the same target as `tests/support/README.md`, which needs the human to revise answer 2. Or keep *The files* and drop the claim that it says what the guards keep, but then the link explains nothing about the folder.
    2. Criterion 5 (the docs criterion), together with `docs/project-guide/README.md:61` and `:72`: the guide still says "The root of `tests/` holds `conftest.py` and folders". It also says `test_tests_layout.py` "fails when the root holds anything but `conftest.py` and packages". After this story both are false, because `tests/README.md` is in the root and the guard now expects `["README.md", "conftest.py"]` (`tests/guards/test_tests_layout.py:264`). Criterion 5 says the guide's list "unchanged", so the documenter will leave those two sentences stale. Fix: add to criterion 5 that those two sentences in the guide's *Shared test helpers* also name the root's `README.md`, with the module list itself unchanged. The same stale sentence is in `CLAUDE.md`, *Tests*: "the root of `tests/` holds only `conftest.py` and folders". `CLAUDE.md` is the human's file, so only the human can change it.

    Checked and clean:
    - Every criterion has its test. Criterion 1: `tests/guards/test_test_folder_readmes.py` plus the existing `test_folder_readmes.py`, whose `FOLDER_READMES` already holds the three rows (`src/factory/shared/domain/folder_readmes.py:33-35`). Criterion 2: the checked-list test. The journal records `make check` green after the coder.
    - Every subfolder line matches the tree: 13 entries in `tests/`; `tests/support/` and `tests/guards/` have no subfolders. Every area folder has `adapters/`, `application/` and `domain/`. The special-folder lines follow their `__init__.py` docstrings.
    - No code changes, no markers, and nothing for the architecture or security groups.

    Question for the human:
    (1) Which link should `tests/guards/README.md` carry? (a) *Shared test helpers* in `docs/project-guide/README.md`, where `tests/guards/` and its guards are actually described. (b) *The files*, as answered, with the sentence changed so that it no longer says the section describes the guards. I would choose (a).
    (2) May criterion 5 be extended so that the documenter updates the two sentences of *Shared test helpers* (`docs/project-guide/README.md:61` and `:72`) to name the root's `README.md`, leaving the list of modules and fixtures unchanged? I would choose yes. And will you change the matching sentence in `CLAUDE.md`, *Tests*, yourself?
    Once you answer, the coder (or the documenter, if you move the READMEs to it) can make the change, and I'd pass the rest.

    Earlier tests:
    - `tests/guards/test_tests_layout.py`: changed under the human's leave in the Interface and journal entry 4. `README.md` was added to the expected root files of `test_the_root_holds_only_conftest_and_packages`, and the module docstring was rewritten to match. The test keeps its name and purpose.
16. 2026-11-07 human: (1) (a): tests/guards/README.md links *Shared test helpers* in docs/project-guide/README.md, where the guards are described; the coder fixes the README in doing.
    (2) Yes: criterion 5 is extended. The documenter updates the two sentences of *Shared test helpers* (docs/project-guide/README.md, the root of tests/ and the layout guard) to name the root's README.md, and leaves the list of modules and fixtures unchanged. The human changed CLAUDE.md, *Tests*, on main: the root of tests/ holds only conftest.py, its README.md and folders.
17. factory: started review as vm.
18. reviewer: Review, round 0, run again after the human's answer (entry 16). I went through groups 1 to 6 and the documents item against the branch. Groups 1 to 4 are clean apart from the README link below. The other findings are about work item hygiene and come from answer 16 not being carried into the work item yet.

    Findings:
    1. `tests/guards/README.md:3`: the README links `docs/project-guide/README.md`, *The files*, and says that section "says what the guards keep". That is false: *The files* (`docs/project-guide/README.md:31-57`) describes the guide's own pages. The guards are described under *Shared test helpers*, in the `tests/guards/` bullet at line 66 and the layout-guard paragraph at line 72. The human's answer 16 (1)(a) settles it. Fix: link *Shared test helpers* in `docs/project-guide/README.md`, and keep the sentence true of that section.
    2. The work item's `## Interface`, the `tests/guards/README.md` sentence: it still says the README "links to `docs/project-guide/README.md`, *The files*", which answer 16 (1) overturned. Fix: the coder rewrites it to *Shared test helpers*, so that the Interface matches what is built.
    3. The work item's criterion 5 (the docs criterion): it was not extended as answer 16 (2) says. It still says only that the guide "keeps its list of shared test helpers unchanged". As written, the documenter will leave two sentences stale: `docs/project-guide/README.md:63` ("The root of `tests/` holds `conftest.py` and folders") and `:72` (`test_tests_layout.py` "fails when the root holds anything but `conftest.py` and packages"). Both are false now that `tests/README.md` is in the root and `tests/guards/test_tests_layout.py:264` expects `["README.md", "conftest.py"]`. Fix: the coder extends criterion 5 so that the documenter updates those two sentences of *Shared test helpers* to name the root's `README.md`, and leaves the list of modules and fixtures unchanged.

    Checked and clean:
    - Every criterion has its test, and the tests check what they are named after.
      - Criterion 1: `tests/guards/test_test_folder_readmes.py` (the file exists, so the guard cannot skip it), plus the existing `tests/guards/test_folder_readmes.py`, whose `FOLDER_READMES` already holds the three rows (`src/factory/shared/domain/folder_readmes.py:33-35`).
      - Criterion 2: the checked-list test.
      - Criteria 3 and 4: covered by `make documents` and `make check`. The coder's entry 13 records `check: green` and `documents ok`.
    - The Interface states no limit or rejected input that would need a test of its failing side.
    - `tests/README.md` names all 13 direct subfolders of `tests/` in the form the guard expects. The special-folder lines match their `__init__.py` docstrings, and the `CLAUDE.md`, *Tests* link exists.
    - `tests/support/README.md` makes one true sentence (taken from `tests/support/__init__.py`), links *Shared test helpers*, which exists, and lists no modules.
    - No code under `src/`, no markers, no secrets. Nothing for the architecture or security groups.

    Earlier tests:
    - `tests/guards/test_tests_layout.py` was changed under the human's leave (the Interface; journal entry 4). `README.md` was added to the expected root files of `test_the_root_holds_only_conftest_and_packages`, and the module docstring was adjusted to match. The test keeps its name and purpose.
19. factory: started doing as vm.
20. coder: Rework round 1. I fixed the reviewer's finding 1 from entry 18, following the human's answer 16 (1)(a).

    Changed: `tests/guards/README.md`. It now links `docs/project-guide/README.md`, *Shared test helpers*, instead of *The files*. The sentence now says only what that section holds: it names the guards in its `tests/guards/` bullet and says what the layout guard keeps in the paragraph on `test_tests_layout.py`. No other file changed. No code, no test.

    Findings 2 and 3 are not done, because I can't write the work item. In `factory/pipeline.yml` the coder's write paths do not include `{work_item}`, so any edit to its Interface or criteria would be dropped. Per stage step 5, here is what the journal changed in the task, for a stage that may write the work item:
    - Interface: answer 16 (1) moves the `tests/guards/README.md` link from *The files* to `docs/project-guide/README.md`, *Shared test helpers*. The built README now follows that.
    - Criterion 5: answer 16 (2) extends it. The documenter updates the two sentences of *Shared test helpers* in `docs/project-guide/README.md` so that both name the root's `README.md`, and leaves the list of modules and fixtures unchanged:
      - "The root of `tests/` holds `conftest.py` and folders"
      - the layout-guard sentence "fails when the root holds anything but `conftest.py` and packages"

      `CLAUDE.md` is already changed on `main` by the human.

    Main choice: I kept the README a one-sentence pointer and changed only its link and its claim. I rejected also citing the layout-guard paragraph's rules in the README, because the Interface says the README lists no modules and keeps the detail in the guide.

    Refactor: nothing to change, since the diff is one sentence.

    Checks:
    - `make documents`: `documents ok (59.1 s)`
    - `make check`: `check: green`

    Noticed, not touched: the two stale sentences in `docs/project-guide/README.md` (lines 63 and 72). They are the documenter's under the extended criterion 5, and outside my write paths.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
21. factory: started review as vm.
