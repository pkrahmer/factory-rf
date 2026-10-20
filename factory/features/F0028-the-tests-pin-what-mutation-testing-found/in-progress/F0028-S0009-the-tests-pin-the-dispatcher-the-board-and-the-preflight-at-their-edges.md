---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 320
comments_read: []
handed_over: null
claim: null
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
