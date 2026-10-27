---
stage: smoke-test
blocked: null
round: 1
attempts: 1
crashes: 0
pull_request: 479
comments_read: [6433412562]
handed_over: null
claim:
  instance: vm
  stage: smoke-test
  started_at: '2026-10-27T04:44:33.790338Z'
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
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-27T04:12:49.949758Z'
  stage: tests
  run: 40105e3349de485796cf23e6a68f59ef
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-27T04:13:10.331617Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-27T04:19:13.707348Z'
  stage: doing
  run: 566e4bc75c624c30bf8e294532500293
- number: 11
  speaker: factory
  kind: stall
  at: '2026-10-27T04:19:14.004873Z'
  stage: doing
  run: 566e4bc75c624c30bf8e294532500293
  reason: check_red
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-27T04:19:36.254299Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-27T04:26:51.561824Z'
  stage: doing
  run: ce6ea1c891c5412190510aa4ddd8fc2e
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-27T04:27:11.846504Z'
  stage: review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-10-27T04:28:40.412281Z'
  stage: review
  run: f8272daaa3c343f2b86fec4b045b00a7
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-27T04:29:00.819010Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-10-27T04:29:16.711119Z'
  stage: doing
  run: b6265194cd314d5bba19bb069b5cc673
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-27T04:29:37.376206Z'
  stage: tests
- number: 19
  speaker: tester
  kind: result
  at: '2026-10-27T04:35:47.192318Z'
  stage: tests
  run: 78d17cdc405c45e786eb554df047de86
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-27T04:36:08.397870Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-10-27T04:42:17.208813Z'
  stage: doing
  run: fa0ef1e9a18042e6b8263669fd41cc9c
- number: 22
  speaker: factory
  kind: started
  at: '2026-10-27T04:42:37.623705Z'
  stage: review
- number: 23
  speaker: reviewer
  kind: result
  at: '2026-10-27T04:43:23.922007Z'
  stage: review
  run: ddff4e0b8c9f4fd1a4e11411cc759b93
- number: 24
  speaker: factory
  kind: started
  at: '2026-10-27T04:43:44.149758Z'
  stage: docs
- number: 25
  speaker: documenter
  kind: result
  at: '2026-10-27T04:44:13.506799Z'
  stage: docs
  run: 596961d254834d65b57ea2b70b7a4062
- number: 26
  speaker: factory
  kind: started
  at: '2026-10-27T04:44:33.790338Z'
  stage: smoke-test
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
8. tester: This story's work is the tester's alone, so I made the five changes in the Interface myself and added the guard tests for criteria 1 to 3. Because the changes are already in, the tests are green rather than red: `make test` ended `test: green (166.2 s)`, and one full `make check` ended `check: green`. After that run I renamed two private row functions in `tests/test_suite_held_once.py`. That module's pytest run then passed and `make lint` was green, but I did not run `make check` again.

   Criteria to tests:
   - criterion 1: `tests/test_suite_held_once.py::test_each_shared_helper_and_constant_is_held_once`, with new rows `vm-setup-helpers` (item 1), `contract-schemas` and `contract-login-helpers` (item 2) and `record-get-repo-public` (item 4). They reuse the module's own `_definers`, which counts plain and annotated assignments but not imports.
   - criterion 2: `tests/test_suite_leftovers.py::test_the_suite_s_smoke_test_moves_back_to_doing_or_docs`
   - criterion 3: `tests/test_suite_leftovers.py::test_the_preparer_s_test_of_its_parameters_is_one_plain_check_of_log`
   - criterion 4 (`make check`) and criterion 5 (docs) need no test.

   Renamed helpers, old name → new name:
   - `_in_order` → `in_order` and `_lines_with` → `lines_with`, from `tests/test_vm_setup_text.py`, `tests/test_vm_setup_caches.py` and `tests/test_vm_setup_idle_shutdown.py`, moved to `tests/vm_support.py` with docstrings. `test_vm_setup_caches.py` had only `_in_order`.
   - `_committed` → `committed` and `_values` → `values` in `tests/contract_login_support.py`, which now imports `SCHEMAS` from `tests/contract_support.py` (its own `SCHEMAS` is gone).
   - `_record_get_repo` → `record_get_repo` in `tests/wiring_support.py`.
   - In `tests/test_suite_held_once.py`: the row function `_record_get_repo_once` → `_get_repo_recorder_once` (its id `record-get-repo` is unchanged, and it now reads the new name). I also named the new row function `_get_repo_recorder_public`. Both renames are needed because the smoke test's `grep 'def _record_get_repo'` would otherwise match these functions.

   Changed modules:
   - Item 1, under the standing leave: `tests/vm_support.py`, `tests/test_vm_setup_text.py`, `tests/test_vm_setup_caches.py`, `tests/test_vm_setup_idle_shutdown.py`.
   - Item 2, under the standing leave: `tests/contract_login_support.py`, `tests/domain/test_contract_login.py`, and also `tests/domain/test_contract_provider_limit.py`, which imports the same two helpers but which the Interface does not name.
   - Item 3, under the human's leave: `tests/git_support.py`, where the smoke test now reads `next: [approval, doing, docs]`. No earlier test failed because of the new entry, so no other test changed.
   - Item 4, under the human's leave: `tests/wiring_support.py`, `tests/entry/test_wiring_boundaries.py`, `tests/entry/test_wiring_one_environment.py`, `tests/test_suite_held_once.py`. I also added the criterion 1 rows to the existing parametrized test there, so I would not copy its `_definers` helper (the story keeps every other helper where it is).
   - Item 5, under the human's leave: `tests/application/test_checkout_preparer.py`. `test_the_preparer_takes_only_the_git_and_the_settings` is now a plain test without fixtures that asserts `"log" not in inspect.signature(CheckoutPreparer.__init__).parameters`. `_takes_no_log` and the repeated rows are gone.

   Files created: `tests/test_suite_leftovers.py`.

   Modules the test run could not import: none.

   Both smoke-test blocks give their expected output: three `0` lines, then `153 passed in 4.34s`. My run of the pytest line also included `tests/test_suite_leftovers.py`.

   Open for the docs stage: criterion 5, the *Shared test helpers* lines in `docs/project-guide/README.md`.

   `lint`: lint: green (0.2 s)
   `test`: test: green (166.2 s)
9. factory: started doing as vm.
10. coder: I built nothing, because this story has no code to write. The Interface names no path under `src/factory/`, `vm/`, `template/` or `claude/`. The tester's entry 8 already made all five changes under `tests/` and added the guard tests for criteria 1 to 3. Those tests pass against the code as it stands.

    What I did: I ran `make check` on the committed state, with no changes of my own, and it ended `check: green` (`test: green (165.9 s)`, coverage 99.57 %). The tester had not re-run the full check after their last rename in `tests/test_suite_held_once.py`, so this run confirms it.

    Main choice: I left the working tree untouched and send the story to review. The alternative I rejected was to make some change under `src/` to have something to show; nothing in the story asks for one. Following the step that compares my own diff, I have no diff, so I had nothing to refactor. No journal entry changed the meaning of the task. The human's answers (entry 4) only added criteria, and intake already wrote them into the Description.

    Noticed, not touched:
    - The tester also changed `tests/domain/test_contract_provider_limit.py`. It imports the renamed `committed` and `values`, but the Interface does not name it. The change is a follow-on of the rename and falls under the standing leave, so the reviewer may want to confirm it.
    - Criterion 5 (the *Shared test helpers* lines in `docs/project-guide/README.md`) is still open for the docs stage.
11. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
    src/factory/entry/check_documents.py               33      1     10      1    95%   51
    src/factory/entry/check_duplicates.py              44      1      6      1    96%   66
    src/factory/entry/check_story.py                   92      1     18      1    98%   161
    src/factory/entry/contract.py                      28      1      6      1    94%   41
    src/factory/entry/health.py                        33      1     10      1    95%   48
    src/factory/entry/run.py                           76      1      6      1    98%   186
    src/factory/entry/watch.py                         52      1      6      1    97%   87
    -------------------------------------------------------------------------------------------
    TOTAL                                            9227     24   1834     24    99%

    120 files skipped due to complete coverage.
    Required test coverage of 90.0% reached. Total coverage: 99.57%
    ======================================================================================= short test summary info ========================================================================================
    FAILED tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_process-group] - OSError: [Errno 22] Invalid argument
    make: *** [Makefile:84: test] Error 1
12. factory: started doing as vm.
13. coder: I built nothing, because there is no code to write. The Interface names no path under `src/factory/`, `vm/`, `template/` or `claude/`. The tester's entry 8 already made all five changes under `tests/` and added the guard tests, and I left the working tree as it was. This round only had to deal with the factory's stall in entry 11.

    The stall: under the factory's `make check`, `tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_process-group]` failed with `OSError: [Errno 22] Invalid argument`. This story did not touch that test. It also did not touch the module it covers, `src/factory/adapters/process.py`, or its support modules; the story's diff is `tests/` only and the tester changed none of those files.
    - I ran `make check` again on the committed state with no changes. It ended `test: green (165.8 s)` and `check: green`, with coverage at 99.57 %.
    - I then ran that test on its own: all six of its rows passed (`6 passed in 60.04s`).

    So the test failed once, under the factory's `make check`, and has passed twice since. The project guide asks for the `E` lines and the `file:line` of such a failure. I cannot quote them: entry 11 holds only pytest's short summary line, and none of my runs reproduced the failure. It looks like an environmental or timing fault in the process-group kill path, not something this story caused. I did not change it, because it is unrelated code (R13). If it comes back, it deserves a story of its own that captures the full `--tb=short` output.

    Main choice: send the story to review without changes. I rejected two alternatives. One was to touch `process.py` or the test to harden it against EINVAL, which is outside this story and is a test I did not write. The other was to end with `question`, but the check is green and the failure did not repeat. I had no diff, so there was nothing to refactor, and no journal entry changed the meaning of the task.

    Noticed, not touched (as in entry 10):
    - The tester also changed `tests/domain/test_contract_provider_limit.py`, which imports the renamed `committed` and `values`, although the Interface does not name it.
    - Criterion 5 (the *Shared test helpers* lines in `docs/project-guide/README.md`) is still open for the docs stage.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 41 known, 0 gone
14. factory: started review as vm.
15. reviewer: Review of round 0. I read the work item and `git diff main...HEAD -- . ':!factory'` (14 files, all under `tests/`), and also `tests/test_suite_held_once.py`, `tests/function_support.py` and `tests/search_support.py`, to check the helpers the new tests use or copy. Groups 1 to 3 pass. Group 1: the rows of criterion 1 cover all three items (`in_order`/`lines_with` only in `vm_support.py` and no `_` variants; `SCHEMAS` only in `contract_support.py`, because `_defined` counts `Assign`/`AnnAssign` and not imports; `committed`/`values` only in `contract_login_support.py` and no `_` variants; `record_get_repo` only in `wiring_support.py` and no `_record_get_repo`). Criterion 2 parses `PIPELINE_YAML` through `RuamelPipelineDefinitionReader`. Criterion 3 checks that there is no parametrize, that `args` is empty, that the `inspect.signature` assert is there, and that both clone rows are kept. The factory's `make check` after the coder was green (entry 13). Groups 2 and 3: `tests/` only, no markers. Group 4 fails:

    1. `tests/test_suite_leftovers.py:13`: `_function` is a second copy, line for line, of `_function` in `tests/test_suite_held_once.py:33`, and `tests/function_support.py::functions` already reads a module's top-level functions with `ast`. This story exists to say once what the tests share. Fix: select the function by name from `function_support.functions(...)`. Or add a by-name helper to `tests/function_support.py` and have `test_suite_held_once.py` use it as well, under the standing leave.
    2. `tests/test_suite_held_once.py:80-86`: the new row `record-get-repo-public` (`_get_repo_recorder_public`) repeats the whole assertion of row `record-get-repo` (`_get_repo_recorder_once`). Criterion 1 asks for one row per item. Fix: add `assert _definers("_record_get_repo") == []` to `_get_repo_recorder_once` (its id `record-get-repo` stays) and drop `_get_repo_recorder_public` and its row.
    3. `tests/test_suite_held_once.py:96-102,167-168`: item 2 is split over two rows (`contract-schemas` and `contract-login-helpers`), but criterion 1 asks for one row per item 1, 2 and 4. Fix: merge `_schemas_once` into `_contract_login_helpers_once` as one row for item 2, and keep the id `contract-login-helpers`.

    Group 5 (not reached as a failing group) looked sound: the Description and the docs criterion match what was built.

    Earlier tests (changed under a leave):
    - `tests/application/test_checkout_preparer.py`: the human's leave, entry 4 (item 5).
    - `tests/contract_login_support.py`: the standing leave (item 2: the shared `SCHEMAS` is used and the shared helpers are renamed).
    - `tests/domain/test_contract_login.py`: the standing leave (item 2: it imports the renamed helpers, and its test and what it checks are unchanged).
    - `tests/domain/test_contract_provider_limit.py`: the standing leave (a follow-on of item 2's rename, which the Interface does not name; its test and what it checks are unchanged).
    - `tests/entry/test_wiring_boundaries.py`: the human's leave, entry 4 (item 4).
    - `tests/entry/test_wiring_one_environment.py`: the human's leave, entry 4 (item 4).
    - `tests/git_support.py`: the human's leave, entry 4 (item 3).
    - `tests/test_suite_held_once.py`: the human's leave, entry 4 (item 4: the row `record-get-repo` reads the new name, and its row function is renamed with the same id). The added rows need no leave.
    - `tests/test_vm_setup_caches.py`: the standing leave (item 1).
    - `tests/test_vm_setup_idle_shutdown.py`: the standing leave (item 1).
    - `tests/test_vm_setup_text.py`: the standing leave (item 1).
    - `tests/vm_support.py`: the standing leave (item 1: the shared place; helpers added, nothing else changed).
    - `tests/wiring_support.py`: the human's leave, entry 4 (item 4).
16. factory: started doing as vm.
17. coder: Round 1: all three of the reviewer's findings (entry 15) are about tests. I don't edit tests, so I changed no code and am sending the story back to the tester with exactly these three changes:

    1. **The copied `_function` helper.** In `tests/test_suite_leftovers.py:13`, `_function` is a line-for-line copy of `_function` in `tests/test_suite_held_once.py:33`. The fix is to pick the function by name from `tests/function_support.py::functions`. Alternatively, add a by-name helper to `tests/function_support.py` and have both modules use it; the standing leave in `CLAUDE.md` (*Tests*) covers that move.
    2. **A repeated row for item 4.** In `tests/test_suite_held_once.py`, add `assert _definers("_record_get_repo") == []` to `_get_repo_recorder_once` and keep its id, `record-get-repo`. Then remove `_get_repo_recorder_public` and its row, `record-get-repo-public`.
    3. **Item 2 split over two rows.** In `tests/test_suite_held_once.py`, merge `_schemas_once` into `_contract_login_helpers_once`, so item 2 is one row with the id `contract-login-helpers`. Remove the `contract-schemas` row.

    Main choice: I end with `tests` and leave the working tree untouched. I rejected two alternatives. One was to make these edits myself, which would break the rule that coders never edit tests. The other was to end with `question`. These are this story's own tests, and the copied helper falls under the standing leave, so there is nothing to ask the human.

    No journal entry changed what the task means, so the Description stays as it is. I have no diff, so there was nothing to refactor.

    Noticed but not touched: the earlier one-off failure of `tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_process-group]` (`OSError: [Errno 22]`, entry 11) has no recorded traceback. If it comes back, it needs a story of its own. Criterion 5 is still open for the docs stage.
18. factory: started tests as vm.
19. tester: Round 1: this is the test change named in the coder's entry 17, which carries the reviewer's three findings from entry 15. I made those three changes and nothing else. All the tests are in this story's own modules, so no earlier test changed.

    1. **`tests/test_suite_leftovers.py`: removed the copied helper.** I deleted `_function`, which was a line-for-line copy of the one in `tests/test_suite_held_once.py`. `test_the_preparer_s_test_of_its_parameters_is_one_plain_check_of_log` now builds a dictionary, by name, of the functions that `tests/function_support.py::functions` returns, and picks its two tests from it. I chose the reviewer's first option, so `tests/function_support.py` is unchanged. I did not choose to add a by-name helper there and change `test_suite_held_once.py` to use it: that is a larger move and the finding does not need it.
    2. **`tests/test_suite_held_once.py`: item 4 is one row.** `_get_repo_recorder_once`, with the id `record-get-repo`, now also asserts `_definers("_record_get_repo") == []`. I removed `_get_repo_recorder_public` and its row `record-get-repo-public`.
    3. **`tests/test_suite_held_once.py`: item 2 is one row.** The `SCHEMAS` assertion from `_schemas_once` is now in `_contract_login_helpers_once`, with the id `contract-login-helpers`. I removed `_schemas_once` and its row `contract-schemas`.

    Criteria to tests, as they stand now:
    - criterion 1: `tests/test_suite_held_once.py::test_each_shared_helper_and_constant_is_held_once`, rows `vm-setup-helpers` (item 1), `contract-login-helpers` (item 2) and `record-get-repo` (item 4)
    - criterion 2: `tests/test_suite_leftovers.py::test_the_suite_s_smoke_test_moves_back_to_doing_or_docs`
    - criterion 3: `tests/test_suite_leftovers.py::test_the_preparer_s_test_of_its_parameters_is_one_plain_check_of_log`
    - criteria 4 and 5: these need no test.

    Files changed: `tests/test_suite_held_once.py` and `tests/test_suite_leftovers.py`. Files created: none in this round.

    Modules the test run could not import: none.

    - `make test`: test: green (166.1 s)
    - `make lint`: lint: green (0.2 s)

    Still open: criterion 5 is for the docs stage.

    `lint`: lint: green (0.2 s)
    `test`: test: green (165.9 s)
20. factory: started doing as vm.
21. coder: Round 1, after the tester's entry 19. I changed nothing, so there is nothing new to list under what I built. The Interface names no path under `src/factory/`, `vm/`, `template/` or `claude/`. The reviewer's three findings in entry 15 were all about tests. The tester made those changes in `tests/test_suite_leftovers.py` and `tests/test_suite_held_once.py`.

    What I did: I ran `make check` on the committed state with no changes of my own. It ended `test: green (165.7 s)` and `check: green`, with coverage at 99.57 %. The tester ran only `make test` and `make lint` after this round's changes, so this full run confirms them.

    Main choice: I left the working tree untouched and sent the story to review. The alternative I rejected was to end with `tests` or `question`. All three findings are addressed in the tests, and nothing in the journal asks for code. I had no diff, so there was nothing to refactor. No journal entry changed what the task means, so the Description stays as it is.

    Noticed but not touched:
    - `tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_process-group]` failed once, with `OSError: [Errno 22]` (entry 11), and has not failed again. There is still no traceback on record. If it comes back, it needs a story of its own.
    - Criterion 5 (the *Shared test helpers* lines in `docs/project-guide/README.md`) is still open for the docs stage.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 41 known, 0 gone
22. factory: started review as vm.
23. reviewer: Review of round 1. I read the work item and `git diff main...HEAD -- . ':!factory'`: 14 files, all under `tests/`. I also read `tests/test_suite_held_once.py` (`_defined`, `_definers`, `_function`), `tests/function_support.py`, `SCHEMAS` in `tests/contract_support.py` and the rows of `test_the_preparer_clones_only_a_missing_checkout_and_checks_none`.

    All three findings from entry 15 are fixed:
    - `tests/test_suite_leftovers.py` no longer has the copy of `_function`. It now picks its two tests by name from `function_support.functions`.
    - Item 4 is one row (`record-get-repo`). It asserts both that `record_get_repo` is defined only in `wiring_support.py` and that nothing defines `_record_get_repo`.
    - Item 2 is one row (`contract-login-helpers`). It asserts that `SCHEMAS` is assigned only in `contract_support.py`, and that `committed`/`values` are defined only in `contract_login_support.py`, with no underscore variants anywhere.

    Group 1 (acceptance criteria):
    - Criterion 1: the rows are `vm-setup-helpers`, `contract-login-helpers` and `record-get-repo`. `_defined` counts top-level `FunctionDef`, `Assign` and `AnnAssign` and does not count imports, as journal entry 4 settled.
    - Criterion 2: the test parses `PIPELINE_YAML` through `RuamelPipelineDefinitionReader` and compares `next` to `["approval", "doing", "docs"]`.
    - Criterion 3: the test checks that there is no `parametrize` decorator and that `args` is empty. It checks that the body holds the `inspect.signature(CheckoutPreparer.__init__)` assertion on `'log'`. It checks that `missing-is-cloned` and `group-writable-git-is-kept` are kept.
    - The factory's `make check` after the coder was green (entry 21: `check: green`, `duplicates: 0 new`).

    Groups 2 and 3: `tests/` only, no layer is touched, and nothing silences a check. Group 4: the new `_row_ids` copies no existing helper (a search of `tests/` for an id-keyword reader found only this one). The new support helpers carry docstrings. Group 5: the Description and the Interface match what was built. Criterion 5 still names the *Shared test helpers* lines the documenter must update.

    no findings

    Earlier tests (changed under a leave):
    - `tests/application/test_checkout_preparer.py`: the human's leave, entry 4 (item 5).
    - `tests/contract_login_support.py`: the standing leave (item 2: uses the shared `SCHEMAS`; the shared helpers are renamed).
    - `tests/domain/test_contract_login.py`: the standing leave (item 2: imports the renamed helpers; its test and what it checks are unchanged).
    - `tests/domain/test_contract_provider_limit.py`: the standing leave (follows from item 2's rename; its test and what it checks are unchanged).
    - `tests/entry/test_wiring_boundaries.py`: the human's leave, entry 4 (item 4).
    - `tests/entry/test_wiring_one_environment.py`: the human's leave, entry 4 (item 4).
    - `tests/git_support.py`: the human's leave, entry 4 (item 3).
    - `tests/test_suite_held_once.py`: the human's leave, entry 4 (item 4: the row `record-get-repo` reads the new name and keeps its id). The added rows `vm-setup-helpers` and `contract-login-helpers` add cases and change no earlier row.
    - `tests/test_vm_setup_caches.py`: the standing leave (item 1).
    - `tests/test_vm_setup_idle_shutdown.py`: the standing leave (item 1).
    - `tests/test_vm_setup_text.py`: the standing leave (item 1).
    - `tests/vm_support.py`: the standing leave (item 1: the shared place; helpers added, nothing else changed).
    - `tests/wiring_support.py`: the human's leave, entry 4 (item 4).
24. factory: started docs as vm.
25. documenter: Docs round 1, criterion 5. I changed one file, `docs/project-guide/README.md`, in *Shared test helpers*, so the lines match the moves and renames:
    - `vm_support.py` now also lists `in_order` and `lines_with`, which the three `vm/setup.sh` text modules share (`test_vm_setup_caches.py` uses only `in_order`).
    - `contract_login_support.py` now names `committed` and `values` (no underscore) and says its schema folder is `SCHEMAS` of `contract_support.py`, assigned nowhere else.
    - `contract_support.py` now lists `SCHEMAS`, the committed schema folder.
    - `wiring_support.py` now says `record_get_repo`. I removed the note that it keeps its underscore.

    I cross-read these against the `tests/` diff (14 files, all under `tests/`) and against the helpers' definitions in `tests/vm_support.py` and `tests/contract_login_support.py`, and found them current:
    - `git_support.py` line of the same section: its helper list is unchanged. Item 3 changed only the pipeline definition text, and the line does not describe it.
    - `docs/operator-guide.md`, `docs/decisions.md` and `README.md`: the criterion says none, and nothing in the diff touches what they describe.

    I changed only documents, so I did not run `make check`. The factory's run after this stage decides.

    I found no stale text outside this story. I have no findings for the coder. The one-off `OSError: [Errno 22]` in `tests/adapters/test_process_session.py` (journal entries 11 and 13) is still unexplained and was not touched.

    `check`: check: green (not run again: passed on tree 19637f912c33 at 2026-10-27T04:39:20Z)
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok
26. factory: started smoke-test as vm.
