---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 463
comments_read: [6422541052]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-10-26T17:21:18.798949Z'
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
