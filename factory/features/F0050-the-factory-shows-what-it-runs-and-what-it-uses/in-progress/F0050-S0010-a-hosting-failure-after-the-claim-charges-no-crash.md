---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 549
comments_read: [6643408151, 6643585034, 6643890182]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T21:56:50.185730Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T21:56:50.192301Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T21:57:10.037322Z'
  stage: intake
  run: 32abf90ff2724cedbb593ab7eecdc288
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T22:11:21.367898Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T22:11:24.090173Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T22:11:46.907895Z'
  stage: intake
  run: ffb77967dc0f40678f226b34a301f5c7
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T22:11:52.197603Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-04T22:13:02.667120Z'
  stage: tests
  run: 35246e0f8d6b43069a51aeea2cb645d1
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-04T22:20:58.710602Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T22:21:01.558602Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-04T22:24:16.238274Z'
  stage: tests
  run: a159d51aedaa46dcbc251518bdcc2050
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-04T22:24:21.490642Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-11-04T22:27:36.343131Z'
  stage: doing
  run: 18f2971367394c71bbe64aa49dba799d
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-11-04T22:35:32.680478Z'
  stage: doing
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-04T22:35:35.256933Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-11-04T22:35:51.611055Z'
  stage: doing
  run: 43577dfabd084e04946e1516b7e0bd3c
---

# A hosting failure after the claim charges no crash

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

S0008 pinned what happens when the hosting service fails right after a stage's claim was pushed. `StageRunner._start` (`src/factory/application/stage.py:158-175`) pushes the claim, then calls `Opening.ensure_pull_request`. When the hosting service fails there, no agent has run. But the claim stands, and the next tick reads the claim without a result as a crash: it records `factory: crash` and counts it. `tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick` holds this as `xfail(strict=True, reason="a crash is charged for a stage in which no agent ran")`. During an outage like that of 2026-11-04, two such ticks reach the crash cap of a work item whose agent never ran, and the human must write a comment to wake it. This story makes that failure cost nothing. The stage that meets a hosting error after its claim and before its agent run releases its claim, so the next tick starts the stage afresh, with no crash. The handler's error count and its cap of three stay as they are. **The human chose (a)** (journal 4): on `HostingServiceError` from `ensure_pull_request`, the stage clears its claim (`Claims.release`), commits `<id>: claim released: hosting failed` and pushes it through `push_with_retries`, then raises the error as today. If that push also fails, today's crash stands. A pull request before the claim was rejected: it would open a race between two instances.

## Interface

- `factory.application.stage` (application), `StageRunner._start`: a `HostingServiceError` raised by `ensure_pull_request` after the claim was pushed releases the claim on the work item's branch (one commit, pushed through `push_with_retries`), then raises the same error unchanged.
- The release commit's subject is `commit_subject(<id>, "claim released: hosting failed")`. Its journal gets no `crash` entry and no new entry of its own; the crash count, attempts and round do not change.
- A release whose push fails (`PushFailed` after the retries) leaves the claim standing, as today, and raises the original `HostingServiceError`; the next tick then records the crash as today.
- Any other error after the claim (not `HostingServiceError`) is handled as today.
- Tests: the mark `xfail(strict=True, ...)` comes off `tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick`, and the test stays as it is otherwise. That test is S0008's, so this needs the human's leave in `feature.md`. New tests go into `tests/application/test_hosting_failure_releases_claim.py`.

## Acceptance criteria

1. A tick whose stage meets a hosting failure in `ensure_pull_request` after the claim was pushed leaves the branch with no claim, and the agent runtime has no call. At the next tick, with the hosting service back, the journal has no `crash` entry, the crash count is 0, and the stage starts and runs its agent.
2. When the release's push is refused four times (the retries spent), the claim stands, and the next tick records a crash, as today. Rows: the release pushed on the first try, the release pushed after two refusals, the release refused four times.
3. The handler error of the failed tick is counted and logged as S0008 built it (`handler error <event key> 1 of 3: HostingServiceError: ...`). The cap of three is unchanged: three failing ticks in a row reach it.
4. An error other than `HostingServiceError` after the claim (for example `WorkItemFormatError` for a body with no title line) releases nothing and is handled as today.
5. S0008's test `test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick` passes without its `xfail` mark.
6. The `HostingServiceError` reaches the caller as the same exception object, not wrapped. Rows: the release push succeeds; the release push fails (criterion 2's case).
7. The release is one commit with the subject `commit_subject(<id>, "claim released: hosting failed")`; the journal has no new entry, and attempts and round are unchanged.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`, in the section on stops and errors where S0008 described a hosting outage: a hosting failure right after a claim releases the claim, so it charges no crash. `docs/decisions.md`: one entry with the reason (a crash was charged for a stage in which no agent ran, found by S0008's test) and the approach the human chose. `README.md` and the project guide: none.

## Smoke test

```bash
grep -c 'xfail' tests/application/test_hosting_failure_after_claim.py
uv run pytest tests/application -k "hosting_failure" 2>&1 | tail -1
```

Expect: `0`, then a line that ends in `passed` with no `failed` and no `xfailed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: The format check passed. The story cannot move on until these are answered:

   1. **The approach is not chosen.** `## Description` still says "To refine: the human picks the approach" and gives two options. (a) Release the claim on `HostingServiceError`. (b) Open the pull request before the claim. The criteria and the Interface are written for (a) only. Options: (a) as written, or (b), which needs a new Interface and new criteria and a reading of the race between two instances. I would choose (a), as the acceptance proposed. Please confirm it, so that the Description loses its "To refine" paragraph and says the choice is made.

   2. **The human's leave is missing.** The Interface and criterion 5 take the `xfail(strict=True)` mark off S0008's test `tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick`. The Interface itself says this "needs the human's leave in `feature.md`". `feature.md`'s "The human's changes" and its decisions 1 to 11 hold no leave for S0010. A story that changes another story's test needs the human's word. Please give the leave. It should say that S0010's tester may remove only that mark and change nothing else in that module. I would choose to give it.

   3. **The Interface rule "raises the same error unchanged" has no criterion of its own.** Criterion 1 checks the claim, the agent runtime and the next tick. Criterion 3 checks the counted handler error. Neither checks that the `HostingServiceError` reaches the caller as the same exception, with no wrapping. Criterion 2 checks that the original `HostingServiceError`, not `PushFailed`, is raised when the release push fails. Please add a criterion, or confirm that criterion 3's `HostingServiceError: ...` line covers it. I would add one.

   4. **The release commit has no criterion.** The Interface fixes the subject `commit_subject(<id>, "claim released: hosting failed")`. It also says the commit is a single commit, that the journal gets no new entry, and that attempts and round do not change. Criterion 1 covers only the crash count. Please add a criterion for the subject, the single commit and the unchanged journal, attempts and round. I would add one.
4. 2026-11-04 human: Answers of the human:

   1. **(a)** Release the claim on `HostingServiceError`, as written and as the acceptance proposed. The Description loses its "To refine" paragraph and says the choice is made: a pull request before the claim would open a race between two instances.
   2. Leave for S0010's tester: in `tests/application/test_hosting_failure_after_claim.py`, only the `xfail(strict=True, ...)` mark of `test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick` goes; nothing else in that module changes. (Also in `feature.md`, decision 12.)
   3. Yes, add a criterion: the `HostingServiceError` reaches the caller as the same exception object, not wrapped; a row where the release push succeeds and one where it fails (criterion 2's case).
   4. Yes, add a criterion: one release commit with the subject `commit_subject(<id>, "claim released: hosting failed")`, no new journal entry, and attempts and round unchanged.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal 4) carried into the story.
   Changes I made from journal 4: the Description lost its "To refine" paragraph and now says approach (a) was chosen and why (b) was rejected (the race between two instances). Two criteria were added before the closing two: new 6 (the same `HostingServiceError` object reaches the caller, rows for the release push succeeding and failing) and new 7 (one release commit with the subject, no new journal entry, attempts and round unchanged). `make check` and `docs:` are now 8 and 9. The leave for the `xfail` mark is in `feature.md`, decision 12.
   - Interface: concrete. It names `factory.application.stage`, `StageRunner._start`, `ensure_pull_request`, `Claims.release`, `push_with_retries` and the commit subject. Each stated behaviour now has a criterion: the release (1), the failed release push (2), the unchanged error (6), the subject, the single commit and the unchanged journal, attempts and round (7), and other errors (4).
   - Criteria: each is testable by one test function or one parametrized test. Both sides of each rule are covered: release pushed or not (2, 6), `HostingServiceError` or another error (4), and the cap of three (3).
   - Smoke test: runnable. The grep count and the pytest tail are checkable, and the `Expect:` line names `0` and a line ending in `passed` with no `failed` or `xfailed`. I did not check the pytest `addopts`, since the command passes no `-q`.
   - Architecture: the change sits in `factory.application`, using the `Claims` and push helpers that already exist. No new layer or dependency.
   - Scope: within F0050 (S0010 is listed in the feature) and not in "Out of scope". The cap of three stays, as the feature requires. The change to S0008's test is limited to the `xfail` mark, with the human's leave.
7. factory: started tests as vm.
8. tester: I stopped before writing any test. Criterion 3 cannot hold together with the Interface as written, and I need the human to choose.

   **The conflict.** The handler's error count is kept per event key and per *remote state* (`factory.domain.tick_status.record_error`: "A new remote state starts the key's count again at 1"). For a work item that has a branch, the event's remote state is the branch head (`factory.domain.evaluation._event`: `remote_state = snapshot.branch_commit`). Under approach (a), every failing tick pushes two new commits to the branch: the claim and the release. So the next tick sees a new branch head, and its count starts again at `1 of 3`. Three failing ticks in a row would log `1 of 3` three times and never reach the cap. That contradicts criterion 3's "three failing ticks in a row reach it". It also contradicts the Description's "The handler's error count and its cap of three stay as they are": the code would stay the same, but the count would no longer add up.

   **Options:**
   - (A) Rewrite criterion 3 to match how the code counts. The failed tick logs `handler error run:<id> 1 of 3: HostingServiceError: ...`. Because each release moves the branch, the count restarts at 1 on every failing tick, so a long outage never reaches the cap and never posts an error stop. The factory just retries every tick until the hosting service is back. Rows: one failing tick logs `1 of 3`; three failing ticks in a row log `1 of 3` each time and post no error stop. Nothing in the domain changes.
   - (B) Keep "three failing ticks reach the cap". The count would then have to survive the claim and release commits, for example by keying a run event's count on the branch commit before the claim, or by ignoring claim and release commits. That is a domain change (`tick_status`/`evaluation`) that the Interface does not name, so it would need its own Interface line and criterion.
   - (C) Leave the branch head unchanged by the release, by resetting the branch to the pre-claim commit instead of adding a commit. That needs a force push, which contradicts the Interface's "one commit, pushed through `push_with_retries`" and criterion 7.

   I would choose (A). It keeps the scope as the human set it, and it matches the story's goal: an outage costs nothing and wakes on its own when hosting returns. The new criterion 3 would read: "The failed tick's handler error is logged as S0008 built it (`handler error <event key> 1 of 3: HostingServiceError: ...`); because the release moves the branch, each failing tick counts from 1 again: three failing ticks in a row each log `1 of 3`, and no error stop is posted."

   **For when the tests are written:** criterion 2's "refused four times" fits `push_with_retries`, which makes 1 try plus 3 retries (`RETRY_WAITS`). I plan to refuse only the release push with a pre-receive hook on the world's bare remote that checks for the release subject. No files created, no test run, no module imports checked yet.
9. 2026-11-04 human: Answer of the human:

   **(A)**, as you propose. Rewrite criterion 3 with your wording: the failed tick logs S0008's handler error (`handler error <event key> 1 of 3: HostingServiceError: ...`); because the release moves the branch, each failing tick counts from 1 again, so three failing ticks in a row each log `1 of 3` and no error stop is posted. The Description's sentence on the count changes with it: the code of the count and its cap stay as they are, and during a hosting outage after the claim the factory retries every tick until the service is back. Nothing in the domain changes.

   Your plan for criterion 2 (a pre-receive hook on the world's bare remote that refuses only the release push) is fine.

   The claim and release commits that a long outage adds to the branch are accepted for this story; I note them for later planning.
10. factory: started tests as vm.
11. tester: Tests written from the criteria, with criterion 3 as the human reworded it in journal 9 (option A). I also carried that answer into `## Description`: criterion 3 now has the wording from journal 9, and the sentence on the count now says the factory retries every tick during an outage. Intake had not done this.

    - criterion 1: tests/application/test_hosting_failure_releases_claim.py::test_a_hosting_failure_after_the_claim_releases_it_and_the_next_tick_runs_the_stage
    - criterion 2: tests/application/test_hosting_failure_releases_claim.py::test_a_release_whose_push_is_refused_four_times_leaves_the_claim_and_a_crash_follows (rows pushed-first-try, pushed-after-two-refusals, refused-four-times). A pre-receive hook on the world's bare remote refuses only pushes whose head has the release subject, as the human approved in journal 9.
    - criterion 3: tests/application/test_hosting_failure_releases_claim.py::test_each_failing_tick_counts_its_handler_error_from_one_and_reaches_no_cap (rows one-tick, three). Every `handler error` line counts `1 of 3`, all under the same `:<id>` event key, and no `error cap reached` line appears.
    - criterion 4: tests/application/test_hosting_failure_releases_claim.py::test_an_error_other_than_a_hosting_failure_after_the_claim_releases_nothing. It drives `StageLauncher.launch` directly with a document that has no title line, which gives `WorkItemFormatError`. The claim stands, there is no release commit and no agent call.
    - criterion 5: tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick. Only its `xfail(strict=True, ...)` mark was removed, under the human's leave (journal 4, feature.md decision 12). Nothing else in that module changed.
    - criterion 6: tests/application/test_hosting_failure_releases_claim.py::test_the_hosting_failure_reaches_the_caller_as_the_same_exception (rows release-pushed, release-refused). It uses a `FakeHostingService` subclass whose `create_pull_request` raises one known `HostingServiceError`, and checks the error with `is`.
    - criterion 7: tests/application/test_hosting_failure_releases_claim.py::test_the_release_is_one_commit_with_its_subject_and_leaves_the_journal_and_counters. One commit has the subject `commit_subject(<id>, "claim released: hosting failed")`, it is the branch head, and its only parent is the claim commit. Journal, attempts, round and crashes are equal to the claim commit's.
    - criteria 8 and 9: no test (`make check`, docs).

    Files: created tests/application/test_hosting_failure_releases_claim.py; changed tests/application/test_hosting_failure_after_claim.py (mark only) and the work item's Description.

    One run with `uv run pytest -q` on the two files: 6 failures plus S0008's test, all wrong results because no release happens yet (claim still set, crash entry, `crash:` event key on the second tick). Four pass today, as expected, because they pin behaviour that stays the same: the one-tick count, the WorkItemFormatError case, and both rows of the same-exception check. The release-refused row of criterion 2 checks the journal's crash entry only. After the crash, the queued run finishes the stage and the `crashes` field is 0 again. Every module imported; nothing failed to import. `make lint` is green; the type check was skipped as the stage says.

    The factory left out changes outside the write paths: factory/features/F0050-the-factory-shows-what-it-runs-and-what-it-uses/in-progress/F0050-S0010-a-hosting-failure-after-the-claim-charges-no-crash.md.

    `lint`: lint: green (0.1 s)
12. factory: started doing as vm.
13. coder: I stopped with the code written and `make check` red on one of S0008's tests, which contradicts criterion 1. I may not change that test.

    **Built:** `src/factory/application/stage.py`. In `StageLauncher._start`, a `HostingServiceError` from `ensure_pull_request` calls the new `_release_after_hosting_failure`. It clears the claim (`ClaimService.release`), writes the work item, commits it with `commit_subject(<id>, RELEASE_AFTER_HOSTING_FAILURE)` ("claim released: hosting failed") and pushes through `push_with_retries`. Then the same error is raised again with a bare `raise`. When the push fails with `PushFailed`, the method logs `claim release not pushed: ...` and swallows the failure, so the original `HostingServiceError` still reaches the caller and the claim on the remote stands, as before. Other errors are not caught. Main choice: catch at the one call in `_start`, where the claim and the document are at hand. Rejected: catching in the tick handler, which would need to know about claims and the work item's path. Every test in `tests/application/test_hosting_failure_releases_claim.py` passes, and so does `test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick` without its `xfail` mark. lint, types, layers, sast, secrets and licenses are green.

    **The contradiction.** `make test` fails on one test only:

    ```
    FAILED tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run - AssertionError: assert None is not None
    tests/application/test_hosting_failure_after_claim.py:23: AssertionError
    ```

    This S0008 test checks `claimed.claim is not None` after the failed tick. Criterion 1 requires "leaves the branch with no claim". Both cannot pass. The human's leave (journal 4) covers only the `xfail` mark of the other test in that module.

    **Options:**
    - (a) Leave for the tester to delete `test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run`. Its other check, no agent call, is covered by criterion 1's test `test_a_hosting_failure_after_the_claim_releases_it_and_the_next_tick_runs_the_stage`.
    - (b) Leave for the tester to change line 23 to `assert claimed.claim is None` and rename the test, for example `..._releases_the_claim_and_runs_no_agent`. The standing leave keeps test names, so this needs the human too.
    - (c) Keep the claim standing: this undoes approach (a) and is not recommended.

    I would choose (a). After the answer, the coder ends with `tests` and names the change.

    Noticed, not touched: a release whose push fails leaves an unpushed release commit in the factory's local checkout. The next tick starts from the remote, so I left that alone.
14. 2026-11-04 human: Answer of the human:

    **(a)**, as you propose. Leave for S0010's tester: delete `tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run`. It pinned the old behaviour that this story replaces, and its other check (no agent run) is covered by criterion 1's test. Nothing else in that module changes, apart from the `xfail` mark already granted. The tester names the deletion in its entry.

    Your handling of a failed release push (logged, the original `HostingServiceError` raised, the remote claim left as before) is fine as it is.
15. factory: started doing as vm.
16. coder: The human's answer (journal 14) calls for a test change, so I changed no code and hand the work item to the tester. The change, in one sentence: delete `tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run`, which pinned the claim left standing that this story replaces; nothing else in that module changes apart from the `xfail` mark already removed, and the tester names the deletion in its entry.

    The code from journal 13 is already on the branch (`src/factory/application/stage.py`: `_release_after_hosting_failure` called from `_start`), and the human accepted how it handles a failed release push. With that one test deleted, `make check` was red only on that test in the last run, so it should come back green. I did not run `make check` this time because nothing changed. Journal 14 does not change what the task means, so the Description stays as it is.
