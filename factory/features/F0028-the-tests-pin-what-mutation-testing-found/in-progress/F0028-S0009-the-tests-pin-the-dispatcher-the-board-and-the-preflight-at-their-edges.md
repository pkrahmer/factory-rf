---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 320
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-20T02:53:56.875799Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T02:40:24.198129Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T02:40:24.203732Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T02:40:39.939138Z'
  stage: intake
  run: 7c6cb461e5814572bcc0cdcb2bdd4ef8
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T02:41:00.512972Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T02:43:37.333351Z'
  stage: tests
  run: 741c9dffdf9046a19ea6163a6645bbaa
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T02:43:57.777739Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T02:46:00.024179Z'
  stage: doing
  run: 3fa5923a279b468ebb1cb02ba2d46720
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T02:46:21.026330Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T02:47:06.435004Z'
  stage: review
  run: 6a4615b4541c4864a376b5735c8cfc58
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T02:47:27.129022Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-20T02:47:46.082173Z'
  stage: doing
  run: 4effc1f81877459c98846308db848a63
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T02:48:06.841056Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-20T02:50:00.352346Z'
  stage: tests
  run: c82a8cbbc38d4f1e8a59853d348ba2c3
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-20T02:50:21.037561Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-20T02:52:16.936068Z'
  stage: doing
  run: d3b9d3ee326949c1addcf29f3b75b245
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-20T02:52:37.538629Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-20T02:53:03.161365Z'
  stage: review
  run: efbc83cff0f546aaac1455a843a30015
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-20T02:53:23.821855Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-20T02:53:36.726145Z'
  stage: docs
  run: 7ab78e89c6d4450e842fd289d62ea008
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-20T02:53:56.875799Z'
  stage: smoke-test
---

# The tests pin the dispatcher, the board and the preflight at their edges

## Description

The mutation sweep of 2026-10-19 over `factory.application` (`planning/overnight/mutation-sweep-2026-10-19-part2.md`, the rest of its story 7) left six live mutants in the dispatcher, the board reader and the preflight, each a side that no test reaches. At the error cap the dispatcher posts its stop for the event's work item; a work item without a state gives the stop no pull request, and the stop service opens a draft (`dispatcher.py:135`). Every test's work item has a state, so a stop that read the state's pull request regardless would pass (it raises, and the report is lost). The board counts a feature's stories per folder, and no board test counts a story in progress in the feature's row (`board.py:40`). The opencode login hint names the agent's user, or `the factory user` when `FACTORY_AGENT_USER` is unset (`preflight.py:313`). Only the hint's first part is tested without a user. This story pins these as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003.

## Interface

No module under `src/factory/` changes. The behaviour pinned (`application`):

- `factory.application.dispatcher.Dispatcher.dispatch(event)`: at the error cap, the stop for a work item whose document has no state carries no pull request, so `StopService.post` opens a draft on the work item's branch and posts the report there.
- `factory.application.board.BoardReader.read(definition)`: a feature's row counts its story files in `backlog/`, `in-progress/` and `done/` on `origin/main`.
- `factory.application.preflight.agent_run_probe_item(boundaries, settings, environment)` under opencode, after a probe run that died without a login (`login="none"`): the detail names `settings.agent_user`, or `the factory user` when it is `None`, in both of its sentences.

Tests (the tester writes them): `tests/application/test_dispatcher_without_state.py`, `tests/application/test_board_in_progress.py` and `tests/application/test_agent_run_probe_factory_user.py`. Each builds its inputs with the fixtures of `tests/conftest.py` and the shared helpers, never a copy of them. The failing handler is `Failing` of `tests/tick_support.py`, which S0008 moves there (it raises `ValueError("boom")` by default). The settings of criterion 3 are the `probe_settings` fixture, and its environment is `ENVIRONMENT` of `tests/probe_support.py`, which `tests/test_shared_test_helpers.py` pins to that module. No earlier test changes.

## Acceptance criteria

1. The error stop of a work item without a state (one test): the human pushes `note.txt` to `work-item/F0001-S0001`, a fetch; the snapshot is `WorkItemSnapshot(id="F0001-S0001", path="factory/features/F0001-demo/in-progress/F0001-S0001-x.md", folder="in-progress", branch="work-item/F0001-S0001", branch_commit=<the branch's commit on the remote>, document=WorkItemDocument(state=None, body="# Demo story\n"))`. The event is `Event(kind="run", work_item=<it>, remote_state="a" * 40)`, dispatched three times by `Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries))`. The outcomes are exactly `["error", "error", "reported"]`. `hosting.pull_requests()` is one draft, number `1`, on `work-item/F0001-S0001`, titled `F0001-S0001: Demo story`, and the keys of its factory posts are exactly `[PostKey(work_item="F0001-S0001", kind="error", n="aaaaaaaaaaaa")]`.
2. A story in progress on the board (one test): on top of the remote's seed, the feature `F0001-example`, titled `Example feature`, with the backlog story `F0001-S0001-first.md`, the human pushes `# Second story\n` to `backlog/F0001-S0002-second.md` and `# Third story\n` to `done/F0001-S0003-third.md` of that feature on `main`, then starts `F0001-S0001`. After a fetch, `BoardReader(boundaries).read(definition).features` is exactly `[FeatureRow(feature="F0001", title="Example feature", backlog=1, in_progress=1, done=1, acceptance="incomplete")]`.
3. The opencode login hint by user (rows of one parametrized test; the agent `coder` installed in the test's agent home; `settings = probe_settings.model_copy(update={"agent_user": <user>, "agent_runtime": "opencode", "pinned_opencode_version": "1.19.3"})`; the probe run queued as `AgentRunResult(end_reason="died", duration=timedelta(seconds=5), login="none")`; `agent_run_probe_item(boundaries, settings, ENVIRONMENT).detail`):
   - `agent_user=None`: exactly `the probe run ended died; run opencode run by hand as the factory user to see why; the agent runs get no API key: log in once as the factory user with the opencode build's own login, or put a key in the file FACTORY_API_LOGIN_FILE names`.
   - `agent_user="agent"`: exactly the same text with `agent` in both places of `the factory user`.
4. `make check` stays green.
5. docs: none. The operator guide already describes the error cap's report, the board's columns and the opencode login hint, and this story changes none of them.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.domain.board import feature_rows
from factory.domain.post_texts import error_report_text
from factory.domain.work_item import StoryFile

directory = "factory/features/F0001-example"
stories = [
    StoryFile(id=f"F0001-S000{n}", path=f"{directory}/{folder}/F0001-S000{n}-x.md", feature_directory="F0001-example", file_name=f"F0001-S000{n}-x.md", folder=folder)
    for n, folder in [(1, "in-progress"), (2, "backlog"), (3, "done")]
]
print(feature_rows(stories, {"F0001": "Example feature"}))
print(error_report_text("run:F0001-S0001", "ValueError: boom", "a" * 40, 3))
EOF
```

Expect: two lines, `[FeatureRow(feature='F0001', title='Example feature', backlog=1, in_progress=1, done=1, acceptance=None)]` and ``The factory failed 3 times on `run:F0001-S0001` and has stopped retrying it. Last error: ValueError: boom. A new commit on the work item's branch (now at aaaaaaaaaaaa) makes the factory try again.``

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names concrete modules and signatures (`Dispatcher.dispatch(event)`, `BoardReader.read(definition)`, `agent_run_probe_item(boundaries, settings, environment)`), the three test modules, and the shared helpers they use (`Failing` in `tests/tick_support.py`, `probe_settings`, `ENVIRONMENT`). No source change, so there is no new signature to check. `Failing` reaches `tests/tick_support.py` through S0008, which must be archived first (the feature's build order and decision 13).
   - Criteria: each is one test, with exact values. 1 gives the outcomes, the draft pull request and the post key for a work item without a state, so the stop opens a draft. 2 gives the exact `FeatureRow` with one story in each folder, so the in-progress count is pinned. 3 is one parametrized test with exact texts for `agent_user=None` and for `"agent"`, so both sentences and both sides of the default are covered. Every behaviour the Interface states has a criterion. No rule has an untested failing side: the story adds no limit or validation, only behaviour on the side that was never reached.
   - Smoke test: one runnable Python snippet that uses `feature_rows`, `error_report_text` and `StoryFile`. Its `Expect:` gives two exact lines, which the output can be compared to. The `acceptance=None` in the first line comes from the domain call, which has no acceptance report. Criterion 2 expects `"incomplete"` from the reader, so the two do not conflict.
   - Architecture: tests only, under `tests/application/`, mirroring the package. It uses the shared fixtures and helpers and copies none of them. No fake git, no mock of the code under test. Nothing under `src/` changes.
   - Scope: inside F0028's scope (the `S0009` line of `feature.md`) and not in its "Out of scope". It changes no earlier test. The only shared-helper move is S0008's, which `feature.md` records. The docs criterion is `none`, as in the feature's decision.
4. factory: started tests as self.
5. tester: Wrote one test per criterion, against the Interface. Each test uses the shared fixtures and helpers: `Failing` from `tests/tick_support.py`, `probe_settings`, `ENVIRONMENT` from `tests/probe_support.py`, `remote_commit`, `install_agents`, `PIPELINE_YAML` and `HumanClone`. None of them is copied.

   - criterion 1: tests/application/test_dispatcher_without_state.py::test_the_error_report_of_a_work_item_without_a_state_opens_a_draft
   - criterion 2: tests/application/test_board_in_progress.py::test_a_feature_row_counts_one_story_in_each_folder
   - criterion 3: tests/application/test_agent_run_probe_factory_user.py::test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user (rows `no-user`: `agent_user=None` → `the factory user`, and `agent`: `agent_user="agent"` → `agent`)
   - criterion 4: `make check`; the factory runs it as the gate. No test of its own.
   - criterion 5: docs: none. No test.

   Files created: the three test modules above. No earlier test file changed, and no shared helper was moved.

   Modules the test run could not import: none. The story changes nothing under `src/` and says the code already behaves this way, so the new tests pass now instead of failing first. In my one `make test` run they passed (`test: green (46.2 s)`), and `make lint` is green. As the stage says, I skipped the type check. There is nothing for the coder to implement. Their `make check` covers the new tests under `mypy --strict`.

   No criterion needed interpreting, and nothing is open.

   `lint`: lint: green (0.0 s)
   `test`: test: green (47.6 s)
6. factory: started doing as self.
7. coder: I built nothing, because the story needs no code. The Interface says no module under `src/factory/` changes, and the tester's three new tests pass against the code as it is: `tests/application/test_dispatcher_without_state.py`, `tests/application/test_board_in_progress.py` and `tests/application/test_agent_run_probe_factory_user.py`. The tester skipped the type check, so I ran `make check` to cover the new tests under `mypy --strict`. Every target is green and it ends with `check: green` (`test: green (46.9 s)`, coverage 99.14 %).

   - Main choice: leave `src/` alone, as the Interface says. The alternative I rejected was any change to the code. That would go beyond the description (R13), and nothing is failing.
   - Refactor: there was nothing to read. `git diff main -- . ':!factory' ':!tests'` is empty, and there are no new files outside `factory/` and `tests/`.
   - Description: no journal entry changed the meaning of the task, so it stays as written.
   - Noticed, not touched: none.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`, which adds three test modules under `tests/application/` and changes nothing under `src/`. I read them against the criteria and against the shared helpers in `tests/`.

   - Criterion 1, `test_dispatcher_without_state.py`, matches the criterion's exact snapshot, event, dispatcher, outcomes, draft and post key.
   - Criterion 2, `test_board_in_progress.py`, builds on the seed in `tests/git_support.py` (`F0001-example`, `backlog/F0001-S0001-first.md`) and asserts the exact `FeatureRow`.
   - Criterion 3, `test_agent_run_probe_factory_user.py`, is one parametrized test with the rows `no-user` and `agent`, and it uses `probe_settings`, `ENVIRONMENT` and `install_agents`.
   - The Interface states no limit or validation, so there is no untested failing side. The coder's `make check` was green (entry 7). Nothing under `src/` changed, so architecture and security are untouched.

   Findings:
   1. `tests/application/test_agent_run_probe_factory_user.py:16` (`HINT`): this is a second copy of the opencode login-hint text that `tests/application/test_agent_run_probe_opencode.py:16-24` (`DIED`, `SSO_HINT`) already holds. With `agent`, the template is exactly `DIED + SSO_HINT`, so a change to that text in `preflight.py:312` would have to be made in both modules. Fix: the tester moves the text once to `tests/probe_support.py`, under the standing leave to move a shared test helper. That can be a function of the user, e.g. `opencode_login_hint(user)`, or a template. `test_agent_run_probe_opencode.py` then builds `DIED`/`SSO_HINT` from it, with every earlier test keeping its name and what it checks, and the new test uses it instead of `HINT`. The coder hands this to the tester with `tests`.

   Considered and not raised:
   - The inline `WorkItemSnapshot` in `test_dispatcher_without_state.py:33` looks like `_snapshot` of `tests/application/test_dispatcher.py:66`. It is not a copy: that helper always sets a state and cannot build `state=None`, and criterion 1 spells this snapshot out.
   - The `agent` row repeats the existing `none` row of `test_agent_run_probe_opencode.py`, but criterion 3 asks for it.
   - The coder's `duplicates: 5 new` comes from no change in this diff, which touches nothing under `src/`.

   Earlier tests: none. The diff only adds test files (status `A`), and no test file on `main` is changed, renamed or deleted.
10. factory: started doing as self.
11. coder: Round 1: the reviewer's one finding is a copied test helper, so this is a change to tests. I changed no code. Under the standing leave to move a shared test helper in `CLAUDE.md`, the tester makes this move:

    - **The helper:** the opencode login-hint text. It appears twice: as `HINT` in `tests/application/test_agent_run_probe_factory_user.py:16`, and as `DIED` plus `SSO_HINT` in `tests/application/test_agent_run_probe_opencode.py:16-24`.
    - **The shared place:** `tests/probe_support.py`. It can be a function of the user, such as `opencode_login_hint(user)` returning the full "died" text with both sentences, or a template.
    - **The earlier test file:** `tests/application/test_agent_run_probe_opencode.py`. It builds its `none` row (`DIED + SSO_HINT`) from the shared helper. Its `API_HINT` and `no-login` rows keep their own text. Every test keeps its name and checks the same thing.
    - **The new test:** `test_agent_run_probe_factory_user.py` uses the shared helper instead of its own `HINT`.

    What I built: nothing. The Interface says no module under `src/factory/` changes, and this round's finding touches only tests. The main choice was to send the work item to the tester with `tests`. I rejected making the move myself, because the coder never edits tests (R9).

    Refactor: there was nothing to refactor; my diff outside `factory/` and `tests/` is still empty. Description: no journal entry changed what the task means.

    Noticed, not touched: `tests/application/test_agent_run_probe_api_login.py:22` has its own `DIED` for `claude -p`. Its text is different (claude, not opencode), so it is not part of this move.
12. factory: started tests as self.
13. tester: Round 1: I moved the shared test helper that the coder's entry 11 names (the reviewer's finding 1, entry 9). I made the move under the standing leave in `CLAUDE.md` to move a shared test helper.

    - The shared place: `tests/probe_support.py` now has `opencode_died(user)`, which is the "died" sentence of a probe under opencode run as `user`, and `opencode_sso_hint(user)`, which is the "no API key" hint for `user`. I split the text in two because the `no-login` row of the earlier test checks the died sentence alone. The module's docstring now names the opencode texts.
    - The earlier test file changed: `tests/application/test_agent_run_probe_opencode.py`. `DIED` is now `opencode_died("agent")` and `SSO_HINT` is now `opencode_sso_hint("agent")`. `API_HINT` keeps its own text. The test keeps its name, its rows and the strings it compares.
    - The new test: `tests/application/test_agent_run_probe_factory_user.py` no longer has its own `HINT`. It asserts `opencode_died(named) + opencode_sso_hint(named)`.

    The mapping is unchanged:
    - criterion 1: tests/application/test_dispatcher_without_state.py::test_the_error_report_of_a_work_item_without_a_state_opens_a_draft
    - criterion 2: tests/application/test_board_in_progress.py::test_a_feature_row_counts_one_story_in_each_folder
    - criterion 3: tests/application/test_agent_run_probe_factory_user.py::test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user
    - criterion 4: `make check`, the factory's gate. It has no test of its own.
    - criterion 5: docs: none. It has no test.

    Files created: none this round. The files changed are `tests/probe_support.py` and the two test modules above. No module failed to import. `make test` is green (`test: green (45.9 s)`, coverage 99.14 %) and `make lint` is green. I skipped the type check, as the stage says. Nothing is open.

    `lint`: lint: green (0.0 s)
    `test`: test: green (38.2 s)
14. factory: started doing as self.
15. coder: Round 1, after the tester's move. I built nothing. The Interface says no module under `src/factory/` changes. In entry 13 the tester moved the opencode login-hint text, the reviewer's only finding, into `tests/probe_support.py` as `opencode_died(user)` and `opencode_sso_hint(user)`. `tests/application/test_agent_run_probe_opencode.py` and `tests/application/test_agent_run_probe_factory_user.py` now both use them. The tester skipped the type check, so I ran `make check`; it is green, which covers the moved helpers under `mypy --strict` (`test: green (44.7 s)`, coverage 99.14 %).

    - Main choice: send the work item on to review without touching anything. I rejected changing any code: nothing is failing, and a change would go beyond the description (R13).
    - Refactor: there was nothing to change. `git diff main -- . ':!factory' ':!tests'` is empty, so the whole diff is the tester's.
    - Description: no journal entry changed what the task means.
    - Noticed but not touched: nothing new. As entry 11 says, `tests/application/test_agent_run_probe_api_login.py:22` keeps its own `DIED` text for `claude -p`. That text is different from the opencode one.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
16. factory: started review as self.
17. reviewer: Round 1. I reviewed `git diff main...HEAD -- . ':!factory'`. It adds three test modules under `tests/application/`, moves the opencode login-hint text into `tests/probe_support.py`, and makes `tests/application/test_agent_run_probe_opencode.py` use that shared text. Nothing under `src/` changes. I read the diff against the criteria and the shared helpers.

    - Criterion 1, `tests/application/test_dispatcher_without_state.py`: the test matches the criterion exactly. It covers the push of `note.txt`, the snapshot with `state=None`, the event with `remote_state="a" * 40`, the dispatcher with `Failing()`, the three outcomes, the one draft (number 1, on the branch, with its title) and the one `PostKey`.
    - Criterion 2, `tests/application/test_board_in_progress.py`: the test pushes the backlog and done stories, starts `F0001-S0001`, fetches, and asserts the exact `FeatureRow` with 1/1/1 and `incomplete`.
    - Criterion 3, `tests/application/test_agent_run_probe_factory_user.py`: one parametrized test with the rows `no-user` and `agent`. It builds the expected text as `opencode_died(named) + opencode_sso_hint(named)`. I joined the two by hand and got exactly the text the criterion gives for both rows.
    - Last round's finding (the copied hint text) is fixed. A search of `tests/` for the hint's wording now finds only `tests/probe_support.py`.
    - The Interface states no limit or validation, so there is no failing side left untested. The coder's `make check` was green (entry 15).
    - Architecture and security: nothing under `src/` changed, and the diff adds no marker that silences a check.
    - Work item: the journal records the main choice (no code change) and the helper move. The Description and the docs criterion (`none`) still match what was built.

    no findings

    Earlier tests:
    - `tests/application/test_agent_run_probe_opencode.py`: changed under the standing leave in `CLAUDE.md` to move a shared test helper. Only `DIED` and `SSO_HINT` now come from `tests/probe_support.py`. They give the same strings as before (I compared them), and every test keeps its name and rows.
    - `tests/probe_support.py`: the shared place the helpers moved to, under the same standing leave. It only adds `opencode_died` and `opencode_sso_hint` and updates the module docstring. `ENVIRONMENT` and `COMPLETED` are unchanged.
18. factory: started docs as self.
19. documenter: Round 1, docs. The docs criterion is `none`, and the diff is tests only: three new modules under `tests/application/`, the shared opencode hint helpers in `tests/probe_support.py`, and `tests/application/test_agent_run_probe_opencode.py` using them. Nothing under `src/` changed.

    Files changed: none. I wrote no documentation. The criterion asks for none and the code behaves as it did before.

    Cross-read and found current against the diff:
    - `docs/operator-guide.md`, "The probe of the agent run" (around line 459). It says the detail names the agent user, or `the factory user` without `FACTORY_AGENT_USER`. That matches the behaviour criterion 3 pins. I did not check this passage against the full opencode hint text; I only checked the part about the user's name.
    - The `grep` of `README.md` and `docs/` for the hint text found no other description of the login hint.
    - I did not check the operator guide's descriptions of the board's columns and the error cap's report. I took them from the story's docs criterion, and this story does not change those behaviours.

    Stale text I noticed but did not touch: none that relates to this story.

    Findings for the coder: none. I ran no `make check`, because I changed no file; the factory's checks follow this stage.

    `check`: check: green (not run again: passed on tree 75f1d0344314 at 2026-10-20T02:51:24Z)
    `secrets`: secrets: green (0.2 s)
    `documents`: documents ok
20. factory: started smoke-test as self.
