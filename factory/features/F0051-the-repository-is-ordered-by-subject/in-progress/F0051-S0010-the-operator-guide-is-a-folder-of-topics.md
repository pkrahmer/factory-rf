---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-05T06:49:04.576792Z'
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
3. `factory-check-documents` reports `docs/operator-guide/stops.md: section 'The stops' is missing` when that heading is removed from `stops.md`, `docs/operator-guide/install.md: missing` when `install.md` is removed, and nothing for the folder as it is (rows of one test).
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
