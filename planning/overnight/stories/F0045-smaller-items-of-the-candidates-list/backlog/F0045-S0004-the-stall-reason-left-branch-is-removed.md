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
