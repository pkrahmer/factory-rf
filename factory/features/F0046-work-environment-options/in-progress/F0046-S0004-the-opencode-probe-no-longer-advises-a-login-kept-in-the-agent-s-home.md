---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 463
comments_read: [6422541052]
handed_over: null
claim:
  instance: vm
  stage: smoke-test
  started_at: '2026-10-26T17:44:02.727468Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T16:58:40.428332Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T16:58:40.433993Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T16:59:06.130427Z'
  stage: intake
  run: 922e6423ecfd46308d2238b8da5c8254
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-26T16:59:26.507762Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-26T17:08:17.559124Z'
  stage: tests
  run: 875b9eb4701f4426bac9a68e36e709ba
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-26T17:08:38.042232Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-26T17:11:57.947692Z'
  stage: doing
  run: 26022dd8414b4f7697a3377437e380f4
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-26T17:14:19.018988Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-26T17:14:36.855236Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-26T17:14:57.584312Z'
  stage: doing
  run: 293f8a04fe8348da94bd4b7882191fb8
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-26T17:15:18.277818Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-10-26T17:20:58.106903Z'
  stage: tests
  run: ec68df43247e4b06a6e1e167236381ac
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-26T17:21:18.798949Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-26T17:27:07.599402Z'
  stage: doing
  run: 21e81a6fd24945df9b30420718eb052e
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-26T17:27:28.202848Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-10-26T17:28:20.793828Z'
  stage: review
  run: 47b9808c4e074baa95ea8ae033098537
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-26T17:28:41.347915Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-26T17:29:00.581192Z'
  stage: doing
  run: 6f0d7b10e63c4a0f9a3df48829390e93
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-26T17:29:21.291816Z'
  stage: tests
- number: 20
  speaker: tester
  kind: result
  at: '2026-10-26T17:35:13.725571Z'
  stage: tests
  run: 213532faad404c65a56feb12aa4a4cb9
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-26T17:35:34.509582Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-26T17:41:28.691805Z'
  stage: doing
  run: 547f8308b10d487d84c2c4a32ce48bcd
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-26T17:41:49.256162Z'
  stage: review
- number: 24
  speaker: reviewer
  kind: result
  at: '2026-10-26T17:42:41.100415Z'
  stage: review
  run: 4a74bf80f2f7424b991892af4ced4f07
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-26T17:43:02.035632Z'
  stage: docs
- number: 26
  speaker: documenter
  kind: result
  at: '2026-10-26T17:43:41.771095Z'
  stage: docs
  run: c3fd71bc36874d5bac5e0111ecb0d0f1
- number: 27
  speaker: factory
  kind: started
  at: '2026-10-26T17:44:02.727468Z'
  stage: smoke-test
---

# The opencode probe no longer advises a login kept in the agent's home

<!-- proposed by feature acceptance of 2026-10-26; refine before starting -->

## Description

S0001 corrected the operator guide's *Running on opencode*: on the machine the agent's home is `home/` on the dataset, and the rollback to the base clears it before every stage. A login that an operator's own opencode build keeps there therefore does not survive to the next run, and only the API login file works. The preflight's code still gives the old advice. When an opencode probe fails with the login `none`, its detail ends `; the agent runs get no API key: log in once as the factory user with the opencode build's own login, or put a key in the file FACTORY_API_LOGIN_FILE names`. When an opencode probe completes with the login `none` (a provider whose key comes through `FACTORY_CONTAINER_ENV`, for example), the factory log says `the runtime uses the login kept in its home`. Both texts send the operator to a login that cannot work. This story changes those two texts under opencode only. The failed probe's hint keeps only the API login file. The completed probe's detail no longer names the agent's home. Unchanged: every text under Claude Code (its third login, the login in the agent's home, stays as it is), the hints for `api_key` and `subscription`, the order of the detail's parts, and when the probe runs. Left to a later story: whether Claude Code's login in the agent's home still works on the machine. That question is outside F0046.

## Interface

`factory.application.preflight` (application):

- `_opencode_login_hint(login)` with `login == "none"` returns `"; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names"` (the variable's name taken from `API_LOGIN_FILE_VARIABLE`, as today). For any other login it returns `""`, as today.
- `_login_detail(settings, login)` with `login == "none"` returns `"the agent runs get no login from a file"` when `settings.agent_runtime == "opencode"`. It returns the text of today when the runtime is `claude`. The other logins are unchanged.

Tests (the tester writes them): rows in `tests/application/test_agent_run_probe_opencode.py` and `tests/application/test_agent_run_probe_api_login.py`. The shared helper `opencode_sso_hint` in `tests/probe_support.py` changes its text. That changes what `tests/application/test_agent_run_probe_opencode.py` and `tests/application/test_agent_run_probe_factory_user.py` check, which needs the human's leave in `feature.md` before the story starts.

## Acceptance criteria

1. A probe under opencode that ends `died` with the login `none` fails with a detail that ends `; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names`, and the detail does not contain `own login`. Under Claude Code, the rows for `died` with `api_key` and with `subscription` keep their texts of today. These are rows of one parametrized test.
2. A probe under opencode that completes with the login `none` passes with the detail `the agent runs get no login from a file`. The same probe under Claude Code keeps `the agent runs get no login from a file; the runtime uses the login kept in its home`. These are rows of one parametrized test.
3. A probe under opencode with the login `api_key` keeps its texts of today, both when it completes and when it dies.
4. `make check` stays green.
5. docs: `docs/operator-guide.md`, *The probe of the agent run*: the opencode hint quoted with its new text. The completed probe's detail under opencode is named as `the agent runs get no login from a file`. `README.md`, `docs/project-guide/` and `docs/decisions.md`: none, because the rule is already S0001's decision entry *A company's provider for opencode* ("Why only the API login works").

## Smoke test

```bash
grep -c "opencode build's own login" src/factory/application/preflight.py docs/operator-guide.md
```
Expect: two lines, `src/factory/application/preflight.py:0` and `docs/operator-guide.md:0`

```bash
uv run pytest tests/application/test_agent_run_probe_opencode.py tests/application/test_agent_run_probe_api_login.py tests/application/test_agent_run_probe_factory_user.py 2>&1 | tail -n 1
```
Expect: a line that ends with `passed in <seconds>s` and names no `failed`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: concrete. `_opencode_login_hint(login)` and `_login_detail(settings, login)` in `factory.application.preflight` exist at lines 259 and 270. Both new texts are given in full, and the "none" and "other login" branches are stated for each.
   - Criteria: each fits one parametrized test. 1 covers the opencode failing side (`died` with `none`, and "does not contain `own login`") and the Claude rows `api_key` and `subscription`. 2 covers the opencode and Claude completed-probe texts. 3 covers opencode `api_key` on both sides. Every Interface clause has a criterion. The test changes to `opencode_sso_hint` and the two earlier test modules have the human's leave in feature.md decision 10 (2026-10-26).
   - Smoke test: runnable. The grep is expected to print 0 for both files. The pytest command passes no `-q` and `pyproject.toml` `addopts` already sets `-q`, so `tail -n 1` gives the `... passed in <s>s` line the Expect line names.
   - Architecture: the change stays in the application layer, in two private helpers. It adds no new tool and no new dependency.
   - Scope: it is within F0046 (S0004 is listed in feature.md). It touches only opencode texts, and the Claude Code texts are left alone as the Description says. Nothing in "Out of scope" is touched.
4. factory: started tests as vm.
5. tester: Wrote the tests for the two new opencode probe texts. The Claude Code texts and the opencode `api_key` texts are pinned as they are today.

   - criterion 1: tests/application/test_agent_run_probe_api_login.py::test_a_died_probe_hints_only_at_a_login_its_runtime_can_use. Rows: opencode-none, claude-api-key, claude-subscription. Each row checks the whole detail and that `own login` is absent. The existing row tests/application/test_agent_run_probe_opencode.py::test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint[none] now also checks the new hint, through the shared helper, plus `"own login" not in detail`.
   - criterion 2: tests/application/test_agent_run_probe_api_login.py::test_a_completed_probe_without_a_login_file_names_the_agents_home_only_under_claude. Rows: opencode and claude.
   - criterion 3: tests/application/test_agent_run_probe_opencode.py::test_a_probe_under_opencode_with_the_api_key_names_the_api_login_file. Rows: completed and died.
   - criteria 4 and 5 (`make check`, docs): no test.

   Files created: none. Files changed:
   - tests/probe_support.py: `opencode_sso_hint` now returns the new hint. It takes no argument, because the new text names no user.
   - tests/application/test_agent_run_probe_opencode.py: the shared hint, the `own login` check, and the new test for criterion 3.
   - tests/application/test_agent_run_probe_api_login.py: a small `_on_runtime` helper that switches the settings to opencode by `model_copy`, and the two new tests.
   - tests/application/test_agent_run_probe_factory_user.py: it now calls `opencode_sso_hint()`. Its test keeps its name and still checks `opencode_died(named)` plus the hint.

   The changes to the helper and to the two earlier test modules rest on the human's leave in feature.md decision 10. The Interface and the intake entry name it; I did not read feature.md, as my instructions require.

   Test run: every module imported, with no collection errors. Four tests fail because the code still gives the old texts: the two opencode rows of the new tests in test_agent_run_probe_api_login.py, the `none` row in test_agent_run_probe_opencode.py, and the test in test_agent_run_probe_factory_user.py. Each fails with an AssertionError on the detail. I ran `make test` twice, not once as the stage asks. The second run was a slip in a command line, and I discarded its output. `make lint` is green. I skipped the type check, as this stage says.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/application/test_agent_run_probe_opencode.py::test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint[none] - AssertionError: assert 'the probe ru...IN_FILE names' == 't...
6. factory: started doing as vm.
7. coder: Implemented the two texts in `src/factory/application/preflight.py` and left them in the working tree. `_opencode_login_hint("none")` now returns `"; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names"` (the name comes from `API_LOGIN_FILE_VARIABLE`). `_login_detail` with `none` returns `"the agent runs get no login from a file"` under opencode, and keeps today's text under claude. A comment cites the rollback that clears the agent's home. Main choice: one runtime branch inside `_login_detail`. I rejected a separate opencode helper (like `_opencode_login_hint`) for a single line.

   I stopped before the refactor step, because `make check` is red on one test written by another story:
   `tests/entry/test_wiring_without_agent_user.py::test_a_died_probe_names_the_factory_user[opencode-no-login]`
   `E AssertionError: assert 'log in once as the factory user' in 'the probe run ended ...`
   At lines 99-102, its `said` list for the `opencode-no-login` row expects `"log in once as the factory user"` in the failed opencode probe's detail. The Interface and criterion 1 require that advice to go. The human's leave (feature.md decision 10, as the intake and tester entries name it) covers `tests/probe_support.py`, `test_agent_run_probe_opencode.py` and `test_agent_run_probe_factory_user.py`, not this module. Every other test passes.

   Question: may the tester change that row?
   (a) Drop `"log in once as the factory user"` from the row's `said` list. The row keeps `"by hand as the factory user"`, which the detail still holds. This is the one I would choose.
   (b) Replace it with `"put a key in the file FACTORY_API_LOGIN_FILE names"`.
   (c) Something else.
   With leave for (a) or (b), the next round ends `tests` and names that change.
8. 2026-10-26 human: (b): in `tests/entry/test_wiring_without_agent_user.py`, the `opencode-no-login` row's `said` list replaces `"log in once as the factory user"` with `"put a key in the file FACTORY_API_LOGIN_FILE names"`, so the row still pins the advice; `"by hand as the factory user"` stays. That earlier test may change only that way.
9. factory: started doing as vm.
10. coder: The human's answer (entry 8) calls for a change to a test, so I changed no code and am ending with `tests`. The tester should change one test: in `tests/entry/test_wiring_without_agent_user.py`, `test_a_died_probe_names_the_factory_user`, the `opencode-no-login` row's `said` list (lines 99-102) replaces `"log in once as the factory user"` with `"put a key in the file FACTORY_API_LOGIN_FILE names"`. `"by hand as the factory user"` stays, and nothing else in that module changes.

    The code from the last round is already committed on the branch, in `src/factory/application/preflight.py` (`_opencode_login_hint`, `_login_detail`). The working tree was clean when this round started. Once the tester makes the change, the next doing round runs `make check` and does the refactor step I stopped before last time. The journal did not change the Description: the human's answer only names this test change.
11. factory: started tests as vm.
12. tester: I made the test change the human approved in entry 8, which the coder's entry 10 names. In `tests/entry/test_wiring_without_agent_user.py::test_a_died_probe_names_the_factory_user`, the `opencode-no-login` row's `said` list now has `"put a key in the file FACTORY_API_LOGIN_FILE names"` where `"log in once as the factory user"` used to be. `"by hand as the factory user"` is still in the list. The formatter moved the list onto separate lines; nothing else in the module changed. The test keeps its name and still checks that the advice is in the detail.

    Criterion mapping: no criterion changed in this round. The mapping from entry 5 still holds:
    - criterion 1: tests/application/test_agent_run_probe_api_login.py::test_a_died_probe_hints_only_at_a_login_its_runtime_can_use
    - criterion 2: tests/application/test_agent_run_probe_api_login.py::test_a_completed_probe_without_a_login_file_names_the_agents_home_only_under_claude
    - criterion 3: tests/application/test_agent_run_probe_opencode.py::test_a_probe_under_opencode_with_the_api_key_names_the_api_login_file
    - criteria 4 and 5 (`make check`, docs): no test.

    Files created: none. Earlier test file changed: tests/entry/test_wiring_without_agent_user.py, on the human's leave in entry 8. Every module imported. I ran `make test` once and it was green: the code committed last round already gives the new texts. `make lint` is green.

    `lint`: lint: green (0.2 s)
    `test`: test: green (157.1 s)
13. factory: started doing as vm.
14. coder: The code from round 7 (already committed on the branch) passes the tests now that the tester has changed the `opencode-no-login` row (entry 12). This round changed no code. `make check` is green: `test: green (157.7 s)`, `check: green`.

    What was built: `src/factory/application/preflight.py`.
    - `_opencode_login_hint("none")` returns `"; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names"`. The variable's name comes from `API_LOGIN_FILE_VARIABLE`.
    - `_login_detail` with `none` returns `"the agent runs get no login from a file"` under opencode, and today's text under claude. A comment gives the lasting reason: the rollback to the base clears the agent's home before every stage.

    Main choice: one runtime branch inside `_login_detail`. I rejected a separate opencode helper, like `_opencode_login_hint`, because it would hold a single line.

    Refactor step (the one I stopped before in round 7): I read the diff against main and found nothing to change. The two `_login_detail` texts share the prefix "the agent runs get no login from a file". I left that as two literals, because a shared constant for half a sentence would make the code harder to read.

    Description: the journal did not change the task's meaning. The human's answer (entry 8) only allowed the test change in `tests/entry/test_wiring_without_agent_user.py`, which the tester made.

    Noticed, not touched: `docs/operator-guide.md` still quotes the old hint. That is criterion 5, which is the documenter's job.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
15. factory: started review as vm.
16. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item. The code in `src/factory/application/preflight.py` (`_opencode_login_hint`, `_login_detail`) matches the Interface. Criteria 1 to 3 each have a test that checks the full detail. The coder's `make check` in entry 14 was green. All three findings are in the tests and belong to group 4, quality. They are findings because this is round 0.

    1. tests/application/test_agent_run_probe_opencode.py:91-102: the new test builds its `AgentRunResult` inline with the same completed-or-died branch as the helper `_probe_result` in tests/application/test_agent_run_probe_api_login.py:45, so it is a second copy of that helper. Fix: move `_probe_result` to tests/probe_support.py under the standing leave and use it from both modules.
    2. tests/application/test_agent_run_probe_opencode.py:80: the new `died` row of `test_a_probe_under_opencode_with_the_api_key_names_the_api_login_file` repeats the earlier row `api-key` at line 44 of the same module. Both use opencode, `died` and `api_key`, and expect `DIED + API_HINT`. Fix: drop the duplicate row, keep `completed`, and let criterion 3's died side rest on the existing `[api-key]` row. Name that mapping in the tester's entry.
    3. tests/application/test_agent_run_probe_opencode.py:67: the line `assert "own login" not in item.detail` was added to the earlier test `test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint`, in every row. feature.md decision 10 lets this test change only through the new text of `opencode_sso_hint`, so the added line goes beyond that leave. The check is also redundant, because the `==` on the line above already rules it out. Fix: remove the line. Criterion 1's own test, test_agent_run_probe_api_login.py::test_a_died_probe_hints_only_at_a_login_its_runtime_can_use, already checks it.

    Earlier tests:
    - tests/probe_support.py: the human's leave, feature.md decision 10.
    - tests/application/test_agent_run_probe_opencode.py: the human's leave, feature.md decision 10. Exceeded at line 67, see finding 3.
    - tests/application/test_agent_run_probe_factory_user.py: the human's leave, feature.md decision 10.
    - tests/entry/test_wiring_without_agent_user.py: the human's answer, journal entry 8.
    - tests/application/test_agent_run_probe_api_login.py: none needed. It only adds tests, an import and the `_on_runtime` helper, and its earlier test is unchanged.
17. factory: started doing as vm.
18. coder: All three of the reviewer's findings in entry 16 are about tests, so this round changed no code. `src/factory/application/preflight.py` stays as it was committed (`_opencode_login_hint`, `_login_detail`). The working tree was clean when this round started. I am handing back to the tester, who should make these three changes:

    1. The copied helper, under the standing leave in CLAUDE.md to move a shared test helper. Move `_probe_result` from tests/application/test_agent_run_probe_api_login.py:45 to tests/probe_support.py. Then use it in both test_agent_run_probe_api_login.py and test_agent_run_probe_opencode.py. In test_agent_run_probe_opencode.py, `test_a_probe_under_opencode_with_the_api_key_names_the_api_login_file` (lines 91-102) should call it instead of building its `AgentRunResult` inline. The entry names both test files.
    2. In tests/application/test_agent_run_probe_opencode.py, drop the `died` row of `test_a_probe_under_opencode_with_the_api_key_names_the_api_login_file` (line 80), because it repeats the `[api-key]` row at line 44. Criterion 3's died side then rests on `test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint[api-key]`, and the entry says so. With only one row left, the test may lose its parametrization, or keep the single `completed` row; that is the tester's call.
    3. In tests/application/test_agent_run_probe_opencode.py:67, remove `assert "own login" not in item.detail` from `test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint`. This test was written earlier, and feature.md decision 10 lets it change only through the new text of `opencode_sso_hint`. Criterion 1's own test already makes this check.

    Main choice: end with `tests` rather than `question`. Findings 2 and 3 undo lines the tester added in this story. Finding 1 is a helper move, which the CLAUDE.md leave covers.

    The Description is unchanged: the review findings do not change what the task means.

    Noticed but not touched: `docs/operator-guide.md` still quotes the old opencode hint. That is criterion 5, for the documenter.
19. factory: started tests as vm.
20. tester: I made the three test changes that the coder's entry 18 asked for after the reviewer's findings in entry 16.

    1. Moved the helper under the standing leave in CLAUDE.md. `_probe_result` now lives in tests/probe_support.py as the public `probe_result(reason, login)`, with a docstring. It still builds the same completed-or-died `AgentRunResult`. tests/application/test_agent_run_probe_api_login.py now imports it, and I removed its now-unused `timedelta` and `AgentRunResult` imports. tests/application/test_agent_run_probe_opencode.py uses it instead of building the result inline. The probe_support module docstring now mentions the probe run results. `_probe_result(reason)` in tests/application/test_agent_run_probe_login.py is a different helper with no login parameter, and I left it alone.
    2. Dropped the `died` row from tests/application/test_agent_run_probe_opencode.py::test_a_probe_under_opencode_with_the_api_key_names_the_api_login_file. Only `completed` was left, so I removed the parametrization: the test now asserts `item.passed` and the detail `"the agent runs log in with the API key from /home/agent/.anthropic-api-key"`. I also removed the import of `EndReason`, which nothing used any more.
    3. Removed `assert "own login" not in item.detail` from tests/application/test_agent_run_probe_opencode.py::test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint. That test is now back to its earlier checks.

    Every earlier test keeps its name and checks the same thing.

    Criterion mapping:
    - criterion 1: tests/application/test_agent_run_probe_api_login.py::test_a_died_probe_hints_only_at_a_login_its_runtime_can_use
    - criterion 2: tests/application/test_agent_run_probe_api_login.py::test_a_completed_probe_without_a_login_file_names_the_agents_home_only_under_claude
    - criterion 3: the completed side is tests/application/test_agent_run_probe_opencode.py::test_a_probe_under_opencode_with_the_api_key_names_the_api_login_file. The died side is tests/application/test_agent_run_probe_opencode.py::test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint[api-key].
    - criteria 4 and 5 (`make check`, docs): no test.

    Files created: none. Earlier test files changed:
    - tests/probe_support.py and tests/application/test_agent_run_probe_api_login.py, under the standing leave to move a shared helper.
    - tests/application/test_agent_run_probe_opencode.py: the helper is used under that leave, and the row and the line this story had added are removed, as the review findings asked.

    Every module imported. I ran `make test` once: test: green (157.7 s). `make lint` is green.

    `lint`: lint: green (0.2 s)
    `test`: test: green (157.1 s)
21. factory: started doing as vm.
22. coder: Round 1. The reviewer's findings in entry 16 were all about tests, and the tester handled them in entry 20. This round changed no code, and the working tree was clean when it started. I ran `make check` against the tester's changes and it is green.

    What was built (already committed on the branch): `src/factory/application/preflight.py`.
    - `_opencode_login_hint("none")` returns `"; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names"`. The variable's name comes from `API_LOGIN_FILE_VARIABLE`.
    - `_login_detail` with `none` returns `"the agent runs get no login from a file"` under opencode. Under claude it returns the same text as before. A comment gives the lasting reason: the rollback to the base clears the agent's home before every stage.

    Main choice: one runtime branch inside `_login_detail`. I rejected a separate opencode helper, like `_opencode_login_hint`, because it would hold only one line.

    Refactor step: I read `git diff main -- src` again and found nothing to change.

    Description: unchanged. The journal since round 0 changed only tests: the reviewer's findings and the tester's move of `probe_result` to tests/probe_support.py. It did not change what the task means.

    Noticed but not touched: `docs/operator-guide.md` still quotes the old opencode hint. Updating it is criterion 5, the documenter's job.

    `check`: check: green (test: green (157.6 s))
    `duplicates`: duplicates: 0 new, 43 known, 0 gone

    `check`: check: green
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
23. factory: started review as vm.
24. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'` against the work item.

    **Code.** In `src/factory/application/preflight.py`, `_opencode_login_hint("none")` now returns the new hint, with the variable's name taken from `API_LOGIN_FILE_VARIABLE`. Every other login still gets `""`. `_login_detail` with `none` now returns `the agent runs get no login from a file` under opencode and keeps the old text under claude. The comment beside it gives the reason (the rollback clears the agent's home). This matches the Interface. The Claude Code texts are unchanged, and so is the order of the detail's parts.

    **Criteria.**
    - Criterion 1: `tests/application/test_agent_run_probe_api_login.py::test_a_died_probe_hints_only_at_a_login_its_runtime_can_use` is one parametrized test with the rows opencode-none, claude-api-key and claude-subscription. Each row checks the whole detail and that `own login` is absent.
    - Criterion 2: `test_a_completed_probe_without_a_login_file_names_the_agents_home_only_under_claude` has the rows opencode and claude.
    - Criterion 3: the completed side is `tests/application/test_agent_run_probe_opencode.py::test_a_probe_under_opencode_with_the_api_key_names_the_api_login_file`. The died side is the `[api-key]` row of `test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint`.
    - The Interface's "any other login returns `""`" is tested by the `[api-key]` and `[no-login]` rows.
    - The coder's `make check` in entry 22 was green, and `duplicates` reported 0 new.

    **Last round's findings.** All three from entry 16 are fixed. `probe_result` now lives in `tests/probe_support.py` and both modules use it. The duplicate died row is gone. The `own login` line that had been added to the earlier test is removed.

    Architecture, security, quality and the work item's hygiene hold. The Description matches what was built, and the docs criterion still names what the documenter must write.

    no findings

    Earlier tests:
    - `tests/probe_support.py`: the new text of `opencode_sso_hint` rests on the human's leave in feature.md decision 10. Moving `probe_result` here rests on the standing leave to move a shared test helper.
    - `tests/application/test_agent_run_probe_api_login.py`: the standing leave to move a shared test helper (`_probe_result` moved out). Otherwise it only adds tests, and its earlier test keeps its name and its checks.
    - `tests/application/test_agent_run_probe_opencode.py`: the human's leave in feature.md decision 10 (`SSO_HINT`). Otherwise it only adds a test.
    - `tests/application/test_agent_run_probe_factory_user.py`: the human's leave in feature.md decision 10.
    - `tests/entry/test_wiring_without_agent_user.py`: the human's answer in journal entry 8. Only the `opencode-no-login` row's `said` entry changed.
25. factory: started docs as vm.
26. documenter: Docs round for the two new opencode probe texts. I changed one file, docs/operator-guide.md, in *The probe of the agent run*, and found no findings.

    Changed:
    - docs/operator-guide.md, the opencode failed-probe paragraph: it now quotes the new hint, `; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names`. It also says why no login kept in the agent's home is advised: the rollback clears it. It points to *Running on opencode*, which S0001 already corrected.
    - docs/operator-guide.md, the completed-probe paragraph: the `none` detail is now given per runtime. Claude Code keeps `the agent runs get no login from a file; the runtime uses the login kept in its home`. Opencode gets `the agent runs get no login from a file`. I added that a provider whose key comes through `FACTORY_CONTAINER_ENV` passes this way.

    I checked the first smoke-test command: `grep -c "opencode build's own login"` on docs/operator-guide.md now gives 0. I did not run the second (pytest) or `make check`, since I changed only a document and the factory's checks run after me. I wrote no runnable examples.

    I compared the diff of src/factory/application/preflight.py with the Interface. `_opencode_login_hint` and `_login_detail` match it, and I found no contradiction between code and docs.

    Cross-read and found current:
    - README.md
    - docs/project-guide/ (README.md, agents.md, watching.md)
    - *Running on opencode* in docs/operator-guide.md, which already carries S0001's rule that only the API login works
    - The agent-home passages in docs/operator-guide.md

    Per criterion 5, docs/decisions.md needed no change.

    Stale text I saw and did not touch: nothing unrelated to this story.

    `check`: check: green (not run again: passed on tree 6c9e3830fbbb at 2026-10-26T17:38:40Z)
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok
27. factory: started smoke-test as vm.
