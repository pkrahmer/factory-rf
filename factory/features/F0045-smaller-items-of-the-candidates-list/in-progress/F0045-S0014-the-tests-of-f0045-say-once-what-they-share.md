---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-10-27T03:59:29.867300Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-27T03:59:29.860853Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-27T03:59:29.867300Z'
  stage: intake
---

# The tests of F0045 say once what they share

<!-- proposed by feature acceptance of 2026-10-27; refine before starting -->

## Description

F0045's reviewers noted under `Notes:` what the feature's own tests left behind, each a remark that was not a finding in its story (F0045-A0001, check 4): `_in_order` and `_lines_with`, the same two helpers in three modules that read `vm/setup.sh` (S0002, S0009); a second `SCHEMAS` path in `tests/contract_login_support.py` beside the one of `tests/contract_support.py` (S0004, S0010); the pipeline definition of `tests/git_support.py`, whose smoke test still has `next: [approval, doing]` while every shipped definition has `[approval, doing, docs]` since S0001; `_record_get_repo`, shared by two modules through `tests/wiring_support.py` but still named as a private helper (S0011); and two rows of `test_the_preparer_takes_only_the_git_and_the_settings` that repeat rows of the earlier test beside it (S0011). This story clears that list, the tester's work alone, as S0011 cleared F0044's. Every test keeps what it checks. What stays: every behaviour of the factory; every other helper; the guards `tests/test_shared_*.py` and `tests/test_suite_held_once.py`, whose one row on `_record_get_repo` follows the rename.

## Interface

None under `src/factory/`, `vm/`, `template/` or `claude/`. The tester changes `tests/` only (items 1 and 2 under the standing leave of `CLAUDE.md`, *Tests*; items 3 to 5 need the human's leave, to be given when this story is refined):

1. `_in_order` and `_lines_with` of `tests/test_vm_setup_text.py`, `tests/test_vm_setup_caches.py` and `tests/test_vm_setup_idle_shutdown.py` (identical bodies on 2026-10-27) move to `tests/vm_support.py` as `in_order` and `lines_with`; the three modules import them.
2. `SCHEMAS` of `tests/contract_login_support.py` goes; the module uses `SCHEMAS` of `tests/contract_support.py`. Its `_committed` and `_values`, which `tests/domain/test_contract_login.py` imports, lose their leading underscore.
3. `tests/git_support.py`: the smoke test's line of its pipeline definition becomes `smoke-test: {role: smoke-tester, next: [approval, doing, docs], round_cap: 3}`; a test that then fails only because of the new entry is named in the tester's entry and changed to the new definition, its name and what it checks kept.
4. `_record_get_repo` of `tests/wiring_support.py` becomes `record_get_repo`; `tests/entry/test_wiring_boundaries.py` and `tests/entry/test_wiring_one_environment.py` import it under that name, and the row `record-get-repo` of `tests/test_suite_held_once.py` reads the new name.
5. `tests/application/test_checkout_preparer.py::test_the_preparer_takes_only_the_git_and_the_settings`: its rows `missing-is-cloned` and `existing-is-kept`, which repeat rows of `test_the_preparer_clones_only_a_missing_checkout_and_checks_none` in the same module, go; it becomes a plain test of the same name that checks that `log` is no parameter of `CheckoutPreparer.__init__`.

The tester's entry names each changed module and, for every renamed helper, its old and its new name.

## Acceptance criteria

1. Each item is held once (rows of one parametrized test over the files under `tests/`, read with `ast`, one row per item 1, 2 and 4): exactly one module defines `in_order` and exactly one `lines_with`, and it is `tests/vm_support.py`, and no module defines `_in_order` or `_lines_with`; exactly one module assigns `SCHEMAS`, and it is `tests/contract_support.py`; exactly one module defines `record_get_repo`, and it is `tests/wiring_support.py`, and no module defines `_record_get_repo`.
2. The suite's definition (one test reading `tests/git_support.py`'s definition through `RuamelPipelineDefinitionReader`): its stage `smoke-test` has `next == ["approval", "doing", "docs"]`, as `template/factory/pipeline.yml` has.
3. The preparer's test (one test reading `tests/application/test_checkout_preparer.py` with `ast`): `test_the_preparer_takes_only_the_git_and_the_settings` carries no `pytest.mark.parametrize` and takes no fixture, and `test_the_preparer_clones_only_a_missing_checkout_and_checks_none` keeps its rows `missing-is-cloned` and `group-writable-git-is-kept`.
4. `make check` stays green.
5. docs: `docs/project-guide/README.md`, *Shared test helpers*: the lines of `vm_support.py`, `contract_support.py`, `contract_login_support.py` and `wiring_support.py` name what they offer after the moves and renames. `docs/operator-guide.md`, `docs/decisions.md`, `README.md`: none.

## Smoke test

```bash
grep -rlE 'def _in_order|def _lines_with|def _record_get_repo' tests | wc -l
grep -c '^SCHEMAS' tests/contract_login_support.py
```
Expect: two lines: `0`; `0`

```bash
uv run pytest tests/test_suite_held_once.py tests/application/test_checkout_preparer.py tests/test_vm_setup_text.py -p no:cacheprovider 2>&1 | tail -1
```
Expect: one line that ends `passed in <n>s` and names no failure

## Journal

1. 2026-10-27 human: created.
2. factory: started intake as vm.
