---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 636
comments_read: [6707209251]
handed_over: null
claim: null
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
