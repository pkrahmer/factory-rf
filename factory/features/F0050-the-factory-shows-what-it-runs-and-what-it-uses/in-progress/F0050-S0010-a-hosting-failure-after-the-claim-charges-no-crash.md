---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 549
comments_read: [6643408151]
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
---

# A hosting failure after the claim charges no crash

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

S0008 pinned what happens when the hosting service fails right after a stage's claim was pushed. `StageRunner._start` (`src/factory/application/stage.py:158-175`) pushes the claim, then calls `Opening.ensure_pull_request`. When the hosting service fails there, no agent has run. But the claim stands, and the next tick reads the claim without a result as a crash: it records `factory: crash` and counts it. `tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick` holds this as `xfail(strict=True, reason="a crash is charged for a stage in which no agent ran")`. During an outage like that of 2026-11-04, two such ticks reach the crash cap of a work item whose agent never ran, and the human must write a comment to wake it. This story makes that failure cost nothing. The stage that meets a hosting error after its claim and before its agent run releases its claim, so the next tick starts the stage afresh, with no crash. The handler's error count and its cap of three stay as they are. **To refine:** the human picks the approach. (a) Release: on `HostingServiceError` from `ensure_pull_request`, the stage clears its claim (`Claims.release`), commits `<id>: claim released: hosting failed` and pushes it through `push_with_retries`, then raises the error as today. If that push also fails, today's crash stands. (b) Open first: call `ensure_pull_request` before the claim, so that a hosting failure leaves nothing to undo. This needs a reading of the race between two instances, since the pull request would exist before the claim decides who works. The acceptance would choose (a). The criteria below are written for (a).

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
6. `make check` stays green.
7. docs: `docs/operator-guide.md`, in the section on stops and errors where S0008 described a hosting outage: a hosting failure right after a claim releases the claim, so it charges no crash. `docs/decisions.md`: one entry with the reason (a crash was charged for a stage in which no agent ran, found by S0008's test) and the approach the human chose. `README.md` and the project guide: none.

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
