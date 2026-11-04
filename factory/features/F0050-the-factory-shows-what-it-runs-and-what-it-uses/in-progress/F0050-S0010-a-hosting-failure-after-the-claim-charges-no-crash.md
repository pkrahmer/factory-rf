---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 549
comments_read: [6643408151, 6643585034, 6643890182]
handed_over: null
claim:
  instance: vm
  stage: smoke-test
  started_at: '2026-11-04T22:51:26.964369Z'
  lease_duration: 60
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
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-04T22:35:56.678654Z'
  stage: tests
- number: 18
  speaker: tester
  kind: result
  at: '2026-11-04T22:36:20.346471Z'
  stage: tests
  run: b0a76fbbce95436c8196303c776bdd83
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-04T22:36:25.675909Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-11-04T22:41:02.153183Z'
  stage: doing
  run: da7c935b242344f6b98f824f3bec5b3c
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-04T22:41:07.989600Z'
  stage: review
- number: 22
  speaker: reviewer
  kind: result
  at: '2026-11-04T22:42:50.634076Z'
  stage: review
  run: 15b838dff5e344adbc385b96572fc610
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-04T22:42:56.217695Z'
  stage: doing
- number: 24
  speaker: coder
  kind: result
  at: '2026-11-04T22:43:29.616759Z'
  stage: doing
  run: f333dcaa1ef846958371354d2116873f
- number: 25
  speaker: factory
  kind: started
  at: '2026-11-04T22:43:35.134159Z'
  stage: tests
- number: 26
  speaker: tester
  kind: result
  at: '2026-11-04T22:44:28.431470Z'
  stage: tests
  run: 9b42f37f005c4675bea02a49721d5970
- number: 27
  speaker: factory
  kind: started
  at: '2026-11-04T22:44:34.083781Z'
  stage: doing
- number: 28
  speaker: coder
  kind: result
  at: '2026-11-04T22:49:28.035120Z'
  stage: doing
  run: ba2b932ac56b4f77a61830b615424504
- number: 29
  speaker: factory
  kind: started
  at: '2026-11-04T22:49:33.422126Z'
  stage: review
- number: 30
  speaker: reviewer
  kind: result
  at: '2026-11-04T22:50:32.846721Z'
  stage: review
  run: fa030a0163fa436bb90a26317f3c3b04
- number: 31
  speaker: factory
  kind: started
  at: '2026-11-04T22:50:38.288251Z'
  stage: docs
- number: 32
  speaker: documenter
  kind: result
  at: '2026-11-04T22:51:21.623557Z'
  stage: docs
  run: be45b84dbc9c4f91839eb47a2ac68a96
- number: 33
  speaker: factory
  kind: started
  at: '2026-11-04T22:51:26.964369Z'
  stage: smoke-test
---

# A hosting failure after the claim charges no crash

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

S0008 pinned what happens when the hosting service fails right after a stage's claim was pushed. `StageRunner._start` (`src/factory/application/stage.py:158-175`) pushes the claim, then calls `Opening.ensure_pull_request`. When the hosting service fails there, no agent has run. But the claim stands, and the next tick reads the claim without a result as a crash: it records `factory: crash` and counts it. `tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick` holds this as `xfail(strict=True, reason="a crash is charged for a stage in which no agent ran")`. During an outage like that of 2026-11-04, two such ticks reach the crash cap of a work item whose agent never ran, and the human must write a comment to wake it. This story makes that failure cost nothing. The stage that meets a hosting error after its claim and before its agent run releases its claim, so the next tick starts the stage afresh, with no crash. The code of the handler's error count and its cap of three stay as they are; because each release moves the branch, each failing tick counts its error from 1 again, so during a hosting outage after the claim the factory retries every tick until the service is back. **The human chose (a)** (journal 4): on `HostingServiceError` from `ensure_pull_request`, the stage clears its claim (`Claims.release`), commits `<id>: claim released: hosting failed` and pushes it through `push_with_retries`, then raises the error as today. If that push also fails, today's crash stands. A pull request before the claim was rejected: it would open a race between two instances.

## Interface

- `factory.application.stage` (application), `StageRunner._start`: a `HostingServiceError` raised by `ensure_pull_request` after the claim was pushed releases the claim on the work item's branch (one commit, pushed through `push_with_retries`), then raises the same error unchanged.
- The release commit's subject is `commit_subject(<id>, "claim released: hosting failed")`. Its journal gets no `crash` entry and no new entry of its own; the crash count, attempts and round do not change.
- A release whose push fails (`PushFailed` after the retries) leaves the claim standing, as today, and raises the original `HostingServiceError`; the next tick then records the crash as today.
- Any other error after the claim (not `HostingServiceError`) is handled as today.
- Tests: the mark `xfail(strict=True, ...)` comes off `tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick`, and the test stays as it is otherwise. That test is S0008's, so this needs the human's leave in `feature.md`. New tests go into `tests/application/test_hosting_failure_releases_claim.py`.

## Acceptance criteria

1. A tick whose stage meets a hosting failure in `ensure_pull_request` after the claim was pushed leaves the branch with no claim, and the agent runtime has no call. At the next tick, with the hosting service back, the journal has no `crash` entry, the crash count is 0, and the stage starts and runs its agent.
2. When the release's push is refused four times (the retries spent), the claim stands, and the next tick records a crash, as today. Rows: the release pushed on the first try, the release pushed after two refusals, the release refused four times.
3. The failed tick's handler error is logged as S0008 built it (`handler error <event key> 1 of 3: HostingServiceError: ...`); because the release moves the branch, each failing tick counts from 1 again: three failing ticks in a row each log `1 of 3`, and no error stop is posted.
4. An error other than `HostingServiceError` after the claim (for example `WorkItemFormatError` for a body with no title line) releases nothing and is handled as today.
5. S0008's test `test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick` passes without its `xfail` mark.
6. The `HostingServiceError` reaches the caller as the same exception object, not wrapped. Rows: the release push succeeds; the release push fails (criterion 2's case).
7. The release is one commit with the subject `commit_subject(<id>, "claim released: hosting failed")`; the journal has no new entry, and attempts and round are unchanged.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`, in the section on stops and errors where S0008 described a hosting outage: a hosting failure right after a claim releases the claim, so it charges no crash; because each release moves the branch, such an outage never reaches the error cap and posts no error stop: the factory retries every tick until the service is back. `docs/decisions.md`: one entry with the reason (a crash was charged for a stage in which no agent ran, found by S0008's test), the approach the human chose, and its consequence (the error count starts at 1 on every failing tick, so the outage retries every tick and reaches no cap). `README.md` and the project guide: none.

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
17. factory: started tests as vm.
18. tester: Made the test change the human approved in journal 14, as the coder named it in journal 16. In `tests/application/test_hosting_failure_after_claim.py` I deleted `test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run`. It pinned the claim being left in place after a hosting failure, which this story replaces. Its check that no agent ran is covered by criterion 1's test in `tests/application/test_hosting_failure_releases_claim.py`.

    With that test gone, the module's import of `branch_state` from `proof_support` was unused, so I removed it from the import line. I made no other change. The `failed_after_claim` fixture stays, and so does `test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick`, which already had its `xfail` mark removed in journal 11.

    Earlier test file changed: tests/application/test_hosting_failure_after_claim.py, under the human's leave (journals 4 and 14). No files created. Every module imported.

    One run of `uv run pytest -q tests/application/test_hosting_failure_after_claim.py`: 1 passed. `make lint`: lint: green (0.1 s).

    `lint`: lint: green (0.2 s)
19. factory: started doing as vm.
20. coder: `make check` is green (`check: green`, coverage 99.26 %) now that the tester has deleted S0008's old claim-stands test (journal 18). I changed no code in this round.

    **Built** (written in journal 13 and unchanged since): `src/factory/application/stage.py`.
    - In `StageLauncher._start`, a `HostingServiceError` from `ensure_pull_request` calls `_release_after_hosting_failure` and then re-raises the same error with a bare `raise`.
    - `_release_after_hosting_failure` clears the claim through `ClaimService.release` and writes the work item. It then makes one commit with the subject `commit_subject(<id>, RELEASE_AFTER_HOSTING_FAILURE)` ("claim released: hosting failed") and pushes it through `push_with_retries`.
    - If that push fails with `PushFailed`, it logs `claim release not pushed: ...` and does not raise. So the original `HostingServiceError` still reaches the caller, and the claim on the remote stands as before; the human accepted this in journal 14.
    - Errors other than `HostingServiceError` are not caught.

    **Main choice:** catch the error at the one call in `_start`, where the claim and the document are at hand. **Rejected:** catching it in the tick handler, which would then need to know about claims and the work item's path.

    **Refactor:** I read the diff once more and nothing needed changing. It is two small blocks with no duplicated code, and they reuse the helpers that already exist (`ClaimService.release`, `commit_subject`, `push_with_retries`).

    **Description:** journals 14 to 18 changed only tests, not what the task means, so the Description stays as it is.

    **Noticed, not touched:** when the release push fails, the release commit stays unpushed in the factory's local checkout. The next tick starts from the remote, so I left it alone.

    `check`: check: green
    `duplicates`: duplicates: 4 new, 41 known, 2 gone
21. factory: started review as vm.
22. reviewer: Review of round 0. I read `src/factory/application/stage.py` (`_start` and `_release_after_hosting_failure`), the two test modules and the work item. The code does what the Interface says. It catches only `HostingServiceError` from `ensure_pull_request`, makes one release commit with the subject, pushes it through `push_with_retries`, logs a `PushFailed` and swallows it, and re-raises the original error with a bare `raise`. Every criterion has a test. The coder's last `make check` was green (journal 20). The 4 new `make duplicates` findings are all in modules this diff does not touch (`claude_runtime`/`opencode_runtime`, `cost_records`).

    Findings:
    1. Work item, `## Acceptance criteria` 3: it still says "The cap of three is unchanged: three failing ticks in a row reach it." That contradicts the human's answer (journal 9, option A) and the test `test_each_failing_tick_counts_its_handler_error_from_one_and_reaches_no_cap`. The tester's rewrite was dropped as outside its write paths (journal 11). Fix: rewrite criterion 3 with the wording from journal 9: the failed tick logs `handler error <event key> 1 of 3: HostingServiceError: ...`; because the release moves the branch, each failing tick counts from 1 again, so three failing ticks in a row each log `1 of 3` and no error stop is posted.
    2. Work item, criterion 9 (`docs:`): the operator guide line says only that the claim is released and no crash is charged. After journal 9, the operator must also know that a hosting outage after the claim never reaches the error cap and posts no error stop: the factory retries every tick until the service is back. Fix: add that to criterion 9's `docs/operator-guide.md` item, and the same consequence to its `docs/decisions.md` entry.
    3. `tests/application/test_hosting_failure_releases_claim.py:114-120`: the fixture `failed_tick` is a copy of `failed_after_claim` in `tests/application/test_hosting_failure_after_claim.py:9-15` (same body, same docstring). Fix: the tester moves the fixture to `tests/conftest.py` under the standing leave and has both modules use it. S0008's test keeps its name and what it checks.
    4. `tests/application/test_hosting_failure_releases_claim.py:94-100`: `_log_text` re-reads `world.state / "factory.log"`, which copies `state_log_lines` in `tests/log_support.py:12-15`. Fix: build `_handler_errors` and the `error cap reached` check on `state_log_lines(world.state)`.
    5. `tests/application/test_hosting_failure_releases_claim.py:222-233`, row `release-refused` of `test_the_hosting_failure_reaches_the_caller_as_the_same_exception`: the test never checks that the release push was actually refused. If the hook did not fire, the row would pass the same way as `release-pushed`, so it would not pin criterion 6's "release push fails" side. Fix: also assert, per row, that `branch_state(world, work_item).claim` is `None` exactly when `refusals == 0`.

    description corrected: "The handler's error count and its cap of three stay as they are." -> "The code of the handler's error count and its cap of three stay as they are; because each release moves the branch, each failing tick counts its error from 1 again, so during a hosting outage after the claim the factory retries every tick until the service is back." (journal 9)

    Notes:
    - `tests/application/test_hosting_failure_releases_claim.py:155-162`, criterion 2: the side of the four-try limit with three refusals (pushed on the last try) has no row. The code handles it: `src/factory/application/pushes.py:26-34` tries 1 + `len(RETRY_WAITS)` = 4 times. Missing row: `pytest.param(3, True, id="pushed-after-three-refusals")`.

    Earlier tests:
    - `tests/application/test_hosting_failure_after_claim.py`: the human's leave, journal 4 (the `xfail` mark removed) and journal 14 (`test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run` deleted). Dropping the `branch_state` import that the deletion left unused follows from that deletion. Nothing else changed.
23. factory: started doing as vm.
24. coder: Round 1. I worked through the reviewer's findings from journal 22. I changed no code. Findings 3 to 5 change tests, so the work item goes to the tester.

    **Findings 1 and 2 (the work item's criteria):** I edited `## Acceptance criteria` in the work item. If my write paths do not include the work item, the factory will drop this edit, as it dropped the tester's edit in journal 11. In that case these two findings are still open and need someone whose write paths do include it.
    - Criterion 3 now uses the human's wording from journal 9. The failed tick's handler error is logged as S0008 built it (`handler error <event key> 1 of 3: HostingServiceError: ...`). Because the release moves the branch, each failing tick counts from 1 again: three failing ticks in a row each log `1 of 3`, and no error stop is posted.
    - Criterion 9, the `docs/operator-guide.md` item, now also says that a hosting outage after the claim never reaches the error cap and posts no error stop. The factory retries every tick until the service is back. The `docs/decisions.md` item now also names that consequence.

    **Test changes for the tester (findings 3 to 5, in one sentence each):**
    - 3: Move the fixture `failed_tick` in `tests/application/test_hosting_failure_releases_claim.py` to `tests/conftest.py`, so that it and its copy `failed_after_claim` in `tests/application/test_hosting_failure_after_claim.py` become one fixture. Both modules then use it. This falls under the standing leave, and S0008's test keeps its name and what it checks.
    - 4: In `tests/application/test_hosting_failure_releases_claim.py`, replace `_log_text` with `state_log_lines(world.state)` from `tests/log_support.py`. Build `_handler_errors` and the `error cap reached` check on it.
    - 5: In `test_the_hosting_failure_reaches_the_caller_as_the_same_exception`, also assert per row that `branch_state(world, work_item).claim` is `None` exactly when `refusals == 0`.
    - The reviewer's note, optional: add the row `pytest.param(3, True, id="pushed-after-three-refusals")` to criterion 2's test.

    **Built:** unchanged since journal 13. In `src/factory/application/stage.py`, `_start` catches a `HostingServiceError` from `ensure_pull_request`, then `_release_after_hosting_failure` releases the claim and the same error is raised again. The main choice and the rejected alternative are the ones in journal 20. I did not run `make check`, because I changed no code. The last run was green (journal 20).

    **Noticed, not touched:** when the release push fails, the release commit stays unpushed in the factory's local checkout. The next tick starts from the remote, so I left it alone.

    The factory left out changes outside the write paths: factory/features/F0050-the-factory-shows-what-it-runs-and-what-it-uses/in-progress/F0050-S0010-a-hosting-failure-after-the-claim-charges-no-crash.md.
25. factory: started tests as vm.
26. tester: Made the test changes the coder named in journal 24 for review findings 3 to 5, and added the reviewer's optional row. I changed no code.

    - Finding 3 (standing leave to move a shared test helper): I moved the duplicated fixture into `tests/conftest.py` as `failed_after_claim`, with the same body and docstring. It is deleted from both modules. I kept S0008's fixture name, so `tests/application/test_hosting_failure_after_claim.py` changes only by losing its fixture and its now unused `import pytest`. Its test `test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick` keeps its name and checks the same thing. In `tests/application/test_hosting_failure_releases_claim.py`, the two tests that used `failed_tick` now take `failed_after_claim`.
    - Finding 4: in `tests/application/test_hosting_failure_releases_claim.py` I removed `_log_text`. `_handler_errors` now applies `HANDLER_ERROR` to each line of `state_log_lines(world.state)` from `tests/log_support.py`. The `error cap reached` check in `test_each_failing_tick_counts_its_handler_error_from_one_and_reaches_no_cap` reads the same lines.
    - Finding 5: `test_the_hosting_failure_reaches_the_caller_as_the_same_exception` now also asserts, for each row, that `branch_state(world, work_item).claim` is `None` exactly when `refusals == 0`.
    - Reviewer's note: I added `pytest.param(3, True, id="pushed-after-three-refusals")` to `test_a_release_whose_push_is_refused_four_times_leaves_the_claim_and_a_crash_follows`. That row is the passing side of the four-try limit.

    Criterion → test mapping: unchanged from the earlier tests entries. Only the fixture's name and source moved, and the assertions above were added.

    Earlier test files I changed: `tests/application/test_hosting_failure_after_claim.py` (S0008's) and `tests/conftest.py`, both under the standing leave to move a shared test helper. No files created. Every module imported.

    One run of `uv run pytest -q` over the two test modules: 12 passed. `make lint`: lint: green (0.2 s).

    Still open: the coder's edits to criteria 3 and 9 (findings 1 and 2) were dropped from the take because they are outside the coder's write paths (journal 24). The work item is outside the tester's write paths as well, so those two findings still need someone whose write paths include it.

    `lint`: lint: green (0.2 s)
27. factory: started doing as vm.
28. coder: Round 1, after the tester's changes in journal 26. I changed no code. `make check` is green: `check: green`, `test: green (116.1 s)`, coverage 99.26 %. The moved `failed_after_claim` fixture in `tests/conftest.py` and the new assertions in `tests/application/test_hosting_failure_releases_claim.py` all pass against the code already on the branch.

    **Built:** `src/factory/application/stage.py`, unchanged since journal 13.
    - `StageLauncher._start` catches a `HostingServiceError` from `ensure_pull_request`, calls `_release_after_hosting_failure`, then re-raises the same error with a bare `raise`.
    - `_release_after_hosting_failure` clears the claim through `ClaimService.release`, writes the work item, makes one commit with the subject `commit_subject(<id>, RELEASE_AFTER_HOSTING_FAILURE)` and pushes it through `push_with_retries`.
    - If that push fails with `PushFailed`, the failure is logged and the original error still reaches the caller.

    **Main choice:** catch the error at the one call in `_start`, where the claim and the document are at hand. **Rejected:** catching it in the tick handler, which would then need to know about claims and work item paths.

    **Refactor:** I read the diff again. It is still two small blocks that reuse the existing helpers, so nothing needed changing.

    **Still open: review findings 1 and 2 (journal 22).** They ask to rewrite acceptance criteria 3 and 9 in the work item. The work item is outside both the coder's and the tester's write paths, so my edit in journal 24 was dropped. The reviewer corrected the Description in journal 22, so its write paths seem to include the work item. I hand it back so that the reviewer can make those two criterion edits, using the wording in journal 24. Nothing in the code depends on them: the test `test_each_failing_tick_counts_its_handler_error_from_one_and_reaches_no_cap` already pins the behaviour the human chose in journal 9. Journal 26 did not change what the task means; I did not touch the Description.

    **Noticed, not touched:** when the release push fails, the release commit stays unpushed in the factory's local checkout. The next tick starts from the remote, so I left it alone.

    `check`: check: green
    `duplicates`: duplicates: 4 new, 41 known, 2 gone
29. factory: started review as vm.
30. reviewer: Review of round 1. I read `src/factory/application/stage.py` (`_start` and `_release_after_hosting_failure`), `tests/application/test_hosting_failure_releases_claim.py`, the changes to `tests/application/test_hosting_failure_after_claim.py` and `tests/conftest.py`, and the work item. The code is unchanged since round 0 and still does what the Interface says:
    - It catches only `HostingServiceError`, and only from `ensure_pull_request`.
    - It makes one release commit through `ClaimService.release` with the subject from `commit_subject` and pushes it through `push_with_retries`.
    - If that push raises `PushFailed`, it logs the failure and swallows it. The original error then goes up through a bare `raise`.

    The coder's last `make check` was green (journal 28). The 4 new `make duplicates` findings are in modules this diff does not touch.

    Round 0's findings:
    - 3, 4 and 5 are fixed (journal 26).
      - 3: the fixture is now shared as `failed_after_claim` in `tests/conftest.py`.
      - 4: `_handler_errors` reads `state_log_lines`.
      - 5: the `release-refused` row now checks that the claim stands.
    - My note is fixed too: the row `pushed-after-three-refusals` is in.
    - 1 and 2 were stuck: neither the coder nor the tester may write the work item, so I made both edits myself. Journal 9 settles them, and I changed nothing else in the work item.

    no findings

    description corrected: criterion 3 "The handler error of the failed tick is counted and logged as S0008 built it (`handler error <event key> 1 of 3: HostingServiceError: ...`). The cap of three is unchanged: three failing ticks in a row reach it." -> "The failed tick's handler error is logged as S0008 built it (`handler error <event key> 1 of 3: HostingServiceError: ...`); because the release moves the branch, each failing tick counts from 1 again: three failing ticks in a row each log `1 of 3`, and no error stop is posted." (the human's wording, journal 9)
    description corrected: criterion 9's `docs/operator-guide.md` item "a hosting failure right after a claim releases the claim, so it charges no crash" -> the same, plus "because each release moves the branch, such an outage never reaches the error cap and posts no error stop: the factory retries every tick until the service is back". Its `docs/decisions.md` item now also names that consequence: the error count starts at 1 on every failing tick, so the outage is retried every tick and reaches no cap. This is the behaviour the human chose in journal 9, and the documenter writes from this criterion.

    Earlier tests:
    - `tests/application/test_hosting_failure_after_claim.py`: changed under the human's leave and the standing leave.
      - Human's leave, journal 4: the `xfail` mark came off.
      - Human's leave, journal 14: `test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run` was deleted, and so was the `branch_state` import that the deletion left unused.
      - Standing leave to move a shared test helper (journal 26): the fixture `failed_after_claim` moved to `tests/conftest.py`, and the `import pytest` it left unused went too. `test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick` keeps its name and what it checks.
    - `tests/conftest.py`: standing leave to move a shared test helper. It only gains the moved fixture `failed_after_claim`, with the same body and docstring, and the `run_ticks` import it needs.
31. factory: started docs as vm.
32. documenter: Docs for F0050-S0010. I changed only documents, so I did not run `make check`; the factory's checks after this stage decide.

    Files changed:
    - `docs/operator-guide.md`, section "During an outage of the hosting service": a new bullet. A hosting failure right after a claim releases the claim and charges no crash. The release commit is `<id>: claim released: hosting failed`. Each failing tick counts its error from 1 again, so the outage never reaches the cap and posts no error stop, and the factory retries every tick. A release whose push fails logs `claim release not pushed: ...` and leaves the claim, so the crash is charged as before. Other errors release nothing.
    - `docs/decisions.md`: a new entry, "A hosting failure after the claim releases the claim and charges no crash", with the decision, the reason and the consequence. Its "Rejected" line comes from the story's journal: opening the pull request before the claim, keeping the count across the claim and release commits, and resetting the branch (a force push). In the S0008 entry, I changed the "Open" line, which said the `xfail` was unfixed, to say it is fixed by S0010.

    Cross-read and found current: `README.md`, `docs/project-guide/` (the criterion says none), and the rest of `docs/operator-guide.md` (the crash and error-cap text, including "A longer outage is as before"). I read the diff in `src/factory/application/stage.py` against the Interface and found no mismatch, so there are no findings for the coder.

    Stale text I did not touch: none found.

    I did not run the story's smoke-test commands (`grep -c xfail`, `uv run pytest -k hosting_failure`). I did not run any code in this stage, because I wrote no examples.

    `check`: check: green (not run again: passed on tree a4a57514a13e at 2026-11-04T22:47:18Z)
    `secrets`: secrets: green (2.9 s)
    `documents`: documents ok
33. factory: started smoke-test as vm.
