---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 550
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-04T23:02:09.900950Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T22:58:40.247838Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T22:58:40.254139Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-04T22:59:01.483096Z'
  stage: intake
  run: 907f752c013f4501b78137aeda2b10ba
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-04T22:59:06.321811Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-04T22:59:25.037512Z'
  stage: tests
  run: 53d5414a54bf49fe85887c54e8aa5bae
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-04T22:59:30.469348Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-04T23:02:02.283216Z'
  stage: doing
  run: 34721fe8dc604ed29ca416c50a5ed2cf
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-04T23:02:09.900950Z'
  stage: review
---

# The decision log and the contract's history match the feature

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

Two texts that F0050 left behind no longer say what the factory does. First, the decision log's S0005 entry, "A run's transcript is kept in the transcript folder" (`docs/decisions.md:1523`), says that "a `tmpfiles.d` rule on a VM and a lifecycle rule on a bucket" remove old transcripts (feature decision 10). Feature decision 11 then dropped the VM's rule, and `docs/operator-guide.md` (*Transcripts*, *On a VM*) says there is none. The log has no entry for decision 11, because S0007's docs criterion asked for none. Second, the records contract's version list in `docs/operator-guide.md` (*The records contract*, *The version*) goes from `4.0` straight to `4.2`. `4.1` came with F0049-S0002 (commit `4796912ee`) and added the stop reason `stage_image_failed` to the `reason` of `stop-record`. The F0050-S0002 documenter saw the gap and could not tell what `4.1` was. This story repairs both texts. It changes no code and no test.

## Interface

- No module under `src/factory/` changes, and no test is written: the criteria are about documents only. The document check of the docs stage (`make documents`) and `make check` are the gate.
- `docs/decisions.md`: a new entry for feature decision 11, in the log's form (Date, Decision, Why, and Rejected when the story names a rejected option). The S0005 entry's sentence about deletion gets a pointer to it. The log's history is not rewritten: the old sentence stays and says that S0007 replaced its VM half.
- `docs/operator-guide.md`: the version list names `4.1`.

## Acceptance criteria

1. `docs/decisions.md` has one entry whose Decision says that a VM keeps no retention of transcripts, with no `tmpfiles.d` rule and no option for an age, and that a Cloud Run bucket keeps its lifecycle rule. Its Why gives the human's reason of 2026-11-04 (about 5 MB per feature). It names F0050-S0007.
2. The S0005 entry's sentence on the `tmpfiles.d` rule is followed by a note that the VM's half was replaced, naming the new entry. No other sentence of that entry changes.
3. The version list of the records contract in `docs/operator-guide.md` has, between `4.0` and `4.2` and in the list's own wording, `` `4.1` added the stop reason `stage_image_failed` to the `reason` of `stop-record` ``.
4. `make check` stays green.
5. docs: as criteria 1 to 3, in `docs/decisions.md` and `docs/operator-guide.md`. `README.md` and the project guide: none.

## Smoke test

```bash
grep -c '`4\.1` added' docs/operator-guide.md
grep -c 'tmpfiles.d' docs/decisions.md | awk '{print ($1>=2)}'
grep -c 'F0050-S0007' docs/decisions.md | awk '{print ($1>=1)}'
```

Expect: `1`, then `1`, then `1` (on `main` before the story: `0`, `0`, `0`).

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: accepted. It names the two documents to change (`docs/decisions.md`, `docs/operator-guide.md`) and says that no module changes. The new entry takes the log's form (Date, Decision, Why).
   - Criteria: accepted. Each can be checked by reading the text. Criterion 1 covers both halves of decision 11, the VM without retention and the bucket with its lifecycle rule, plus the Why and the S0007 name. Criterion 2 fixes what changes in the S0005 entry, which is at `docs/decisions.md:1533` (the Description says 1523, so the line number is off by ten; the entry is unambiguous). Criterion 3 gives the exact wording. The story states no limits or validations, so none lacks a failing side.
   - Smoke test: accepted. The three greps are runnable. The records contract's version list in `docs/operator-guide.md` is one line, so the first count is 1. One inaccuracy in the `Expect:` line: `grep -c tmpfiles.d docs/decisions.md` gives 1 on this branch before the story, not 0, because the S0005 entry names it. After the story it is 3 or more (the S0005 entry, its note and the new entry), so `>=2` still gives `1`. Nothing to ask.
   - Architecture: accepted. Documents only, within the docs stage's paths. No layer is touched.
   - Scope: accepted. It matches feature decisions 10 and 11 and the A0001 proposal, and nothing is in `feature.md`'s out-of-scope list.
4. factory: started tests as vm.
5. tester: No tests written, as the Interface says: "no test is written: the criteria are about documents only". The gate is `make documents` in the docs stage and `make check`.
   - criterion 1 (an entry for decision 11 in `docs/decisions.md`): no test. It is a document criterion, checked by reading the text and by the smoke test's `tmpfiles.d` and `F0050-S0007` counts.
   - criterion 2 (the note after the S0005 entry's `tmpfiles.d` sentence): no test. Document criterion.
   - criterion 3 (`4.1` in the records contract's version list in `docs/operator-guide.md`): no test. Document criterion, checked by the smoke test's first grep.
   - criterion 4 (`make check` stays green): no test of its own. The factory's checks cover it.
   - criterion 5 (docs): no test. It belongs to the docs stage.
   Files created: none. Modules the test runner could not import: none, because no test was added and so there was no red run. `make lint` passed. Open: nothing. This story's only work is in the documents, within the docs stage's write paths.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Built nothing, and the working tree is unchanged. The Interface says no module under `src/factory/` changes and no test is written. All three criteria are about `docs/decisions.md` and `docs/operator-guide.md`, and `CLAUDE.md` (*Docs*) gives those files to the documenter: "the coder does not write them". With no failing tests and no code in scope, the coder has nothing to implement.

   - Main choice: leave the two documents to the docs stage. I rejected writing the new decision-log entry for decision 11, the note on the S0005 entry and the `4.1` line myself. That would go against the project's rule on who writes docs, and those files may be outside the coder's write paths, so the factory could drop the change.
   - Refactor: none, because the diff is empty.
   - `make check`: green (`test: green (119.5 s)`, `check: green`).
   - What the docs stage needs, from the work item and the intake entry: the S0005 entry is at `docs/decisions.md:1533`, not 1523. Before the story `grep -c tmpfiles.d docs/decisions.md` gives 1, not 0. The smoke test's `>=2` still holds after the edits.
   - The journal did not change the meaning of the task, so the Description was not rewritten.
   - Noticed but not touched: nothing.

   `check`: check: green (not run again: passed on tree a4a57514a13e at 2026-11-04T22:47:18Z)
   `duplicates`: duplicates: 4 new, 41 known, 2 gone
8. factory: started review as vm.
