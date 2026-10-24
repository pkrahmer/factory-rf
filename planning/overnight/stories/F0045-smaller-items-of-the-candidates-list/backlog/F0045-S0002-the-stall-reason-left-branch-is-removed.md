# The stall reason left_branch is removed

## Description

Since v1's port, the factory checks after every agent run that its own checkout is still on the work item's branch, and stalls the stage as `left_branch` ("the agent left the work item's branch") when it is not. On the VM of v1.2 the agent works on the dataset in a throwaway container and never reaches the host's checkout (F0042, F0044), so the check can no longer fire; F0044 kept the reason because it names no layer (its decision 14) and left its removal to this feature with the records contract's next major (its decision 29 (b)). This story removes the reason: the value `left_branch` of `StallReason`, its stall sentence, and the branch check after the agent. Removing a value of a contract model narrows the work item and acceptance states, so the records contract rises from F0044's `3.0` to `4.0` and the schemas are generated again (decision 13 of `feature.md`). What stays: every other stall reason and its sentence; the stall service, which still brings the checkout back to the work item's branch before it takes and commits; `Git.status`; the restore at the start of a tick.

## Interface

`factory.domain.journal.StallReason` (`domain`) loses `"left_branch"`; the other values keep their order:

```python
StallReason = Literal[
    "died", "time_limit", "budget", "no_result", "decision_not_allowed",
    "form_invalid", "check_red", "merge_conflict", "provider_limit",
]
```

(F0044-S0006 removed `nested_repository`; the list is the one on `main` after F0044 less `left_branch`.)

`factory.domain.post_texts` (`domain`): the entry of `left_branch` in the stall sentences goes.

`factory.application.stage` (`application`): `AfterAgent`'s early stall no longer compares `boundaries.git.status().branch` with the work item's branch; it reads only the run's own end (`stall_reason_of(result)`), as before for every other reason.

`factory.domain.contract` (`domain`): `RECORDS_CONTRACT = "4.0"`; `src/factory/contract/*.schema.json` regenerated with `uv run python -m factory.entry.contract` (`work-item-state` and `acceptance-state` lose the value; every file's `x-records-contract` is `4.0`).

Tests (the tester writes and changes them; the leave is decision 17 of `feature.md`): new tests at the tester's choice, for example `tests/application/test_no_left_branch.py`. Earlier tests:

- Deleted: `tests/application/test_after_agent.py::test_a_checkout_left_on_another_branch_stalls_as_left_branch`; `tests/application/test_stall_edges.py::test_a_stall_after_the_agent_left_drops_its_commit_on_the_branch`, with the helpers `_left_branch` and `CommitThenLeaveRuntime` when no remaining test reads them.
- `tests/application/test_stall_edges.py::test_a_stall_without_a_detail_says_only_its_reason`: its row `left-branch` goes, the row `merge-conflict` stays.
- `tests/domain/test_stall_texts.py::test_each_stall_cause_is_its_sentence_alone_or_with_the_detail`: the row of `left_branch` goes from `SENTENCES`.
- `tests/application/test_stalls.py::test_an_agent_that_left_the_branch_is_brought_back_and_its_other_branch_kept` and the row `checkout-back-on-the-branch` of `tests/application/test_stall_environment.py::test_the_take_runs_after_the_checkout_is_back_and_before_the_sidecar_is_written`: the stall they make has the reason `died`; each keeps its name and what it checks of the checkout, the branch and the take.
- `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` and `tests/domain/test_contract_provider_limit.py::test_the_committed_schemas_list_provider_limit_at_version_1_2` read the version `4.0`; each keeps its name.

## Acceptance criteria

1. The removed value (rows of one parametrized test): `"left_branch"` is not in `typing.get_args(StallReason)`; the stall sentences of `factory.domain.post_texts` have no entry for it; every value left in `StallReason` still has its sentence (a value without one fails the row).
2. The early stall reads the run alone (rows of one parametrized test through `StageRunner` on the `boundaries` fixture, a tester's stage): a scripted run that ends `died` stalls as `died`; one that reaches its time limit stalls as `time_limit`; a completed run that writes `tests/test_new.py` and decides `doing` moves the work item to `doing` with no stall entry, and its result commit holds `tests/test_new.py`.
3. The branch check is gone (one test reading the source of `factory.application.stage` with `ast`): the module calls no method `status` (on `main` before this story its one call was the branch check), so no stage stalls because of the host checkout's branch.
4. The stall still brings the checkout back (the existing `tests/application/test_stalls.py::test_an_agent_that_left_the_branch_is_brought_back_and_its_other_branch_kept`, with the reason `died`): after the stall the checkout is on the work item's branch at the stall commit, and the branch `elsewhere` still exists.
5. The contract (rows of one parametrized test): `RECORDS_CONTRACT == "4.0"`; each of the five committed schemas under `src/factory/contract/` holds `"x-records-contract": "4.0"` and equals `contract_schema` of its entry; no committed schema names `left_branch`.
6. The source (one test reading `src/factory`): no module holds the string `left_branch` or `the agent left the work item's branch`.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`, `## A stall: the stall note`: the reason "the agent left the work item's branch" goes from the list of reasons; `## The records contract`: the version `4.0` and why it rose (the stall reason `left_branch` removed, after F0044's `2.0` and `3.0`). `docs/project-guide/stages.md`, `## Stalls`, *The reasons*: `left_branch` goes; `## After the agent run`: the step *Branch* goes and the steps after it are numbered on. `docs/decisions.md`: the entry "The records carry generated JSON Schemas under `src/factory/contract/`" gains one line: "`4.0` removed the stall reason `left_branch`, which no agent can cause on the dataset (v1.2 F0045-S0002)." `README.md`: none.

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
