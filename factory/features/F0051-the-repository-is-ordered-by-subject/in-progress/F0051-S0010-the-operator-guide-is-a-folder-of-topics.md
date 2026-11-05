---
stage: tests
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 565
comments_read: [6651800802]
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
