---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 317
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T02:09:58.782726Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T02:09:58.788211Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T02:10:13.588548Z'
  stage: intake
  run: 6e1a6ed050a241bca744d33090cc35d5
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T02:10:34.448619Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T02:13:08.763818Z'
  stage: tests
  run: f041459261a14168a99fa0c64fc4eb6b
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T02:13:29.143493Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T02:15:15.168113Z'
  stage: doing
  run: 8163a3393c0b4eaf935b093f987eddc3
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T02:15:35.471015Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T02:16:17.167380Z'
  stage: review
  run: ae0ee1f9fd39409c906eee616796ff62
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T02:16:37.646478Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T02:16:52.696254Z'
  stage: docs
  run: 41a9decde5744b27a7f087d35d540cd9
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T02:17:12.972474Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T02:17:29.332154Z'
  stage: smoke-test
  run: 603bea80c28a4e199b9fcea79b7a43ff
---

# The tests pin the subjects of a story's recovery and handler commits

## Description

The mutation sweep of 2026-10-19 over `factory.application` (`planning/overnight/mutation-sweep-2026-10-19-part2.md`, its story 6) left 15 live mutants in the subjects of the commits that the recovery and three handlers record on a story's branch; the acceptance's eight are S0005's. No test reads these subjects: the crash or expiry recorded (`recovery.py:102`), the pull request an expiry note opened (`recovery.py:174`), the send-back (`handlers/closed.py:119`) and the comments copied from the pull request (`handlers/comments.py:103`). The move-back's subject is checked only for its marker, so the work item's id in it is not pinned (`handlers/reject.py:47`). The human reads these subjects in the branch's history, so they are behaviour, not wording. This story pins them as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003.

## Interface

No module under `src/factory/` changes. The behaviour pinned (`application`), every subject as `git log` shows it:

- `factory.application.recovery.RecoveryHandler.handle(event)`: a `crash` event is committed as `work item <id>: crash of stage <stage> recorded`, an `expired` one as `work item <id>: expiry of stage <stage> recorded`; when the expiry note opens a draft pull request, its number is committed on top as `work item <id>: pull request opened`.
- `factory.application.handlers.closed.ClosedHandler.handle(event)` at an approval stage: the close is committed as `work item <id>: close recorded`, the send-back on top as `work item <id>: sent back`.
- `factory.application.handlers.comments.CommentCopier.copy(snapshot, pull_request)`: `work item <id>: comments from the pull request`.
- `factory.application.handlers.reject.RejectHandler.handle(event)`: `work item <id>: stage <illegal stage> -> <stage before>, moved back`.

Tests (the tester writes them):

- `tests/application/test_recovery_subjects.py` builds on `tests/crash_support.py` as it is: `claim`, `expired_claim`, `open_pull_request`, `snapshot`, `crash_event`, `expired_event`, `handler`, `other_handler`, `Rerun` and `BRANCH`.
- `tests/application/handlers/test_handler_subjects.py` builds on the fixtures of `tests/application/handlers/conftest.py` as they are: `pull_request`, and `work_item`, a story at stage `doing` with that pull request, pushed to `work-item/F0001-S0001`.

Each test reads the subjects with `git.log("origin/work-item/F0001-S0001", since=<the commit named in the row>)` after a fetch, newest first. No earlier test changes.

## Acceptance criteria

1. The recovery's subjects (rows of one parametrized test; each since `claimed.start.commit`, the claim's stage-start commit):
   - `claim(boundaries, human, crashes=0, pull_request=open_pull_request(hosting))`, then `handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))`: exactly `["work item F0001-S0001: crash of stage doing recorded"]`.
   - `expired_claim(boundaries, human, clock, pull_request=open_pull_request(hosting))`, then `other_handler(boundaries, claimed, Rerun()).handle(expired_event(snapshot(boundaries)))`: exactly `["work item F0001-S0001: expiry of stage doing recorded"]`.
   - The same expiry without a pull request (`expired_claim(boundaries, human, clock)`): exactly `["work item F0001-S0001: pull request opened", "work item F0001-S0001: expiry of stage doing recorded"]`.
2. The comments' subject (one test): one human comment `Make the title shorter.` on `pull_request`, then `CommentCopier(boundaries).copy(work_item, pull_request)`; since `work_item.branch_commit`: exactly `["work item F0001-S0001: comments from the pull request"]`.
3. The send-back's subjects (one test): the human pushes `work_item.document` with its state at stage `approval` and `handed_over="approval"`; the pull request is made ready (`hosting.set_draft(pull_request, False)`) and closed by the human (`hosting.close_by_human(pull_request)`); then `ClosedHandler(boundaries, definition).handle(Event(kind="closed", work_item=<the snapshot fetched after the push>, remote_state="a" * 40))`. Since that snapshot's `branch_commit`: exactly `["work item F0001-S0001: sent back", "work item F0001-S0001: close recorded"]`.
4. The move-back's subject (one test): the human pushes `work_item.document` with its state at stage `approval`, an illegal change from `doing`; then `RejectHandler(boundaries).handle(Event(kind="reject", work_item=<the snapshot fetched after the push>, remote_state=<origin/main's commit>))`. Since that snapshot's `branch_commit`: exactly `["work item F0001-S0001: stage approval -> doing, moved back"]`.
5. `make check` stays green.
6. docs: none. These are the subjects the factory already writes, and this story changes none.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.application.handlers.recording import commit_subject
from factory.domain.post_texts import MOVED_BACK_MARKER

print(commit_subject("F0001-S0001", "crash of stage doing recorded"))
print(commit_subject("F0001-S0001", f"stage approval -> doing, {MOVED_BACK_MARKER}"))
EOF
```

Expect: two lines, `work item F0001-S0001: crash of stage doing recorded` and `work item F0001-S0001: stage approval -> doing, moved back`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete methods (RecoveryHandler.handle, ClosedHandler.handle, CommentCopier.copy, RejectHandler.handle), the exact subject of each, and the two test modules with the existing fixtures and support helpers they build on. No source change.
   Criteria: each is testable by one test function. Criterion 1 is rows of one parametrized test and covers both sides of "when the expiry note opens a draft pull request", with the extra commit and without it, and the crash and expiry subjects. Criteria 2 to 4 each give the exact expected subject list, in order, and the commit they are read since. Every subject the Interface states has a criterion. The Interface states no limit, validation or rejected input, so there is no failing side to cover. Criteria 5 and 6 are the closing ones.
   Smoke test: the command is runnable. It uses commit_subject and MOVED_BACK_MARKER, which the Interface's subjects imply. The Expect line gives two exact output lines that can be compared.
   Architecture: tests only, under tests/application/ as CLAUDE.md prescribes. They use real git and the fake hosting service, with no mocks of the code under test.
   Scope: within the feature's Scope, which lists these two modules for S0006. The 15 subjects match decision 8. The story is not in Out of scope, and it changes no earlier test.
4. factory: started tests as self.
5. tester: Wrote one test per criterion. Each test reads the branch's subjects with `git.log("origin/work-item/F0001-S0001", since=...)` after a fetch, newest first, and compares them with the exact list the criterion gives.

   - criterion 1: tests/application/test_recovery_subjects.py::test_the_recovery_commits_name_the_work_item_and_what_it_recorded (rows `crash`, `expiry`, `expiry-opening-a-pull-request`; each since `claimed.start.commit`)
   - criterion 2: tests/application/handlers/test_handler_subjects.py::test_the_copied_comments_are_committed_under_the_work_item_s_id
   - criterion 3: tests/application/handlers/test_handler_subjects.py::test_a_close_at_the_approval_commits_the_close_and_then_the_send_back
   - criterion 4: tests/application/handlers/test_handler_subjects.py::test_the_move_back_names_the_work_item_and_both_stages
   - criteria 5 and 6: no test (`make check`; docs: none)

   Files created: tests/application/test_recovery_subjects.py, tests/application/handlers/test_handler_subjects.py. They use `tests/crash_support.py` and the fixtures of `tests/application/handlers/conftest.py` and the root `definition` fixture unchanged. No earlier test changed and no shared helper moved.

   Modules the test run could not import: none. These tests pass now instead of failing first. That is expected: the Description says the code already writes these subjects and the coder has nothing to change. `make test` was green (40.5 s) and `make lint` is green. The type check was skipped, as this stage says.

   In criteria 3 and 4, the human's push is `work_item.document` with its state copied to `stage="approval"`: with `handed_over="approval"` for the close, and with `handed_over` left as `None` for the move-back. The snapshot is re-read from `origin/work-item/F0001-S0001` after that push, and its `branch_commit` is the commit the subjects are read since. In criterion 4, `remote_state` is the commit `origin/main` resolves to. Nothing open.

   `lint`: lint: green (0.0 s)
   `test`: test: green (38.8 s)
6. factory: started doing as self.
7. coder: Built nothing: no path changed. The Description and Interface say no module under `src/factory/` changes, because the code already writes these subjects. The tester's two modules, `tests/application/test_recovery_subjects.py` and `tests/application/handlers/test_handler_subjects.py`, already pass against the code as it is. I did not edit them.

   Main choice: I left the source alone and only confirmed it with `make check`, which ends with `check: green` (`test: green (40.3 s)`, coverage 99.14 %). I rejected touching `recovery.py` or the handlers, for example to pull the subject texts into constants. Nothing failed and nothing asked for it, so that would go beyond the work item's scope. The refactor step found no diff of mine to tidy.

   Noticed but did not touch: nothing new. The journal did not change the meaning of the task, so the Description stays as it is.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   Reviewed `git diff main...HEAD -- . ':!factory'`: two new test modules, no change under `src/`. The six tests in those two modules pass when run on their own (pytest, run by itself).
   - Criterion 1: `tests/application/test_recovery_subjects.py::test_the_recovery_commits_name_the_work_item_and_what_it_recorded`. Its rows are `crash`, `expiry` and `expiry-opening-a-pull-request`, and each compares the exact, ordered list of subjects since `claimed.start.commit`. That covers both sides of "when the expiry note opens a draft pull request".
   - Criteria 2 to 4: `tests/application/handlers/test_handler_subjects.py` has one test each. Each compares the exact subject list since the `branch_commit` the criterion names: the work item's own for the comments, and the snapshot re-read after the human's push to `approval` for the send-back and the move-back. The move-back's `remote_state` is origin/main's commit, as the criterion says.
   - Exact equality pins the work item's id and the stage words in every subject, which is what the mutants changed.
   - The Interface states no limit and no rejected input.
   - The tests use real git and the fake hosting service, and mock none of the code under test.
   - The helpers `_subjects` and `_push_at_approval` look like the private helpers in `tests/application/handlers/test_reject.py`. They are not copies of an existing shared helper.
   - The coder's `make check` was green (entry 7).
   - The description matches what was built: no source change. The docs criterion "none" holds.

   Earlier tests: none. `git diff --name-status main...HEAD` shows only added test files (status `A`).
10. factory: started docs as self.
11. documenter: Docs criterion is `none`, and the diff matches it: two new test modules (`tests/application/test_recovery_subjects.py`, `tests/application/handlers/test_handler_subjects.py`), no change under `src/`. I changed no file, so there is nothing to run and no `make check` (only documents could change).

    Cross-read against the diff and found current:
    - `docs/operator-guide.md`: the subjects `work item <id>: close recorded` (line 1311), `work item <id>: sent back` (line 1313) and `work item <id>: stage <to> -> <from>, moved back` (line 1365). In the move-back, `<to>` is the illegal stage and `<from>` the stage before it, which is the order the pinned test uses (`stage approval -> doing, moved back`).
    - `docs/project-guide/watching.md`: `commit_subject` and the `work item <id>: ` prefix on every handler commit (line 138), the close record (line 177) and the `moved back` marker (line 209).

    Nothing stale noticed that is unrelated. One gap I left alone: no document spells out the crash, expiry or `pull request opened` subjects of the recovery, or the `comments from the pull request` subject. The docs criterion says none, and the pinned tests now hold those subjects. No findings for the coder.

    `check`: check: green (not run again: passed on tree 562b1eb11f1c at 2026-10-20T02:14:27Z)
    `secrets`: secrets: green (0.1 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed with no findings. I ran the one command under `## Smoke test` exactly as written, from the repository root. It did not start a server.

    Command 1 (`uv run -q python -` with the heredoc that prints two `commit_subject` results):

    ```
    work item F0001-S0001: crash of stage doing recorded
    work item F0001-S0001: stage approval -> doing, moved back
    ```

    The exit status was 0.

    Met its `Expect:` line: yes. The command printed exactly two lines, and they are the two lines the `Expect:` line gives, in the same order.

    Against the acceptance criteria: the output contradicts none of them. Both lines have the form that criteria 1 and 4 pin: the crash subject, and the move-back subject with the illegal stage first and then the stage before it. The command does not exercise criteria 2 and 3 (the comments subject and the close and send-back subjects), but nothing in its output contradicts them. Criteria 5 and 6 (`make check` and docs: none) are not things a smoke test can contradict. I fixed nothing and changed no file.

    Findings: none.
