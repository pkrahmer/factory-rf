---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 479
comments_read: [6433412562]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-10-27T04:02:10.224197Z'
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-27T03:59:51.158586Z'
  stage: intake
  run: 153b14ea7101425b9e350068fdae7512
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-27T04:01:09.315165Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-27T04:01:27.258333Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-27T04:01:49.327757Z'
  stage: intake
  run: 0dd47be2432945cd8283fb5d91b242d6
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-27T04:02:10.224197Z'
  stage: tests
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

1. Each item is held once (rows of one parametrized test over the files under `tests/`, read with `ast`, one row per item 1, 2 and 4; plain and annotated assignments count as assigning, imports do not): exactly one module defines `in_order` and exactly one `lines_with`, and it is `tests/vm_support.py`, and no module defines `_in_order` or `_lines_with`; exactly one module assigns `SCHEMAS`, and it is `tests/contract_support.py`; exactly one module defines `committed` and exactly one `values`, and it is `tests/contract_login_support.py`, and no module defines `_committed` or `_values`; exactly one module defines `record_get_repo`, and it is `tests/wiring_support.py`, and no module defines `_record_get_repo`.
2. The suite's definition (one test reading `tests/git_support.py`'s definition through `RuamelPipelineDefinitionReader`): its stage `smoke-test` has `next == ["approval", "doing", "docs"]`, as `template/factory/pipeline.yml` has.
3. The preparer's test (one test reading `tests/application/test_checkout_preparer.py` with `ast`): `test_the_preparer_takes_only_the_git_and_the_settings` carries no `pytest.mark.parametrize` and takes no fixture, its body asserts that `log` is not among the parameters of `CheckoutPreparer.__init__` (through `inspect.signature`), and `test_the_preparer_clones_only_a_missing_checkout_and_checks_none` keeps its rows `missing-is-cloned` and `group-writable-git-is-kept`.
4. `make check` stays green.
5. docs: `docs/project-guide/README.md`, *Shared test helpers*: the lines of `vm_support.py`, `contract_support.py`, `contract_login_support.py` and `wiring_support.py` name what they offer after the moves and renames. `docs/operator-guide.md`, `docs/decisions.md`, `README.md`: none.

## Smoke test

```bash
grep -rlE 'def _in_order|def _lines_with|def _record_get_repo' tests | wc -l
grep -c '^SCHEMAS' tests/contract_login_support.py
grep -cE 'def _committed|def _values' tests/contract_login_support.py
```
Expect: three lines: `0`; `0`; `0`

```bash
uv run pytest tests/test_suite_held_once.py tests/application/test_checkout_preparer.py tests/test_vm_setup_text.py -p no:cacheprovider 2>&1 | tail -1
```
Expect: one line that ends `passed in <n>s` and names no failure

## Journal

1. 2026-10-27 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. I judged the story and have four questions. I changed nothing.

   1. **The leave for items 3, 4 and 5 is missing.** The Interface says items 3 to 5 "need the human's leave, to be given when this story is refined". Item 3 is `tests/git_support.py` plus any test that fails on the new `next`. Item 4 is `tests/wiring_support.py`, `tests/entry/test_wiring_boundaries.py`, `tests/entry/test_wiring_one_environment.py` and `tests/test_suite_held_once.py`. Item 5 is `tests/application/test_checkout_preparer.py`. All of these are tests other stories wrote. The journal holds no such leave, and the feature's decisions 21 to 31 give leave only for S0001 to S0011. Please say in a journal entry whether you give the leave for items 3, 4 and 5 and name the modules it covers. I would choose to give it, with item 3's knock-on tests left open to be named by the tester, as the story says.

   2. **Item 2's rename has no criterion.** The Interface says `_committed` and `_values` of `tests/contract_login_support.py` lose their underscore, and `tests/domain/test_contract_login.py` imports them. Criterion 1 covers only `SCHEMAS` for item 2. Two testers could read the rename two ways. Should criterion 1 gain a row saying exactly one module defines `committed` and one defines `values` (both `tests/contract_login_support.py`), and none defines `_committed` or `_values`? I would choose to add it. The smoke test could also gain a matching grep.

   3. **Criterion 3 does not test item 5's behaviour.** Item 5 says the plain test "checks that `log` is no parameter of `CheckoutPreparer.__init__`". Criterion 3 asks only that the test carries no `parametrize` and takes no fixture. It does not require the test to inspect `__init__`'s parameters. Should the criterion also say that the test's body asserts `log` is not among `CheckoutPreparer.__init__`'s parameters, for example through `inspect.signature`, read with `ast`? I would choose to add it.

   4. **Criterion 1's wording leaves the "ast" test unclear for `SCHEMAS`.** It says "exactly one module assigns `SCHEMAS`". Should plain assignments, annotated assignments and imports of the name count? As I read it, imports do not count as assignments. Please confirm, or state the rule.

   The other checks found nothing to ask. I checked the pytest configuration: `addopts` sets only `-q`, and the smoke commands pass none, so `tail -1` shows `N passed in <n>s`. Item 1 and the `SCHEMAS` row sit within the standing leave. All five items are within F0045's scope and are the tester's `tests/` paths.
4. 2026-10-27 human: 1. The human's leave is given for items 3, 4 and 5, for exactly these modules: item 3, `tests/git_support.py` and every earlier test that fails only because of the new `next` (the tester names each one); item 4, `tests/wiring_support.py`, `tests/entry/test_wiring_boundaries.py`, `tests/entry/test_wiring_one_environment.py` and `tests/test_suite_held_once.py`; item 5, `tests/application/test_checkout_preparer.py`. Each test keeps its name and what it checks.
   2. Yes, add that row: exactly one module defines `committed` and one defines `values` (both `tests/contract_login_support.py`), and none defines `_committed` or `_values`; the matching grep in the smoke test is welcome.
   3. Yes: the test's body asserts that `log` is not among `CheckoutPreparer.__init__`'s parameters (`inspect.signature`), and criterion 3 reads that with `ast`.
   4. Confirmed: plain and annotated assignments count, imports do not.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: Items 1 to 5 name concrete modules, files and old and new names under `tests/`; nothing under `src/`. The leave for items 3 to 5 is in journal entry 4 (the human), naming the modules.
   - Criteria: Carried in from journal entry 4. Criterion 1 gains a row for `committed` and `values` of `tests/contract_login_support.py` (answer 2) and states that plain and annotated assignments count and imports do not (answer 4). Criterion 3 now also requires that the test's body asserts `log` is not among the `CheckoutPreparer.__init__` parameters, through `inspect.signature` read with `ast` (answer 3). Every rule has its failing side: the old names are absent, and the clone rows and the parametrize ban are checked. Each criterion is one test function.
   - Smoke test: The commands are runnable. The first block gains a grep for `def _committed|def _values` (answer 2), so its Expect reads three lines, `0`; `0`; `0`. The pytest line passes no `-q` (`addopts` already sets it), so `tail -1` shows `N passed in <n>s`.
   - Architecture: `tests/` only. Helpers move to support modules, as `CLAUDE.md` (*Tests*) asks. No layer is touched.
   - Scope: All five items are F0045's own tests' leftovers from A0001 and are not in "Out of scope". The description's meaning is unchanged, so it was not rewritten.
7. factory: started tests as vm.
