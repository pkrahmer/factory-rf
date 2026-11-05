---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 565
comments_read: [6651800802, 6651897156, 6652196970]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-05T07:43:39.954371Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T06:49:04.570227Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T06:49:04.576792Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-05T06:49:22.382886Z'
  stage: intake
  run: 4a5c3799a44145ca90bfa82be1e0e4b5
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-05T06:57:18.356041Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-05T06:57:20.814822Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-05T06:57:38.919760Z'
  stage: intake
  run: 56d20cce934141f0adb737575a12c6a7
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T06:57:44.212247Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-05T06:59:24.698367Z'
  stage: tests
  run: e86bea74133c461490e703ed05df3760
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-05T07:03:16.709541Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-05T07:03:19.222771Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-05T07:05:50.903677Z'
  stage: tests
  run: 4a251c9016d545e2ad3821568d71c2b3
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T07:05:56.373853Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-11-05T07:11:18.722219Z'
  stage: doing
  run: 1e707fe87f1a44c8ba3ec8ca8446b475
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-11-05T07:21:17.109662Z'
  stage: doing
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-05T07:21:19.630413Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-11-05T07:21:40.633718Z'
  stage: doing
  run: 0e7e549c226042e69cfd5fdcffbe3655
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-05T07:21:45.685085Z'
  stage: tests
- number: 18
  speaker: tester
  kind: result
  at: '2026-11-05T07:22:13.395308Z'
  stage: tests
  run: 7c8ce4a5aa6d4f9992e84fd9eb6ad88a
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-05T07:22:19.023780Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-11-05T07:27:33.413291Z'
  stage: doing
  run: 59e475635b0f4856813c3ce3aadf2e85
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-05T07:27:38.539714Z'
  stage: review
- number: 22
  speaker: reviewer
  kind: result
  at: '2026-11-05T07:30:33.172637Z'
  stage: review
  run: 2a98a7f58eb0488b9b0938b5fe0cb462
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-05T07:30:38.603397Z'
  stage: doing
- number: 24
  speaker: coder
  kind: result
  at: '2026-11-05T07:35:17.607744Z'
  stage: doing
  run: 06a0f60d328945bd8d756e3e2c2f2c5b
- number: 25
  speaker: factory
  kind: started
  at: '2026-11-05T07:35:22.942527Z'
  stage: tests
- number: 26
  speaker: tester
  kind: result
  at: '2026-11-05T07:36:34.505319Z'
  stage: tests
  run: b948896794e24710a5e6bd756adc567b
- number: 27
  speaker: factory
  kind: started
  at: '2026-11-05T07:36:40.098015Z'
  stage: doing
- number: 28
  speaker: coder
  kind: result
  at: '2026-11-05T07:37:26.742213Z'
  stage: doing
  run: 5f12694203d446fbbb2de734c25ff27d
- number: 29
  speaker: factory
  kind: started
  at: '2026-11-05T07:37:33.133613Z'
  stage: tests
- number: 30
  speaker: tester
  kind: result
  at: '2026-11-05T07:38:14.902333Z'
  stage: tests
  run: 4a9313bb09684dda865a7873e6313857
- number: 31
  speaker: factory
  kind: started
  at: '2026-11-05T07:38:20.515120Z'
  stage: doing
- number: 32
  speaker: coder
  kind: result
  at: '2026-11-05T07:43:34.619110Z'
  stage: doing
  run: c053a580c07247efae2582b69dc67fa4
- number: 33
  speaker: factory
  kind: started
  at: '2026-11-05T07:43:39.954371Z'
  stage: review
---

# The operator guide is a folder of topics

## Description

`docs/operator-guide.md` has 2,603 lines and 50 sections, from the install to the stops and the hand-over; an operator who looks for one topic scrolls through all of them, and every documenter run reads far more than it needs (F0051 candidates, item 42). This story turns it into a folder `docs/operator-guide/`, like the project guide: an index `README.md` and one file per topic. The topics are: `install.md` (*Install*, *Configuration*, *When the process refuses to start*, *The loop and its pauses*, *The project's make targets*), `agent-runtime.md` (*The agent runtime*, *The agent files*), `machine.md` (*The machine*), `site.md` (*The site file*, *Repeating a trial*, *Setting up an operator's machine*), `cloud-run.md` (*On Cloud Run*), `health.md` (*The preflight and the health check*, *The factory log and the health status file*, *Transcripts*), `stops.md` (*The stops* and every section from *What a stage run shows* to *The stops of the tick*, and *An event that keeps failing*, *Stops that cannot be done*), `pipeline.md` (*The pipeline definition*, *Checking a story before it starts*), `records.md` (*The records contract*, *What a work item cost: `factory-bill`*, *Looking at the remote: `factory-watch`*), and `work-items.md` (every section from *When a feature acceptance is due* to *A stage changed by hand*, and *A restart during a stage*, *An expired lease*, *Claims, leases and the clock*); *Replaced in v1.2* and *Replaced from v1* go to the index. Each section moves as it is; the words change only where a section points to another one. The document check follows: it requires the folder's index and its topic files, and it checks the sections it checks today (*Install*, *Configuration*, *The stops*) in their new files.

## Interface

- `factory.shared.domain.documents`: `OPERATOR_GUIDE` becomes the folder `docs/operator-guide` with its index `docs/operator-guide/README.md`, as `PROJECT_GUIDE_FOLDER` and `PROJECT_GUIDE` are today; the required sections are checked per file: *Install* and *Configuration* in `install.md`, *The stops* in `stops.md`. A missing topic file is reported as `docs/operator-guide/<file>: missing`, as a missing document is today.
- Every place under `src/`, `claude/`, `operator/`, `vm/` and `README.md` that names `docs/operator-guide.md` names the folder or its topic file instead.
- The tests that read the guide (`tests/test_operator_site_check.py` and the document check's tests) read the topic file that now holds their section; the leave of feature decision 5 covers it.
- `factory/story-form.md` names the four documents; its change to the folder is the human's, at this story's merge.

## Acceptance criteria

1. `docs/operator-guide.md` does not exist; `docs/operator-guide/` holds `README.md` and the ten topic files named in the Description.
2. Every section heading (`##` and `###`) of the guide before this story is found exactly once in the folder (one row per heading, from `origin/main` before the story).
3. `factory-check-documents` reports `docs/operator-guide/stops.md: section 'The stops' is missing` when that heading is removed from `stops.md`, `docs/operator-guide/install.md: section 'Install' is missing` and `docs/operator-guide/install.md: section 'Configuration' is missing` when those headings are removed from `install.md`, `docs/operator-guide/install.md: missing` when `install.md` is removed, `docs/operator-guide/README.md: missing` when the index is removed, and nothing for the folder as it is (rows of one test).
4. No file under `src/`, `claude/`, `operator/`, `vm/`, `docs/` or `README.md` names `docs/operator-guide.md`, except `docs/decisions.md`, which is history.
5. `make check` stays green.
6. docs: as criteria 1, 2 and 4; the index says in one sentence per file what it covers. `docs/project-guide/shared.md` (the document check): the new paths. `docs/decisions.md`: an entry for the split, naming F0051-S0010.

## Smoke test

```bash
ls docs/operator-guide | wc -l
```
Expect: `11`

```bash
test -e docs/operator-guide.md && echo still there || echo split
```
Expect: `split`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. Two questions, both about rules the Interface states whose failing side has no criterion:
   1. The Interface requires *Install* and *Configuration* in `install.md` and *The stops* in `stops.md`. Criterion 3 tests only the removal of *The stops* from `stops.md`. Should it also have rows for removing *Install* and *Configuration* from `install.md`, reported as `docs/operator-guide/install.md: section 'Install' is missing` and `docs/operator-guide/install.md: section 'Configuration' is missing`? I would add both rows to criterion 3.
   2. The Description says the document check "requires the folder's index and its topic files". Criterion 3 covers a missing topic file (`install.md`) but not a missing `docs/operator-guide/README.md`. Should it have a row reporting `docs/operator-guide/README.md: missing`? I would add that row.
   Other checks:
   - The Interface names concrete modules (`factory.shared.domain.documents`, `OPERATOR_GUIDE`).
   - The smoke tests are runnable.
   - The architecture and scope fit F0051 (S0010 is listed in `feature.md`).
4. 2026-11-05 human: Answers of the human:

   1. **Yes**, both rows in criterion 3, with those exact messages.
   2. **Yes**, the row `docs/operator-guide/README.md: missing` too.

   One note for the later stages: for the rest of F0051 the coder may write `docs/operator-guide.md`, `docs/operator-guide/*`, `docs/project-guide/*` and `README.md` (`factory/pipeline.yml`, the human, 2026-11-05), because this story's tests check documents in the check after `doing`. So the coder makes the split itself, and the documenter keeps the docs criterion's other parts.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: accepted. It names `factory.shared.domain.documents` and `OPERATOR_GUIDE`, the per-file required sections and the `docs/operator-guide/<file>: missing` message.
   - Criteria: accepted. Journal entry 4 (the human's answers) is carried into criterion 3 and nothing else changed. Criterion 3 now has these rows:
     - `install.md: section 'Install' is missing`
     - `install.md: section 'Configuration' is missing`
     - `install.md: missing`
     - `README.md: missing`
     - `stops.md: section 'The stops' is missing`
     - the clean folder reports nothing

     Each rule has its failing side, and each criterion is testable by one test function.
   - Smoke test: accepted. Both commands are runnable and both `Expect:` lines can be checked.
   - Architecture: accepted. The change is in documents plus `factory.shared.domain.documents`, which fits the shared area.
   - Scope: accepted. S0010 is listed in `feature.md`, and the leave of decision 5 and the human's note in entry 4 cover the test and coder write paths.
7. factory: started tests as vm.
8. tester: I've written tests for criteria 1–4. I stopped before changing the earlier document tests, because the Interface doesn't say what they should expect. Those tests have to change: once `OPERATOR_GUIDE` stops being `docs/operator-guide.md` they fail, and the coder may not edit them.

   Criterion → test so far:
   - criterion 1: tests/guards/test_operator_guide_files.py::test_the_single_guide_is_gone_and_the_folder_holds_the_index_and_ten_topics
   - criterion 2: tests/guards/test_operator_guide_files.py::test_every_earlier_heading_is_kept_in_the_folder (one row per heading, 128 rows, taken from `docs/operator-guide.md` as it is on this branch, which `origin/main` does not change)
   - criterion 3: tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file. It copies the repository's README.md, docs/decisions.md, docs/project-guide/ and docs/operator-guide/ into tmp_path. It has six rows: as-it-is, no-stops-section, no-install-section, no-configuration-section, no-install-file and no-index. Each row expects exactly the one line the criterion names.
   - criterion 4: tests/guards/test_operator_guide_files.py::test_no_file_names_the_single_guide

   Files created: tests/guards/test_operator_guide_files.py, tests/entry/test_check_documents_operator_guide.py. The test runner imported every module (`factory.entry.check_documents` exists). The tests fail because `docs/operator-guide/` does not exist yet: the criterion 3 rows error in the fixture's copytree, and the guard tests fail on the missing folder. `make lint` is green.

   Questions:
   1. Where does the stop-table row check (`stop '<id>' has no table row with its destination`) run now? I would put it in `stops.md`.
   2. Do the topic files and the index get the wording check (v1 words, replaced phrases), as the project guide's files do? I would check all eleven.
   3. When every document is missing, which lines appear and in what order? This sets `MISSING_LINES` in tests/support/check_documents_support.py. I would list README.md, docs/operator-guide/README.md, the ten topic files in the Description's order, then docs/project-guide/README.md and docs/decisions.md. Each line ends in `: missing`.
   4. What should the new constants be? Today tests/shared/domain/test_documents_guide_files.py::test_the_guide_is_an_index_in_its_folder pins `DOCUMENT_PATHS`. I would use `OPERATOR_GUIDE_FOLDER = "docs/operator-guide"`, `OPERATOR_GUIDE = "docs/operator-guide/README.md"` and `OPERATOR_GUIDE_FILES` (the ten topic paths). `DOCUMENT_PATHS` would hold all four documents with the topic files after the index, in the order of question 3.
   5. With those answers, I would adapt the earlier tests under the leave the Interface cites: tests/support/document_texts.py (`operator_guide` gives way to builders of the index and topic files, with the sections and stop rows in install.md and stops.md, and `write_documents`/`clean_texts` write them all), tests/support/check_documents_support.py, tests/entry/test_check_documents.py, tests/entry/test_check_documents_guide_files.py, tests/pipeline/domain/test_documents.py and tests/shared/domain/test_documents_guide_files.py. Every test would keep its name and what it checks. tests/operator_scripts/test_operator_site_check.py::test_the_guide_names_every_key_of_the_example_site_file would read `site.md`. Should I go ahead?
   6. Two places where I read the criteria, which you may want to correct:
      - Criterion 2 says "exactly once", but `### The steps` appears twice in the old guide. My test expects it as often as before, twice.
      - Criterion 4 searches `docs/`, but docs/runs/2026-11-04-f0050/log.md and docs/runs/2026-10-12-overnight/night-log.md name `docs/operator-guide.md`, and they are your files that no stage edits. My test leaves out `docs/runs/` as well as `docs/decisions.md`.
9. 2026-11-05 human: Answers of the human: all as you propose.

   1. The stop-table row check runs on `stops.md`.
   2. Yes, all eleven files get the wording check.
   3. The order you name: `README.md`, `docs/operator-guide/README.md`, the ten topic files in the Description's order, `docs/project-guide/README.md`, `docs/decisions.md`, each line ending in `: missing`.
   4. `OPERATOR_GUIDE_FOLDER = "docs/operator-guide"`, `OPERATOR_GUIDE = "docs/operator-guide/README.md"`, `OPERATOR_GUIDE_FILES` with the ten topic paths, and `DOCUMENT_PATHS` in the order of answer 3.
   5. Yes, go ahead with those test changes; this answer is the leave for them. Every test keeps its name and what it checks, and your entry names each file.
   6. Both readings are right: each heading as often as before (`### The steps` twice), and criterion 4 leaves out `docs/runs/` as well as `docs/decisions.md`.
10. factory: started tests as vm.
11. tester: I wrote the tests for criteria 1–4 and changed the earlier document tests under the leave in the human's answer (entry 9), following answers 1–6.

    Criterion → test:
    - criterion 1: tests/guards/test_operator_guide_files.py::test_the_single_guide_is_gone_and_the_folder_holds_the_index_and_ten_topics
    - criterion 2: tests/guards/test_operator_guide_files.py::test_every_earlier_heading_is_kept_in_the_folder. It has one row per heading of the old guide, with how often each appeared, so `### The steps` is expected twice (answer 6).
    - criterion 3: tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file. It has six rows: as-it-is, no-stops-section, no-install-section, no-configuration-section, no-install-file and no-index.
    - criterion 4: tests/guards/test_operator_guide_files.py::test_no_file_names_the_single_guide. It leaves out `docs/decisions.md` and `docs/runs/` (answer 6).

    Files created (in the earlier tests run, kept): tests/guards/test_operator_guide_files.py and tests/entry/test_check_documents_operator_guide.py. This run the guard file takes its `TOPIC_FILES` from the support module instead of its own copy.

    Earlier test files changed under the leave of entry 9. Every test keeps its name and what it checks:
    - tests/support/document_texts.py: `operator_guide` is gone. In its place are `operator_index`, `operator_install` (sections *Install* and *Configuration*), `operator_stops` (section *The stops* and the stop rows), `operator_topic` and `operator_file(path)`. The module also gains the constants `OPERATOR_INSTALL`, `OPERATOR_STOPS`, `INSTALL_SECTIONS` and `STOPS_SECTIONS`. `clean_texts` now gives all fourteen documents.
    - tests/support/check_documents_support.py: `MISSING_LINES` has the fourteen lines in the order of answer 3. A new `TOPIC_FILES` holds the ten topic names in the Description's order.
    - tests/pipeline/domain/test_documents.py:
      - The section rows check `install.md` and `stops.md`.
      - The stop-row tests check `stops.md` (answer 1).
      - `TEXT_GUIDES` covers the index and all ten topic files, so all eleven get the wording tests (answer 2).
      - The v1-word tests use the index.
      - The rule-order test now expects the findings of `install.md`, then `stops.md`, then the project guide.
      - test_the_operator_guide_sections_are_the_three_in_their_order is unchanged, so `OPERATOR_GUIDE_SECTIONS` stays `("Install", "Configuration", "The stops")`.
    - tests/shared/domain/test_documents_guide_files.py: test_the_guide_is_an_index_in_its_folder also pins `OPERATOR_GUIDE_FOLDER`, `OPERATOR_GUIDE` and `OPERATOR_GUIDE_FILES` (a tuple of the ten paths), and `DOCUMENT_PATHS` in the order of answer 3 (answer 4).
    - tests/entry/test_check_documents.py: test_each_finding_prints_one_line_in_order_and_returns_one expects `docs/operator-guide/install.md: section 'Install' is missing`.
    - tests/entry/test_check_documents_guide_files.py: `_old_path_texts` is the clean texts without the project guide's index, plus the old `docs/project-guide.md`.
    - tests/operator_scripts/test_operator_site_check.py: test_the_guide_names_every_key_of_the_example_site_file reads `docs/operator-guide/site.md`.

    Modules the test runner could not import: these four test modules fail at collection with an ImportError, because `factory.shared.domain.documents` has no `OPERATOR_GUIDE_FILES` or `OPERATOR_GUIDE_FOLDER` yet:
    - tests/entry/test_check_documents.py
    - tests/entry/test_check_documents_guide_files.py
    - tests/pipeline/domain/test_documents.py
    - tests/shared/domain/test_documents_guide_files.py

    The collection errors stopped pytest before the other three files ran: the two guard and criterion-3 test files, and the site check test. Those three fail because `docs/operator-guide/` does not exist yet.

    `make lint` is green. I skipped the type check, as this stage's instructions say.

    `lint`: lint: green (0.2 s)
12. factory: started doing as vm.
13. coder: I've done the split and the code change, but I had to stop before `make check` went green. Two tests still fail, and fixing either one needs your call: one is a test I may not change, the other needs files outside my write paths.

    What is in the working tree:
    - `src/factory/shared/domain/documents.py`:
      - New constants: `OPERATOR_GUIDE_FOLDER`, `OPERATOR_GUIDE` (the index), `OPERATOR_INSTALL`, `OPERATOR_STOPS` and `OPERATOR_GUIDE_FILES`. `DOCUMENT_PATHS` lists all fourteen documents in the agreed order.
      - The required sections are checked per file: *Install* and *Configuration* in `install.md`; *The stops* and the stop-table rows in `stops.md`. Every file gets the wording check. `OPERATOR_GUIDE_SECTIONS` stays as it was.
      - `_messages` now looks the rules up in a table (`_RULES`). The other choice was a growing `if` chain, and ruff refuses that at seven returns (PLR0911).
    - `src/factory/entry/check_documents.py`: docstring only. The topic files are in `DOCUMENT_PATHS`, so the command reads them with no further change.
    - `docs/operator-guide.md` is removed. `docs/operator-guide/` holds `README.md` and the ten topic files. A script (not kept) moved each section as it was, in the Description's split.
      - Each topic file has a new `#` title. I made the titles different from the section headings, so the required-section check cannot find them.
      - A quoted reference to a heading in another file now reads `"X" in [file.md](file.md)`. No other words changed.
      - The index has the old intro, one line per file, and *Replaced in v1.2* and *Replaced from v1*.
    - `README.md` and `docs/project-guide/{agents,machine,operator,pipeline}.md` name the topic files instead of the old path.
    - `factory-check-documents` reports `documents ok`. Lint, types, layers, sast, secrets and licenses are green. Coverage is 99.26 %.

    The two failing tests:

    1. `tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file` (an earlier story's test) fails 20 times. Its `REMOVED_FILES` holds the old project-guide name `work-items.md`. Its pattern matches that name anywhere under `docs/` after any character but a word character, `.` or `-`, so `/` and `(` count. The Description requires a topic file `docs/operator-guide/work-items.md`, so the index's own link fails it (first hit: `docs/operator-guide/README.md:16: work-items.md`), and so do the links between topics. Options:
       - (a) The tester changes that test: leave `docs/operator-guide/` out of its search, and do not count a name that follows `operator-guide/`.
       - (b) Rename the topic to `approvals.md`. That changes the Description, criterion 1, and `TOPIC_FILES` in `tests/support/check_documents_support.py`.
       - (c) Never write the name in full anywhere. The index then cannot say what that file covers.
       I would choose (a).

    2. `tests/guards/test_operator_guide_files.py::test_no_file_names_the_single_guide` fails on two lines that still name the old path:
       - `operator/README.md:37`
       - `docs/operator-playbook.md:3`
       Both are outside the coder's write paths: entry 4 adds only `docs/operator-guide*`, `docs/project-guide/*` and `README.md`. The playbook is also yours and no stage keeps it. Options:
       - (a) You edit the two lines on this branch. In `operator/README.md`, `docs/operator-guide.md` becomes `docs/operator-guide/site.md`. In the playbook, it becomes `docs/operator-guide/`.
       - (b) You add `operator/README.md` and `docs/operator-playbook.md` to the coder's write paths, and I make those edits.
       - (c) The test also leaves those two files out, and the documenter fixes `operator/README.md` later.
       I would choose (a). Either way, `make check` stays red after this stage until it is done.

    Not touched: some project-guide files refer to "the operator guide, *Section*" without a path, for example `docs/project-guide/machine.md:54` and `docs/project-guide/pipeline.md:116`. They are still correct; naming the topic file there belongs to the documenter's part of the docs criterion. No refactoring beyond the `_RULES` table was needed.
14. 2026-11-05 human: Answers of the human:

    1. **(a).** Leave for the tester: `tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file` leaves `docs/operator-guide/` out of its search and does not count a name that follows `operator-guide/`. The test keeps its name and still checks that no file names a removed project-guide file.
    2. **(a), on `main`.** I changed both lines on `main` (a pull of `main` at the next stage brings them in): `operator/README.md` names `docs/operator-guide/site.md`, and the playbook names `docs/operator-guide/` (an index and one file per topic). Do not edit them.

    End with `tests` for point 1. The documenter names the topic files in the project guide's "the operator guide, *Section*" references, as you suggest.
15. factory: started doing as vm.
16. coder: Following the human's answer (entry 14), I changed no code; one test needs a change. The split (`docs/operator-guide/`, 11 files) and the code change in `src/factory/shared/domain/documents.py` are already committed from the last doing run (b97f2bb71). The human's fix to `operator/README.md` and `docs/operator-playbook.md` on `main` is merged into this branch (4fc0116f5, b8e4f99a9). Neither file names `docs/operator-guide.md` any more, so `tests/guards/test_operator_guide_files.py::test_no_file_names_the_single_guide` should pass now.

    Test change for the tester, with the human's leave from entry 14 point 1: `tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file` should leave `docs/operator-guide/` out of its search, and should not count a removed name that follows `operator-guide/`. The test keeps its name and still checks that no file names a removed project-guide file.

    Still open: for the documenter, the project guide's "the operator guide, *Section*" references (for example `docs/project-guide/machine.md:54` and `docs/project-guide/pipeline.md:116`) should name the topic file. The human assigned this to the documenter in entry 14.
17. factory: started tests as vm.
18. tester: I made the test change the human approved in entry 14 point 1 and the coder named in entry 16. I edited `tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file` and nothing else.

    What changed:
    - `NOT_SEARCHED` now also holds `docs/operator-guide`, so the search leaves out the operator guide's folder.
    - The pattern has a second lookbehind, `(?<!operator-guide/)`. A removed project-guide name that comes right after `operator-guide/` no longer counts, so the link `docs/operator-guide/work-items.md` in other files passes.

    The test keeps its name and still checks that no searched file names a removed project-guide file. `REMOVED_FILES` and the other tests in the module are unchanged.

    Why: the Description requires a topic file `docs/operator-guide/work-items.md`. Its name matched the removed project-guide file `work-items.md`, so the guard failed 20 times on correct links.

    Run: `uv run pytest -q tests/guards/test_project_guide_files.py` passed, all 170 tests in the module. `make lint` is green.

    Files changed: tests/guards/test_project_guide_files.py. Created: none. Modules the test runner could not import: none.

    `lint`: lint: green (0.1 s)
19. factory: started doing as vm.
20. coder: In this run I changed nothing: the implementation was already committed, and the tester's change in entry 18 makes `make check` green (`check: green`, coverage 99.26 %). The working tree is clean.

    What was built in the earlier doing runs (b97f2bb71):
    - `src/factory/shared/domain/documents.py`:
      - New constants: `OPERATOR_GUIDE_FOLDER`, `OPERATOR_GUIDE` (the index), `OPERATOR_INSTALL`, `OPERATOR_STOPS` and `OPERATOR_GUIDE_FILES` (the ten topic paths).
      - `DOCUMENT_PATHS` holds the fourteen documents in the order of entry 9.
      - The required sections are checked per file: *Install* and *Configuration* in `install.md`; *The stops* and the stop-table rows in `stops.md` (`_stop_rows`, formerly `_operator_guide_rows`). Every file gets the wording check.
      - `OPERATOR_GUIDE_SECTIONS` stays `("Install", "Configuration", "The stops")`.
    - `src/factory/entry/check_documents.py`: docstring only.
    - `docs/operator-guide.md` is gone. `docs/operator-guide/` holds `README.md` and the ten topic files. Each section moved as it was; only references between sections changed.
    - `README.md` and `docs/project-guide/{agents,machine,operator,pipeline}.md` name the topic files.
    - The human's edits on `main` to `operator/README.md` and `docs/operator-playbook.md` are merged into this branch (4fc0116f5, b8e4f99a9).

    Main design decision: `_messages` picks each document's rules from a table (`_RULES`, path → message function; any other file gets the wording check alone). I rejected the longer `if` chain because ruff refuses it at seven returns (PLR0911), and the table keeps each file's rules in a function of its own.

    Refactor: I re-read the diff against `main` and found nothing to change.

    Description: the journal changed no meaning beyond what intake already carried into criterion 3. Entries 9 and 14 only settled the details (the order of the missing lines, the guard test's exclusion, the two lines the human changed on `main`). I did not rewrite the Description.

    Noticed, not touched: some project-guide files still say "the operator guide, *Section*" without naming the topic file (e.g. `docs/project-guide/machine.md:54`, `docs/project-guide/pipeline.md:116`). The human gave these to the documenter in entry 14.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 40 known, 3 gone
21. factory: started review as vm.
22. reviewer: Review of round 0. I read the work item, the diff against `main` and the topic files, and ran `make duplicates` to read its new findings. `make check` was green after the coder (entry 20).

    Findings:
    1. `docs/operator-guide/*.md`, italic references between files: the coder updated only the quoted references to sections that moved to another file (`"X" in [file.md](file.md)`). About 40 italic `*X*` references still point to a section in another topic file without naming that file. Examples: `cloud-run.md:7` (*The job profile*, *The metadata server in a job*, *Without ZFS*, *The idle shutdown* are now in `machine.md`), `machine.md:109` (*The preflight's items*, now in `health.md`), `site.md:201` (*A merge archives the story*, now in `work-items.md`), `install.md:32`/`43`/`49`/`54`, `agent-runtime.md:57`, `health.md:255`, `stops.md:51`. The Description says the words change where a section points to another one. Fix: give each such reference its file, in the form the quoted references already use.
    2. `docs/operator-guide/*.md`, quoted references to `####` sections that moved: these still point to a section in another file without naming it. `agent-runtime.md:65`, `:130` and `:148` ("The environment file", now in `machine.md`); `agent-runtime.md:150` ("The probe of the agent run", now in `health.md`); `pipeline.md:48` and `stops.md:86` ("The known results", now in `health.md`); `stops.md:58` ("The stop records", now in `health.md`). Fix: add `in [file.md](file.md)` as elsewhere.
    3. `docs/operator-guide/*.md`, "above" and "below": some of these now point into another file. `records.md:166` says "(see the table above)", but the environment table is in `install.md`. `pipeline.md:72` says "the stop `pipeline_definition_invalid`, described above", but that section is in `stops.md`. Fix: name the section and its file instead. Check the other "above" and "below" pointers in the topic files the same way.
    4. `src/factory/shared/domain/documents.py:43`, `OPERATOR_GUIDE_SECTIONS`: since the split, nothing in `src` uses it. `make duplicates` reports it as new dead code (`unused variable 'OPERATOR_GUIDE_SECTIONS'`). It is kept only because `tests/pipeline/domain/test_documents.py::test_the_operator_guide_sections_are_the_three_in_their_order` pins it. Fix: ask the human for leave to drop the constant and the earlier test that pins it, or make the per-file rules read their sections from it.
    5. `tests/guards/test_operator_guide_files.py`, `_lines_outside_fences` and `_searched_files`: both copy the helpers of the same names in `tests/guards/test_project_guide_files.py:201` and `:232`, and `_guide_headings` follows the same pattern. Fix: the tester moves the shared helpers into a `tests/support/*_support.py` module under the standing leave, and both guard files use them.
    6. `tests/support/document_texts.py:24-25`, `OPERATOR_INSTALL` and `OPERATOR_STOPS`: these are a second copy of the constants that `factory.shared.domain.documents` now exports under the same names. Fix: import them from there.
    7. Work item, criteria 2 and 4: they no longer say what the human settled in entry 9, answer 6. Criterion 2 still says "exactly once", but `### The steps` is expected twice, as often as before. Criterion 4 still names only `docs/decisions.md` as excluded, but `docs/runs/` is excluded too. The Interface also names `tests/test_operator_site_check.py`, which is `tests/operator_scripts/test_operator_site_check.py`. Fix: rewrite criteria 2 and 4 and that Interface path to match entry 9. The docs criterion 6 cites them ("as criteria 1, 2 and 4").

    Earlier tests (changed, status M):
    - `tests/entry/test_check_documents.py`: the human's leave, entry 9 answer 5.
    - `tests/entry/test_check_documents_guide_files.py`: the human's leave, entry 9 answer 5.
    - `tests/pipeline/domain/test_documents.py`: the human's leave, entry 9 answer 5.
    - `tests/shared/domain/test_documents_guide_files.py`: the human's leave, entry 9 answers 4 and 5.
    - `tests/support/check_documents_support.py`: the human's leave, entry 9 answers 3 and 5.
    - `tests/support/document_texts.py`: the human's leave, entry 9 answer 5.
    - `tests/operator_scripts/test_operator_site_check.py`: the human's leave, entry 9 answer 5 (it reads `site.md`).
    - `tests/guards/test_project_guide_files.py`: the human's leave, entry 14 point 1 (it leaves out `docs/operator-guide/` and has the `operator-guide/` lookbehind).

    Checked and found sound: criterion 1 has its test. Criterion 2 has one row per heading, counted. Criterion 3 has six rows of one parametrized test, as the human's answer asks. Criterion 4 searches `src/`, `claude/`, `operator/`, `vm/`, `docs/` and `README.md`. All eleven files get the wording check (`TEXT_GUIDES`), and the stop rows are checked in `stops.md`. The `_RULES` table is a clean replacement for the `if` chain. The architecture holds (domain layer, no I/O). No markers silence a check and no secrets were added. The other five new `make duplicates` findings are outside this diff.
23. factory: started doing as vm.
24. coder: Round 1: I fixed the reviewer's findings 1 to 4 (entry 22). Findings 5 and 6 are changes to tests, so I end with `tests`. Finding 7 is outside my write paths. `make check` is green (`check: green`, coverage 99.26 %), and `factory-check-documents` reports `documents ok`.

    Built:
    - Findings 1 and 2, `docs/operator-guide/{agent-runtime,cloud-run,health,install,machine,pipeline,site,stops}.md`: every italic `*X*` or quoted `"X"` reference to a heading that now lives in another topic file names that file, in the form the quoted references already use (`*X* in [file.md](file.md)`). That is 33 lines. Where a run of references in one sentence all point to the same file, the file is named once, after the last one (`cloud-run.md:7`, `:38`). The two `*The idle shutdown*` references in `install.md` already carried `under "The machine" in [machine.md](machine.md)` and are unchanged. `*The steps*` in `health.md:255` points to `machine.md`, because it means the `vm/setup.sh` steps. A script (not kept) found and fixed the references, and run again it finds no cross-file reference without its file. No other words changed.
    - Finding 3: I read every "above" and "below" in the topic files. Two pointed into another file and now name the section and its file:
      - `pipeline.md:72` now reads "described in "The stop `pipeline_definition_invalid`" in [stops.md](stops.md)".
      - `records.md:166` now reads "see the table of *Configuration* in [install.md](install.md)".
      The others point inside their own file.
    - Finding 4, `src/factory/shared/domain/documents.py`: `OPERATOR_GUIDE_SECTIONS` is now the one source of the required sections. A private map `_OPERATOR_SECTION_FILES` says which topic file holds each one, and `_operator_sections(document)` picks a file's sections from the tuple, in its order. `_INSTALL_SECTIONS` and `_STOPS_SECTIONS` are gone. I took the reviewer's second option rather than asking to drop the constant and its earlier test: the code change needs no leave, keeps `test_the_operator_guide_sections_are_the_three_in_their_order` meaningful, and should remove the vulture finding.

    For the tester:
    - Finding 5, under the standing leave in `CLAUDE.md`: move `_lines_outside_fences` and `_searched_files` (in both `tests/guards/test_operator_guide_files.py` and `tests/guards/test_project_guide_files.py:201`, `:232`) into one `tests/support/*_support.py` module, and change both guard files to use it. `_guide_headings` too, if it shares their pattern.
    - Finding 6: `tests/support/document_texts.py:24-25` should import `OPERATOR_INSTALL` and `OPERATOR_STOPS` from `factory.shared.domain.documents` and drop its own copies. `INSTALL_SECTIONS` and `STOPS_SECTIONS` there stay as they are: test data, now with no copy in `src`.

    Not done:
    - Finding 7 (criteria 2 and 4, and the Interface's `tests/test_operator_site_check.py` path): the work item is not in the coder's write paths, so I did not rewrite the Description. What the journal changed (entry 9, answer 6): criterion 2 means each heading appears as often as before (`### The steps` twice), criterion 4 also leaves out `docs/runs/`, and the site-check test is `tests/operator_scripts/test_operator_site_check.py`. A role that may write the work item, such as the reviewer, can carry this into the Description.

    Main decision: I added the file names with a script that reads the folder's headings, rather than by hand from the reviewer's examples. The examples were not a complete list ("about 40"), and the script covers every reference.

    Refactor: I re-read my diff and found nothing to change.

    Noticed, not touched: references in `docs/project-guide/` that say "the operator guide, *Section*" without the topic file. The human gave these to the documenter (entry 14).
25. factory: started tests as vm.
26. tester: I made the two test changes the coder named in entry 24, for the reviewer's findings 5 and 6 in entry 22. Both fall under the standing leave in `CLAUDE.md` for moving a shared test helper. No test was renamed, and every test checks the same thing as before.

    - Finding 5: I created `tests/support/guide_files_support.py` with three helpers:
      - `lines_outside_fences(text)`
      - `guide_headings(folder)`
      - `searched_files(searched, not_searched)`

      These were private copies in both guard modules. I removed the copies, and both modules now import the helpers from the new module.
      - `tests/guards/test_operator_guide_files.py`: changed; its unused `import re` is gone.
      - `tests/guards/test_project_guide_files.py`: changed (this module belongs to an earlier story; the change uses the standing leave).
      - One difference: the shared `searched_files` skips `__pycache__`, as the operator guard's copy did. The project guard's copy did not, but it searches `claude/`, `docs/` and `README.md`, which hold no `__pycache__` (checked with `find`). So it reads the same files as before.
    - Finding 6: `tests/support/document_texts.py` no longer defines its own `OPERATOR_INSTALL` and `OPERATOR_STOPS`. It imports them from `factory.shared.domain.documents`, and its now-unused import of `OPERATOR_GUIDE_FOLDER` is dropped. The tests that import these names through `support.document_texts` work as before. `INSTALL_SECTIONS` and `STOPS_SECTIONS` stay as test data, as entry 24 asked.

    Criterion → test mapping (unchanged by this run):
    - criterion 1: tests/guards/test_operator_guide_files.py::test_the_single_guide_is_gone_and_the_folder_holds_the_index_and_ten_topics
    - criterion 2: tests/guards/test_operator_guide_files.py::test_every_earlier_heading_is_kept_in_the_folder
    - criterion 4: tests/guards/test_operator_guide_files.py::test_no_file_names_the_single_guide
    - criterion 3: still covered by the parametrized document-check test written earlier (entries 9 and 22); this run did not touch it.

    Run: `uv run pytest -q` over the two guard modules, `tests/pipeline/domain/test_documents.py` and `tests/entry/test_check_documents.py` passed. `make lint` is green.

    Files created: `tests/support/guide_files_support.py`.
    Files changed: `tests/guards/test_operator_guide_files.py`, `tests/guards/test_project_guide_files.py` (earlier story's test, standing leave), `tests/support/document_texts.py`.
    Modules the test runner could not import: none.

    Still open: finding 7 (criteria 2 and 4 and the Interface's path of the site-check test) is a rewrite of the Description. That is outside the tester's write paths for this mode, so I left it.

    `lint`: lint: green (0.2 s)
27. factory: started doing as vm.
28. coder: Round 1, after the tester's entry 26: I changed no code this run. `make check` is red, and only because of a type error in the tests. The tester's fix for finding 6 caused it.

    `make types` (`mypy --strict`) fails 3 times:
    - `tests/pipeline/domain/test_documents.py:22: error: Module "support.document_texts" does not explicitly export attribute "OPERATOR_INSTALL"  [attr-defined]`
    - the same line for `OPERATOR_STOPS`
    - `tests/entry/test_check_documents.py:17` for `OPERATOR_INSTALL`

    `tests/support/document_texts.py` now imports these two constants from `factory.shared.domain.documents`. Under `--strict` a name that a module only imports is not re-exported, so the two test modules that still import them from `support.document_texts` fail.

    Test change for the tester (the fix for finding 6 under the standing leave, not finished yet): in `tests/pipeline/domain/test_documents.py` and `tests/entry/test_check_documents.py`, import `OPERATOR_INSTALL` and `OPERATOR_STOPS` from `factory.shared.domain.documents` instead of `support.document_texts`. The other choice is to re-export them in `document_texts.py` with `__all__` or `import X as X`. I'd take the direct import, since the support module shouldn't pass on names from `src`.

    Checked, all good:
    - `uv run pytest -q` over the two guard modules, `tests/pipeline/domain/test_documents.py`, `tests/entry/test_check_documents.py` and `tests/entry/test_check_documents_operator_guide.py` passes.
    - `make duplicates` now reports `5 new, 40 known, 3 gone`, down from 6 new. The dead-code finding for `OPERATOR_GUIDE_SECTIONS` (finding 4) is gone. The other five findings are outside this diff, as the reviewer noted.

    What I built (round 1, entry 24; unchanged this run): `src/factory/shared/domain/documents.py` takes its sections from `OPERATOR_GUIDE_SECTIONS` through `_OPERATOR_SECTION_FILES`. In `docs/operator-guide/*.md`, every reference to a section in another topic file now names that file.

    Still open:
    - Finding 7: rewrite criteria 2 and 4 and the Interface's path `tests/operator_scripts/test_operator_site_check.py` to match entry 9, answer 6. I can't write the work item.
    - For the documenter: the "the operator guide, *Section*" references in the project guide (entry 14).
29. factory: started tests as vm.
30. tester: I made the test change the coder named in entry 28. It finishes the fix for finding 6 under the standing leave for moving a shared test helper. No test was renamed, and every test checks the same thing as before.

    - `tests/pipeline/domain/test_documents.py`: `OPERATOR_INSTALL` and `OPERATOR_STOPS` are now imported from `factory.shared.domain.documents` instead of `support.document_texts`.
    - `tests/entry/test_check_documents.py`: `OPERATOR_INSTALL` is now imported from `factory.shared.domain.documents` instead of `support.document_texts`.

    This is the coder's preferred option: a direct import. I rejected re-exporting the names from `document_texts.py`, because the support module should not pass on names from `src`.

    Criterion → test mapping (unchanged by this run):
    - criterion 1: tests/guards/test_operator_guide_files.py::test_the_single_guide_is_gone_and_the_folder_holds_the_index_and_ten_topics
    - criterion 2: tests/guards/test_operator_guide_files.py::test_every_earlier_heading_is_kept_in_the_folder
    - criterion 3: the parametrized document-check test written earlier (entries 9 and 22); not touched this run.
    - criterion 4: tests/guards/test_operator_guide_files.py::test_no_file_names_the_single_guide

    Checks:
    - `uv run pytest -q` over the two changed modules passed.
    - `mypy` over them reports no more `attr-defined` errors. It was run without the project's configuration, so it is not `make types`; the coder's `make check` covers that.
    - `make lint` is green.

    Files created: none. Files changed: `tests/pipeline/domain/test_documents.py` and `tests/entry/test_check_documents.py` (earlier tests, under the standing leave). Modules the test runner could not import: none.

    Still open: finding 7, a rewrite of the Description, is outside my write paths.

    `lint`: lint: green (0.2 s)
31. factory: started doing as vm.
32. coder: Round 1, after the tester's entry 30: I changed no code in this run. The working tree is clean and `make check` is green (`check: green`, coverage 99.26 %). The tester's direct imports in `tests/pipeline/domain/test_documents.py` and `tests/entry/test_check_documents.py` fixed the three `attr-defined` errors from `mypy --strict` that I reported in entry 28.

    Round 1 now covers the reviewer's findings from entry 22:
    - Findings 1 to 3, `docs/operator-guide/*.md` (entry 24): every italic or quoted reference to a section that is now in another topic file names that file. The two "above" pointers that led into another file, `pipeline.md:72` and `records.md:166`, now name the section and its file.
    - Finding 4, `src/factory/shared/domain/documents.py` (entry 24): `OPERATOR_GUIDE_SECTIONS` is the one source of the required sections. A private map, `_OPERATOR_SECTION_FILES`, says which topic file holds each one. `make duplicates` no longer reports the dead constant. I rejected asking for leave to drop the constant and the test that pins it, because the code change needs no leave.
    - Findings 5 and 6, tests (entries 26 and 30): the tester moved the shared guard helpers to `tests/support/guide_files_support.py`. The tests now import the operator-guide constants from `factory.shared.domain.documents`.

    Refactor: I made no edits in this run, so there was nothing new to refactor. My earlier diff is unchanged.

    Description: no rewrite, because the work item is outside my write paths. Finding 7 is still open, and the meaning the journal settled (entry 9, answer 6) is this:
    - Criterion 2 means each heading appears as often as before (`### The steps` twice).
    - Criterion 4 also leaves out `docs/runs/`.
    - The site-check test is `tests/operator_scripts/test_operator_site_check.py`.
    A role that may write the work item can carry this into the Description.

    Noticed, not touched:
    - Some project-guide files still say "the operator guide, *Section*" without naming the topic file (for example `docs/project-guide/machine.md:54` and `docs/project-guide/pipeline.md:116`). The human gave these to the documenter in entry 14.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
33. factory: started review as vm.
