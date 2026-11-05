---
stage: doing
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 565
comments_read: [6651800802, 6651897156]
handed_over: null
claim: null
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
