---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 318
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T02:20:10.337180Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T02:20:10.343930Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T02:20:23.614905Z'
  stage: intake
  run: 25080d7385974d9f8c8adc16e0115f5d
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T02:20:44.341832Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T02:23:42.686193Z'
  stage: tests
  run: ea222def836f4daab836f908d105afdf
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T02:24:03.321034Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T02:25:53.629479Z'
  stage: doing
  run: 8eeec9d0b76848b48257dd3b12599725
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T02:26:14.246239Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T02:26:46.656664Z'
  stage: review
  run: c6530146e9d34d45af465f01dd3cac7f
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T02:27:07.589535Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T02:27:20.954414Z'
  stage: docs
  run: 3752fcd76d2640b2b65e22f9695fea86
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T02:27:41.167643Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T02:27:54.321361Z'
  stage: smoke-test
  run: 1e1567f13b6d49a5834b51939c92e26d
- number: 14
  speaker: factory
  kind: done
  at: '2026-10-20T02:29:12.914887Z'
  stage: approval
---

# The tests pin the expiry note's key at the crash cap and the stalls at their edges

## Description

The mutation sweeps of 2026-10-19 over `factory.application` (`planning/overnight/mutation-sweep-2026-10-19-part2.md`, story 7, and `-part3.md`, its addition to it) left seven live mutants in the recovery and the stalls, each a side that no test reaches. An expiry at the crash cap posts its note under the key of the *expiry* record (`recovery.py:124`). The last factory record is then the crash-cap question, and no test reads the note's number there. Two stalls carry no detail: the merge-conflict stall (`stage.py:452`, through `StallService.stall`'s default at `stalls.py:64`) and the stall when the agent left its branch (`stage.py:226`). No test pins their note or their entry, so a default detail would pass. When the agent commits on its work branch and then switches to another one, the stall must start the branch again at the stage-start commit (`stalls.py:103`). No test has such an agent, so a stall that kept the agent's commit would pass. A red check stalls with the stage-start commit, so the stall undoes what the check wrote outside the write paths (`stage.py:362`). No check in a test writes such a file. This story pins these as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003.

## Interface

No module under `src/factory/` changes. The behaviour pinned (`application`):

- `factory.application.recovery.RecoveryHandler.handle(event)` for an `expired` event: the expiry note's key is `PostKey(work_item=<id>, kind="expiry", n=<the expiry record's number>)`, also at the crash cap, where the crash-cap question follows under its own record's number.
- `factory.application.stalls.StallService.stall(context, reason, detail="")` with the stalls of `factory.application.stage.StageRunner.run`: a merge conflict and a run that left the work item's branch stall with no detail, so the note says only the reason's sentence and the entry ends with it.
- `StallService.stall` after a run that left the branch: the branch is checked out again at the stage-start commit, so a commit the agent made on it is not part of the stall.
- `factory.application.stage.StageFinisher.finish` at a red check: the stall undoes from the stage-start commit, a file the check wrote outside the write paths included.

Tests (the tester writes them):

- `tests/application/test_recovery_expiry_key.py` builds on `tests/crash_support.py` as it is: `expired_claim`, `open_pull_request`, `snapshot`, `expired_event`, `other_handler` and `Rerun`.
- `tests/application/test_stall_edges.py` builds on `tests/stage_run_support.py` as it is: `open_story`, `run_stage`, `completed`, `stage_makefile`, `BRANCH` and `PATH`. Its agent runtime that leaves the branch is a small class of its own around the `agent_runtime` fixture, as `CommittingRuntime` of `tests/application/test_stage_run.py` is one there. Before it plays the queued run, it always writes `tests/test_a.py` and commits it (`"the agent's commit"`) on the work branch, and it then checks out `elsewhere` at `HEAD`. So it is no copy of the two `SwitchingRuntime` classes: the one of `tests/application/test_after_agent.py` leaves without a commit, the one of `tests/application/test_stalls.py` commits on the other branch. The test runs the stage with `run_stage(replace(boundaries, agent_runtime=<it>))`.

A stall's *note* is the first line of the one factory post on `report.pull_request`. Its *entry* is the text (`entry_text`) of the last journal record of the work item at `report.commit`. No earlier test changes.

## Acceptance criteria

1. The expiry note's key (rows of one parametrized test; `number = open_pull_request(hosting)`, `expired_claim(boundaries, human, clock, crashes=<crashes>, pull_request=number)`, then `other_handler(boundaries, claimed, Rerun()).handle(expired_event(snapshot(boundaries)))`; the journal before is `1` human `created`, `2` factory `started`):
   - `crashes=1`, at the cap of 2: the keys of `hosting.factory_posts(number)` are exactly `[PostKey(work_item="F0001-S0001", kind="expiry", n="3"), PostKey(work_item="F0001-S0001", kind="crash_cap", n="4")]`.
   - `crashes=0`, below the cap: exactly `[PostKey(work_item="F0001-S0001", kind="expiry", n="3")]`.
2. The stalls without a detail (rows of one parametrized test; each gives the note and the entry):
   - A merge conflict: `open_story(boundaries, human, agent_home, main_files={"notes.md": "base\n"})`, then the human pushes `notes.md` as `branch\n` to `work-item/F0001-S0001` and as `main\n` to `main`, a fetch, `run_stage(boundaries)`: the note `Stalled (attempt 1 of 2): merging the main branch conflicts and the merge was aborted. Retrying on the next tick.`, the entry `Stage tests stalled (attempt 1 of 2): merging the main branch conflicts and the merge was aborted`.
   - A run that left the branch: `open_story(boundaries, human, agent_home)`, `ScriptedRun(result=completed())` queued, the runtime of the Interface: the note `Stalled (attempt 1 of 2): the agent left the work item's branch. Retrying on the next tick.`, the entry `Stage tests stalled (attempt 1 of 2): the agent left the work item's branch`.
3. A commit on the branch before the agent left it (one test; as the second row of criterion 2): `report.stall.reason` is `left_branch`; the subjects of `boundaries.git.log(report.commit, since="origin/main")` are exactly `["work item F0001-S0001: tests stalled", "work item F0001-S0001: tests starts as factory-1", "write factory/features/F0001-example/in-progress/F0001-S0001-first.md"]`, so the stall commit's parent is the stage-start commit; and `boundaries.git.show_file(report.commit, "tests/test_a.py")` is `None`.
4. What a red check wrote is undone (one test): `open_story(boundaries, human, agent_home, makefile=stage_makefile({"lint": 1}, extra=["@echo checked > written-by-lint.txt"]))`, `ScriptedRun(result=completed("doing"))` queued, `run_stage(boundaries)`: `report.rule` is `5` and `report.stall.reason` is `check_red`; `boundaries.git.show_file(report.commit, "written-by-lint.txt")` is `None`, and the file is not in the checkout.
5. `make check` stays green.
6. docs: none. The operator guide and `docs/project-guide/` already describe the expiry note, the stalls and the undo, and this story changes none of them.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.domain.post_texts import stall_note

print(stall_note("merge_conflict", 1, 2))
print(stall_note("left_branch", 1, 2))
EOF
```

Expect: two lines, `Stalled (attempt 1 of 2): merging the main branch conflicts and the merge was aborted. Retrying on the next tick.` and `Stalled (attempt 1 of 2): the agent left the work item's branch. Retrying on the next tick.`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no `src/` change. It names concrete behaviour on `RecoveryHandler.handle`, `StallService.stall` and `StageFinisher.finish`, with the `PostKey` fields, and it names the two test modules and the support helpers they build on. Each behaviour stated in it has a criterion.
   Criteria: each is testable by one test function. Criterion 1 has a row at the crash cap and a row below it. Criterion 2 has a row for each of the two detail-less stalls, with the exact note and entry texts. Criterion 3 covers the branch restart and the dropped agent commit. Criterion 4 covers the undo of a file the red check wrote. The rule "stall with no detail" is pinned on both sides: the cap and non-cap keys, and the stalls' exact texts.
   Smoke test: it is a runnable `stall_note` call. Its Expect line gives the two exact sentences, which can be checked against the output.
   Architecture: the story changes only tests, under `tests/application/` and mirroring the package layers. It reuses the shared support modules and adds no copy of a helper.
   Scope: it matches the feature's scope entry for S0007 and decisions 1, 8, 9 and 13. Nothing falls in the feature's "Out of scope".
4. factory: started tests as self.
5. tester: Wrote one test per criterion against the Interface. The new tests build on `tests/crash_support.py` and `tests/stage_run_support.py` and leave both unchanged. No earlier test file was changed.

   criterion 1: tests/application/test_recovery_expiry_key.py::test_the_expiry_note_is_keyed_by_the_expiry_record (rows `at-the-cap`, crashes=1 → expiry n=3 then crash_cap n=4; `below-the-cap`, crashes=0 → expiry n=3 only)
   criterion 2: tests/application/test_stall_edges.py::test_a_stall_without_a_detail_says_only_its_reason (rows `merge-conflict` and `left-branch`; each checks the first line of the one factory post and the `entry_text` of the last journal record at `report.commit`)
   criterion 3: tests/application/test_stall_edges.py::test_a_stall_after_the_agent_left_drops_its_commit_on_the_branch
   criterion 4: tests/application/test_stall_edges.py::test_a_red_check_stall_undoes_what_the_check_wrote
   criterion 5 (`make check`) and criterion 6 (docs: none): no test.

   The runtime that leaves the branch is `CommitThenLeaveRuntime` in test_stall_edges.py. It wraps the `agent_runtime` fixture the way `CommittingRuntime` does. It writes and commits `tests/test_a.py` ("the agent's commit") on the work branch, checks out `elsewhere` at `HEAD`, then plays the queued run. The setup for the left-branch case is one helper, `_left_branch`, used by both criterion 2's row and criterion 3.

   Files created: tests/application/test_recovery_expiry_key.py, tests/application/test_stall_edges.py.

   Modules the test run could not import: none. As the story says, no `src/` change is needed. All the new tests pass already, so the branch has no red tests this time: `make test` ended with `test: green (44.6 s)`. That was the run before I removed the unused `remote` fixture parameters and an unused `Path` import that lint flagged; there was no second run. `make lint` is green. I skipped the type check, as this stage says.

   Open: nothing. The coder has no code to write; their `make check` covers mypy over the new tests.

   `lint`: lint: green (0.0 s)
   `test`: test: green (39.9 s)
6. factory: started doing as self.
7. coder: I built nothing. The Interface says no module under `src/factory/` changes, and the tester's new tests already pass against the code as it stands: `tests/application/test_recovery_expiry_key.py` and `tests/application/test_stall_edges.py`. I ran `make check` in the foreground and it ended `check: green`. That run includes `mypy --strict` over the two new test modules, which the tester had skipped. `test: green (40.3 s)`, total coverage 99.14 %.

   Main choice: change no code. The one alternative was to touch `recovery.py`, `stage.py` or `stalls.py` to "strengthen" the pinned sides, and I rejected it. The story's purpose is to pin behaviour that already exists, and any change there is scope beyond the description (R13).

   Refactor: I have no diff of my own under `src/` (`git diff main -- . ':!factory'` shows only the tester's two files), so there was nothing to refactor. The journal did not change the meaning of the task, so the Description stays as it is.

   Noticed, not touched: the coverage report still lists uncovered lines in the modules this feature is about, `recovery.py` 126 and 200 and `stage.py` 467. They are outside this story's criteria.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I read: the work item and `git diff main...HEAD -- . ':!factory'`, which adds two test files and changes nothing under `src/`. I checked them against `tests/stage_run_support.py` (`_target`, `stage_makefile`, `open_story`), `CommittingRuntime` in `tests/application/test_stage_run.py`, and the two `SwitchingRuntime` classes in `test_after_agent.py` and `test_stalls.py`.

   1. Acceptance criteria: each criterion has one test, and each test checks what its criterion says.
      - Criterion 1 is one parametrized test in `tests/application/test_recovery_expiry_key.py:23`. The crash cap is tested on both sides: `crashes=1` (at the cap) expects the expiry key then the crash-cap key; `crashes=0` (below it) expects the expiry key alone.
      - Criterion 2 is one parametrized test in `tests/application/test_stall_edges.py:75`, with a merge-conflict row and a left-branch row. Each row requires exactly one factory post (`[post] = ...`) and checks its first line and the last journal record's `entry_text` at `report.commit`.
      - Criterion 3 (`test_stall_edges.py:118`) checks the stall reason, the three exact log subjects and that `tests/test_a.py` is gone.
      - Criterion 4 (`test_stall_edges.py:136`) cannot pass without the file having been written. `_target` puts the `extra` line ahead of `exit 1` in the `lint` recipe, and the test requires `check_red`, so lint ran its whole recipe. The test then checks that the file is in neither the commit nor the checkout.
      - The coder's `make check` was green (journal entry 7: `check: green`).
   2. Architecture: no `src/` change. The tests sit under `tests/application/`, mirroring the package layers.
   3. Security: no markers, no secrets, no command or query built from strings.
   4. Quality: `CommitThenLeaveRuntime` is the class the Interface asks for. It commits on the work branch before leaving, so it copies neither `SwitchingRuntime`. It wraps the `agent_runtime` fixture the way `CommittingRuntime` does. The test modules import their helpers from `crash_support` and `stage_run_support` unchanged.
   5. Work item hygiene: the Description matches what was built (tests only, as in F0025-S0003). Journal entry 7 gives the main choice (change no code) and what was rejected. The docs criterion "none" still holds.
   6. Earlier tests: `git diff --name-status main...HEAD` shows only `A` for test files, so no earlier test file was changed, renamed or deleted.
10. factory: started docs as self.
11. documenter: I changed no files. The docs criterion says `none`, and the diff (`git diff main...HEAD -- . ':!factory' ':!docs' ':!README.md'`) adds only `tests/application/test_recovery_expiry_key.py` and `tests/application/test_stall_edges.py`, with nothing under `src/`.

    Cross-read against that diff, all found current:
    - `docs/project-guide/watching.md` (steps 3 and 4b of recovery): it says the expiry note's key is `<id>:expiry:<the expiry entry's number>`. That matches criterion 1, including at the crash cap, where the crash-cap question follows under its own number.
    - `docs/operator-guide.md` (expiry, around lines 1453–1462; stall reasons, line 733): the expiry entry and the one-sentence stall causes match the pinned texts. Those are the merge-conflict and left-branch notes, which carry no detail.
    - `docs/project-guide/stages.md` (stall reasons, line 217; branch check, line 246): `left_branch` and `merge_conflict` match what the tests pin.
    - `docs/project-guide/git-and-hosting.md` (post key format, line 75): matches.

    I found no stale text. I did not run `make check`, because I changed no file. No finding for the coder: the code behaves as the Interface says.

    `check`: check: green (not run again: passed on tree c2e932948e4b at 2026-10-20T02:25:04Z)
    `secrets`: secrets: green (0.2 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test: no findings.

    I ran the one command under `## Smoke test` from the repository root, as written:

    ```
    Stalled (attempt 1 of 2): merging the main branch conflicts and the merge was aborted. Retrying on the next tick.
    Stalled (attempt 1 of 2): the agent left the work item's branch. Retrying on the next tick.
    ```

    Result: met its `Expect:` line. The output is two lines, and each matches the expected sentence exactly.

    Against the acceptance criteria: the two sentences are exactly the notes criterion 2 pins for the merge-conflict and left-branch stalls. Neither has a detail after the reason's sentence. No criterion is contradicted. The smoke test does not touch criteria 1, 3 and 4 (the expiry key, the branch restart and the red-check undo); their tests and the green `make check` are recorded in entries 5, 7 and 9. Criterion 6 (docs: none) still holds.

    Findings: none. Open: nothing.
14. factory: done (pull request merged); cost: 6 runs, 4.3 min, 37 turns, 127892 tokens in (714332 more from cache), 12538 out, $1.24
