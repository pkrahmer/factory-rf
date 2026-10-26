---
stage: review
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 469
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-10-26T21:23:25.487439Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T21:05:18.111068Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T21:05:18.116694Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T21:05:41.566210Z'
  stage: intake
  run: e94f0bb8ed354aa0901be07d0cd93116
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-26T21:06:01.875283Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-26T21:13:13.729595Z'
  stage: tests
  run: bbfe2a14c75942d08fda25bffdffbb95
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-26T21:13:34.632643Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-26T21:16:50.952418Z'
  stage: doing
  run: 10b2f27bb8154b0c9d0a6421da90697a
- number: 8
  speaker: factory
  kind: stall
  at: '2026-10-26T21:16:51.287328Z'
  stage: doing
  run: 10b2f27bb8154b0c9d0a6421da90697a
  reason: check_red
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-26T21:17:15.304181Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-26T21:23:04.531828Z'
  stage: doing
  run: 096af63ddca94f7fb5edc06539a6ee14
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-26T21:23:25.487439Z'
  stage: review
---

# The stall reason left_branch is removed

## Description

Since v1's port, the factory checks after every agent run that its own checkout is still on the work item's branch, and stalls the stage as `left_branch` ("the agent left the work item's branch") when it is not. On the VM of v1.2 the agent works on the dataset in a throwaway container and never reaches the host's checkout (F0042, F0044), so the check can no longer fire; F0044 kept the reason because it names no layer and left its removal to this feature with the records contract's next major (F0044's decision 29 (b), the human's answers). This story removes the reason: the value `left_branch` of `StallReason`, its stall sentence, and the branch check after the agent. Removing a value of a contract model narrows the work item and acceptance states, a change that can break a reader, so the records contract rises from F0044's `3.0` to `4.0` and the schemas are generated again (decision 13 of `feature.md`). What stays: every other stall reason and its sentence; the stall service, which still brings the checkout back to the work item's branch before it takes and commits; `Git.status`; the restore at the start of a tick.

## Interface

`factory.domain.journal.StallReason` (`domain`) loses `"left_branch"`; the other values keep their order.

`factory.domain.post_texts` (`domain`): the entry of `left_branch` in the stall sentences goes.

`factory.application.stage` (`application`): `AfterAgent`'s early stall no longer compares `boundaries.git.status().branch` with the work item's branch; it reads only the run's own end (`stall_reason_of(result)`), as before for every other reason.

`factory.domain.contract` (`domain`): `RECORDS_CONTRACT = "4.0"`; `src/factory/contract/*.schema.json` regenerated with `uv run python -m factory.entry.contract` (`work-item-state` and `acceptance-state` lose the value; every file's `x-records-contract` is `4.0`).

Tests (the tester writes and changes them; the leave is decision 24 of `feature.md`): new tests at the tester's choice, for example `tests/domain/test_contract_version_4.py` and `tests/application/test_no_branch_check.py`. Earlier tests, each kept test keeping its name and what it checks:

- Deleted: `tests/application/test_after_agent.py::test_a_checkout_left_on_another_branch_stalls_as_left_branch`, with the class `SwitchingRuntime`, the keyword `switching` of `_launch` and the constant `ELSEWHERE` of that module when no remaining test there reads them.
- `tests/application/test_stall_edges.py::test_a_stall_without_a_detail_says_only_its_reason`: its row `left-branch` goes, the row `merge-conflict` stays; the helpers `_left_branch` and `CommitThenLeaveRuntime` and the constant `ELSEWHERE` go when no remaining test reads them, and the module's docstring no longer names a commit before the agent left.
- `tests/domain/test_stall_texts.py::test_each_stall_cause_is_its_sentence_alone_or_with_the_detail`: the row of `left_branch` goes from `SENTENCES`.
- `tests/application/test_stall_environment.py::test_the_take_runs_after_the_checkout_is_back_and_before_the_sidecar_is_written`, its row `checkout-back-on-the-branch`: the stall it makes has the reason `died` instead of `left_branch`; it keeps what it checks of the checkout's branch and head.
- `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version`, `tests/domain/test_contract_provider_limit.py::test_the_committed_schemas_list_provider_limit_at_version_1_2`, `tests/domain/test_contract_version_2.py::test_the_records_contract_is_at_version_2_without_tool_paths` and `tests/domain/test_contract_version_3.py::test_the_records_contract_is_at_version_3_without_nested_repository`: they read the version `4.0` where they read `3.0`; each keeps its name and its other assertions.

## Acceptance criteria

1. The removed value (rows of one parametrized test): `"left_branch"` is not in `typing.get_args(StallReason)`; the stall sentences of `factory.domain.post_texts` have no entry for it; every value left in `StallReason` still has its sentence (a value without one fails its row).
2. The early stall reads the run alone (rows of one parametrized test through `AfterAgent` on the `boundaries` fixture, a tester's stage): a scripted run that ends `died` stalls as `died`; one that ends `time_limit` stalls as `time_limit`; a completed run that decides `doing` gives an aftermath with the decision `doing` and no stall.
3. The branch check is gone (one test reading the source of `factory.application.stage` with `ast`): the module calls no method named `status` (on `main` before this story its one call is the branch check).
4. The stall still brings the checkout back (the existing row `checkout-back-on-the-branch` of `tests/application/test_stall_environment.py::test_the_take_runs_after_the_checkout_is_back_and_before_the_sidecar_is_written`, with the reason `died`): when the take runs, the checkout is on the work item's branch at the stage start's commit.
5. The contract (rows of one parametrized test): `RECORDS_CONTRACT == "4.0"`; each of the five committed schemas under `src/factory/contract/` holds `"x-records-contract": "4.0"` and equals `contract_schema` of its entry; no committed schema holds `left_branch`.
6. The source (one test reading `src/factory`): no `*.py` or `*.json` file under it holds `left_branch` or `the agent left the work item's branch`.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`, `## A stall: the stall note`: the reason "the agent left the work item's branch" goes from the list of reasons, if it is there; `## The records contract`, *The version*: `4.0`, and why it rose (the stall reason `left_branch` removed, after `2.0` and `3.0` of F0044). `docs/project-guide/stages.md`, `## Stalls`: `left_branch` goes from the list of `StallReason`; `## After the agent run`: the step *Branch* goes and the steps after it are numbered on. `docs/decisions.md`: the entry "The records carry generated JSON Schemas under `src/factory/contract/`" (the one that names `2.0` and `3.0`) gains one line: "The records contract's version is `4.0` since F0045-S0004, which removed the stall reason `left_branch`; no agent can cause it on the dataset." `README.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
import typing
from factory.domain.contract import RECORDS_CONTRACT
from factory.domain.journal import StallReason
print("left_branch" in typing.get_args(StallReason), RECORDS_CONTRACT)
EOF
grep -l 'left_branch' src/factory/contract/*.schema.json | wc -l
```
Expect: two lines: `False 4.0`; `0`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: concrete. It names `StallReason` in `factory.domain.journal`, the sentence entry in `factory.domain.post_texts`, `AfterAgent` in `factory.application.stage`, `RECORDS_CONTRACT = "4.0"` and the regeneration command. I checked it against `src` on this branch. `journal.py:53` and `post_texts.py:33` hold `left_branch`. The branch check is at `stage.py:238-239`, and it is the only `.status(` call in that module; the other calls are in `stalls.py`, `claims.py` and `tick.py`. The Interface keeps the stall service's use of `status`, so those calls stay. It lists each earlier test it changes by name and decision 24 of `feature.md` gives the human's leave. It states no behaviour that lacks a criterion.
   - Criteria: each is testable by one test function. 1 covers both sides of the removed value in rows: the value is gone, the sentence is gone, and every remaining value still has a sentence. 2 gives rows for `died`, `time_limit` and a completed run that decides `doing` with no stall. 3 is an `ast` check for no `status` call. 4 is the existing row that the Interface changes to `died`. 5 covers the version and the five schemas, and checks that none holds `left_branch`. 6 is a source search. 7 and 8 are the closing criteria. No new rule is introduced, so there is no failing side to test.
   - Smoke test: runnable. It uses `uv run python -` and a `grep -l ... | wc -l`, and neither runs pytest, so the `-q` rule does not apply. The `Expect:` line gives the exact output (`False 4.0`, then `0`), which can be checked.
   - Architecture: the changes sit in the layers they belong to (domain for the reason, sentence and contract; application for `AfterAgent`). The contract schemas are regenerated through `factory.entry.contract`, as `CLAUDE.md` requires. The stall service, `Git.status` and the restore stay as they are.
   - Scope: this matches S0004 in `feature.md` and decision 13, and nothing in its "Out of scope" is touched. The test changes are covered by the human's leave in decision 24.
4. factory: started tests as vm.
5. tester: I wrote the new tests and changed the earlier ones as the Interface lists them, under the leave in decision 24 of `feature.md`. One run of `make test` was red for the right reasons: `RECORDS_CONTRACT` and the committed schemas are still at `3.0`, `left_branch` is still in the schemas, the sentences and the source, and `stage.py` still calls `status`. The tail showed the `test_contract_version_4` failures. `make lint` is green. I skipped the type check, as this stage says.

   Criterion → test:
   - criterion 1: `tests/domain/test_stall_reason_removed.py::test_left_branch_is_no_stall_reason_and_every_other_keeps_its_sentence`. Its rows are `not-a-reason` (`get_args(StallReason)`) and `no-sentence` (no `left_branch` string literal in `factory.domain.post_texts`, read with `ast`, because the sentence table is private). Every remaining `StallReason` value then has a row that calls `stall_cause(reason)` and expects a non-empty sentence, so a missing entry fails that row.
   - criterion 2: `tests/application/test_no_branch_check.py::test_the_early_stall_reads_only_the_runs_own_end`, with rows `died`, `time-limit` and `completed-doing`. It runs through `AfterAgent` on the `boundaries` fixture in stage `tests`. These rows already pass on today's code, because nothing in them moves the checkout. The branch check's removal is pinned by criterion 3.
   - criterion 3: `tests/application/test_no_branch_check.py::test_the_stage_module_calls_no_status`.
   - criterion 4: `tests/application/test_stall_environment.py::test_the_take_runs_after_the_checkout_is_back_and_before_the_sidecar_is_written[checkout-back-on-the-branch]`. Its reason is now `died` instead of `left_branch`; the branch and head assertions are unchanged.
   - criterion 5: `tests/domain/test_contract_version_4.py::test_the_records_contract_is_at_version_4_without_left_branch`, with rows `version`, one per contract entry (committed schema holds `4.0` and equals `contract_schema`) and `no-left-branch`.
   - criterion 6: `tests/test_left_branch_removed.py::test_no_source_or_schema_file_names_left_branch`.
   - criteria 7 and 8: no test (`make check`; docs).

   Files created: `tests/domain/test_stall_reason_removed.py`, `tests/domain/test_contract_version_4.py`, `tests/application/test_no_branch_check.py`, `tests/test_left_branch_removed.py`.

   Earlier test files changed:
   - `tests/application/test_after_agent.py`: deleted `test_a_checkout_left_on_another_branch_stalls_as_left_branch`, along with `SwitchingRuntime`, the `switching` keyword of `_launch`, `ELSEWHERE`, and the imports only they used (`replace`, `ObservingRuntime`, `AgentRunRequest`). The module docstring no longer says "the branch tested".
   - `tests/application/test_stall_edges.py`: removed the `left-branch` row of `test_a_stall_without_a_detail_says_only_its_reason`, along with `_left_branch`, `CommitThenLeaveRuntime`, `ELSEWHERE` and the imports only they used. The docstring no longer names a commit before the agent left.
   - `tests/domain/test_stall_texts.py`: removed the `left_branch` row from `SENTENCES`.
   - `tests/application/test_stall_environment.py`: the row change for criterion 4.
   - `tests/domain/test_contract.py`, `test_contract_provider_limit.py`, `test_contract_version_2.py` and `test_contract_version_3.py`: `3.0` → `4.0` in their version assertions only. Names and the other assertions are unchanged. The module docstring of `test_contract_version_3.py` still says "version 3.0", because it describes that story.

   `SwitchingRuntime` in `tests/stall_support.py` stays, since the stall-environment row still uses it.

   Modules the runner could not import: none. Every new module imports names that already exist, and the failures are wrong results.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/domain/test_contract_version_4.py::test_the_records_contract_is_at_version_4_without_left_branch[no-left-branch] - AssertionError: assert ['acceptance-....schema.json'] == []
6. factory: started doing as vm.
7. coder: I removed the stall reason `left_branch` as the Interface describes. `make check` is green (coverage 99.56 %).

   What changed:
   - `src/factory/domain/journal.py`: `"left_branch"` is gone from `StallReason`. The other values keep their order.
   - `src/factory/domain/post_texts.py`: its entry in `_STALL_SENTENCES` is gone.
   - `src/factory/application/stage.py`: `AfterAgent._early_stall` no longer compares `git.status().branch` with the work item's branch. It reads only `stall_reason_of(launched.result)`.
   - `src/factory/domain/contract.py`: `RECORDS_CONTRACT = "4.0"`.
   - `src/factory/contract/*.schema.json`: all five regenerated with `uv run python -m factory.entry.contract`, not edited by hand. `work-item-state` and `acceptance-state` lose the value, and every file now carries `x-records-contract` `4.0`.

   Main choice: I removed the check outright and kept `_early_stall` as a method, so its call site stays as it is. I rejected the alternative of keeping a `status` call for some softer check (a log line or warning): the description says the check cannot fire on the dataset, and criterion 3 asks for no `status` call in the module. I also rejected turning `_early_stall` into a module-level function now that it no longer reads `self._boundaries`. That would be a restructuring beyond this story.

   Refactor pass: I read the diff and found nothing to change.

   Noticed, not touched:
   - The comment at `src/factory/application/stalls.py:112` ("Whatever the agent left on the other branch is dropped") belongs to the stall service's restore. The description keeps that restore, so the comment stays.
   - The docs criterion (operator guide, `stages.md`, `decisions.md`) is the documenter's.

   No journal entry changed the meaning of the task.
8. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
   Bytecode compiled 4164 files in 104ms
   sync: green (0.1 s)
   Bytecode compiled 4164 files in 74ms
   All checks passed!
   Bytecode compiled 4164 files in 70ms
   lint: green (0.2 s)
   Bytecode compiled 4164 files in 76ms
   make: *** [Makefile:38: types] Error 139
9. factory: started doing as vm.
10. coder: I re-ran the stage after the stall in entry 8. The work from entry 7 is already committed on the branch and I changed nothing. `make check` is green this time: `check: green`, `test: green (156.8 s)`, coverage 99.56 %.

       Why the stall happened: the red check was `make types`, which died with `make: *** [Makefile:38: types] Error 139`. Exit 139 is a segfault in the mypy process, not a type error. This time, on the same tree, `types` passed. I take the earlier failure as a crash of the tool on the machine, not a fault in the diff. If it happens again, the mypy run inside the check container is the place to look. Nothing in this story touches it.

       What is built (unchanged from entry 7), in `src/factory/`:
       - `domain/journal.py`: `"left_branch"` is gone from `StallReason`.
       - `domain/post_texts.py`: its stall sentence is gone.
       - `application/stage.py`: `AfterAgent._early_stall` no longer has the branch comparison through `git.status()`.
       - `domain/contract.py`: `RECORDS_CONTRACT = "4.0"`.
       - `contract/*.schema.json`: regenerated with `uv run python -m factory.entry.contract`.

       Main choice (unchanged): I removed the check outright. I rejected keeping a softer `status`-based warning, because the check cannot fire on the dataset and criterion 3 forbids the call. I also left `_early_stall` as a method rather than moving it to module level, since that move is a restructuring beyond this story.

       Refactor pass: I read the diff again and found nothing to change.

       Noticed, not touched:
       - The comment at `src/factory/application/stalls.py:112` belongs to the stall service's restore, which this story keeps.
       - The docs criterion is the documenter's.

       No journal entry changed the meaning of the task.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
11. factory: started review as vm.
