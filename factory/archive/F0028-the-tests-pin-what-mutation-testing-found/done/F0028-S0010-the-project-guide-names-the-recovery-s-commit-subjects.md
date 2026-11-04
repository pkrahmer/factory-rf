---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 332
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T04:18:12.127079Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T04:18:12.133154Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T04:18:29.733054Z'
  stage: intake
  run: ffaefd7fa74f45e59426acb92cf1ee9f
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T04:18:50.209103Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T04:19:44.646398Z'
  stage: tests
  run: 15c1ed54eecc482c8e3d856096aa90c1
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T04:20:05.123454Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T04:21:11.433893Z'
  stage: doing
  run: 5c1f6aa0bef042bbb6f6eb4bffcb9a52
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T04:21:31.858957Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T04:21:45.655458Z'
  stage: review
  run: 289e7ee2ba8a4cf0bc4a0d90eb7b393f
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T04:22:05.939226Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T04:22:21.894649Z'
  stage: docs
  run: e38ae522cc1340d18e9c72938915b141
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T04:22:42.323561Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T04:22:59.633518Z'
  stage: smoke-test
  run: 5fa75530864f4bffa7af58a5bcd5bc01
- number: 14
  speaker: factory
  kind: done
  at: '2026-10-20T04:25:23.000362Z'
  stage: approval
---

# The project guide names the recovery's commit subjects

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0028-S0006 pinned the subjects of a story's recovery commits in tests: `RecoveryHandler.handle` commits a crash as `work item <id>: crash of stage <stage> recorded` and an expiry as `work item <id>: expiry of stage <stage> recorded` (`src/factory/application/recovery.py:102`). Its documenter noticed that no document names these two subjects. `docs/project-guide/watching.md`, *A crash is discarded and the stage is rerun*, step 4, says only that the recorder "makes one commit on top of the remote's head", while the same file names the subject of every other handler commit (`close recorded`, `sent back`, `handed over at <stage>`, `comments from the pull request`, `merged, archived`, the move-back, and `pull request opened` for the draft step 4b and `ask_crash_cap` make). This story is for the agent who reads the guide before changing `recovery.py`, or who reads a branch's log after a crash. It adds the two subjects to step 4. The code, the tests and the other documents stay as they are. It changes no behaviour, so it has no criterion of its own beyond the two closing ones.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The reference the documenter checks against is `src/factory/application/recovery.py:100-104` (the entry kind and the subject) and `tests/application/test_recovery_subjects.py`, which pins them.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/project-guide/watching.md`, *A crash is discarded and the stage is rerun*, step 4: the commit's subject is `work item <id>: crash of stage <stage> recorded` for a `crash` and `work item <id>: expiry of stage <stage> recorded` for an `expired`, where `<stage>` is the stage the work item was in. Step 4b stays as it is; the subject of its draft's commit, `pull request opened`, stays named once, in the `ask_crash_cap` bullet of *The crash cap asks the human*. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, because they describe what an operator sees and decides, and no subject or behaviour changes.

## Smoke test

```bash
g=docs/project-guide/watching.md
for s in 'crash of stage <stage> recorded' 'expiry of stage <stage> recorded' 'pull request opened'; do grep -qF -e "$s" "$g" && echo found || echo "missing: $s"; done
```
Expect: three lines `found` (both recovery subjects and the draft's subject are in the guide)

```bash
uv run -q python - <<'EOF'
from factory.application.handlers.recording import commit_subject
print(commit_subject("F0001-S0001", "crash of stage doing recorded"))
EOF
```
Expect: `work item F0001-S0001: crash of stage doing recorded` (the form the guide now gives)

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no module under `src/factory/` changes and no test module is written. The reference lines are right: `recovery.py:100-104` builds the subject as `commit_subject(id, f"{entry_kind} of stage {stage} recorded")`, and `commit_subject` in `handlers/recording.py:47` gives `work item <id>: <text>`. `tests/application/test_recovery_subjects.py` exists.
   Criteria: criterion 2, the docs criterion, names the file, the section, step 4 and both subjects, one for a crash and one for an expiry. It also says step 4b stays and the other documents get `none`. A reviewer can check it by reading the guide. Criterion 1 is `make check`. The story states no Interface rule with a failing side, so none is missing a criterion.
   Smoke test: both blocks are runnable. The grep loop is a plain shell loop. The Python block calls `commit_subject`, which exists with that signature. Each `Expect:` line is checkable against the output. Before the documenter's edit, the grep for the two recovery subjects will print `missing:` lines, as expected for a docs story.
   Architecture: this is a documentation change in `docs/project-guide/`, which the documenter keeps. No layer is touched.
   Scope: it is within F0028's goal, which pins what the recovery commits. The feature's "Out of scope" lists "The documents" only for the stories that add tests. This story is the documenter's follow-up proposed by feature acceptance, and its change is limited to the two subjects in step 4.
   Open: none.
4. factory: started tests as self.
5. tester: No test written. The Interface says no module under `src/factory/` changes and the tester writes no test module, and neither criterion describes behaviour a test could check:
   criterion 1 (`make check` stays green): the factory's own check covers it; no test function.
   criterion 2 (docs: `docs/project-guide/watching.md`, step 4, names the two recovery subjects): the documenter does this and the reviewer checks it by reading the guide; no test function. `tests/application/test_recovery_subjects.py` (from F0028-S0006) already pins the subjects in code. I did not change it.
   Files created: none. Modules the test run could not import: none, because no new test refers to code that is missing.
   I did not run `make test`. With no new tests there are none that should fail, so there was no red run to confirm. `make lint`: green.
   Open: none.

   `lint`: lint: green (0.0 s)
   `test`: test: green (40.6 s)
6. factory: started doing as self.
7. coder: Built nothing: no files changed. The Interface says no module under `src/factory/` changes, and the tester wrote no test. The one real change is criterion 2: naming the two recovery subjects in `docs/project-guide/watching.md`, step 4. That is the documenter's job; per `CLAUDE.md` the coder does not write the project guide.
   Main choice: hand forward an empty diff. The alternative I rejected was editing `watching.md` myself, which would cross into the docs stage's files.
   Refactor: no diff, so nothing to change.
   `make check`: green (`check: green`, total coverage 99.14 %).
   Noticed but did not touch: nothing. The journal did not change the meaning of the task, so `## Description` stays as it is.

   `check`: check: green (not run again: passed on tree 450879e8d6a9 at 2026-10-20T04:13:05Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   The scope (`git diff main...HEAD -- . ':!factory'`) is empty. The only changes on the branch are the work item and its `.costs.jsonl` sidecar, both under `factory/`. That is what the story asks for: the Interface says no module under `src/factory/` changes and no test module is written. Criterion 2, the docs criterion, is the documenter's job, so the guide edit was not expected before this stage.
   1. Acceptance criteria: criterion 1 holds. The journal shows `check: green` after the coder (entry 7, total coverage 99.14 %). Criterion 2 has no test because it is a docs criterion, as the tester explained in entry 5. The Interface states no rule with a failing side and no limit, so no test is missing.
   2. to 4. Architecture, security, quality: no code changed, so there is nothing to judge. The `duplicates: 5 new` record in entry 7 cannot come from this branch because it changes nothing under `src/factory`.
   5. Work item hygiene: the coder's entry explains the empty diff and the rejected alternative, which was editing `watching.md` in the doing stage. The Description and criterion 2 still describe what the documenter must write in `docs/project-guide/watching.md` step 4: both recovery subjects, with step 4b and the `pull request opened` bullet left as they are, and `none` for `README.md`, `docs/operator-guide.md` and `docs/decisions.md`.
   6. Earlier tests: the branch changes, renames or deletes no test file on `main` (`git diff --name-status main...HEAD` lists only the work item `M` and its sidecar `A`).
10. factory: started docs as self.
11. documenter: Files changed: `docs/project-guide/watching.md`, in *A crash is discarded and the stage is rerun*, step 4. It now names the commit subject: `work item <id>: crash of stage <stage> recorded` for a `crash` and `work item <id>: expiry of stage <stage> recorded` for an `expired`, with `<stage>` the stage the work item was in. I checked this against `src/factory/application/recovery.py:100-104` (entry kind `crash` or `expiry`, then `commit_subject`). Step 4b and the `pull request opened` bullet in *The crash cap asks the human* are untouched, as the criterion says.

    Ran the story's smoke test. The grep loop printed `found` three times. The `commit_subject` block printed `work item F0001-S0001: crash of stage doing recorded`.

    Cross-read and found current against the diff, which is empty under `src/` and `tests/`: `README.md`, `docs/operator-guide.md`, `docs/decisions.md`, the rest of `docs/project-guide/watching.md`. These are `none` by the docs criterion, since no behaviour or subject changed.

    No findings. I did not run `make check`, because I changed only a document and the factory runs the checks after this stage. Stale text noticed but not touched: none.

    `check`: check: green (not run again: passed on tree 450879e8d6a9 at 2026-10-20T04:13:05Z)
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Ran both smoke-test commands from the repository root, exactly as written and in order. Both met their `Expect:` lines.

    Command 1 (the grep loop over `docs/project-guide/watching.md`):
    ```
    found
    found
    found
    ```
    Expect: three lines `found`. Met.

    Command 2 (`commit_subject` through `uv run`):
    ```
    work item F0001-S0001: crash of stage doing recorded
    ```
    Expect: `work item F0001-S0001: crash of stage doing recorded`. Met.

    I also checked the output against the acceptance criteria. Criterion 2: `watching.md:103` (step 4) now names both subjects, `work item <id>: crash of stage <stage> recorded` for a `crash` and `work item <id>: expiry of stage <stage> recorded` for an `expired`, where `<stage>` is the stage the work item was in. `pull request opened` still appears once, at `watching.md:113`, in the `ask_crash_cap` bullet. `git diff --stat main...HEAD` shows that `watching.md` is the only document changed, and only one line of it (`2 +-`), so step 4b and `README.md`, `docs/operator-guide.md` and `docs/decisions.md` are unchanged. Criterion 1: the smoke test does not contradict it; the factory's check of the tree is green (entries 7 and 11).

    Findings: none.

    Open: none.
14. factory: done (pull request merged); cost: 6 runs, 2.1 min, 26 turns, 87322 tokens in (315347 more from cache), 5411 out, $0.69
