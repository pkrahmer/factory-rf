---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 319
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T02:29:31.607110Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T02:29:31.613661Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T02:29:48.567204Z'
  stage: intake
  run: 6647a6b51df04e93904184cb58c50319
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T02:30:09.113580Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T02:34:09.004690Z'
  stage: tests
  run: 7c2013ef472c400b98ddde529d926ffa
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T02:34:29.411930Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T02:36:39.100594Z'
  stage: doing
  run: 78d05e7caecb46adad01bd79ae2b4137
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T02:37:00.474977Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T02:37:35.584012Z'
  stage: review
  run: 2be74335efb64a88bcdb9ef5a6ead627
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T02:37:56.287735Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T02:38:08.344475Z'
  stage: docs
  run: 59c0279c1f414f01bb5bb57d78480f0d
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T02:38:29.813542Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T02:38:45.680076Z'
  stage: smoke-test
  run: 484dd0a90dbb4b328f174e3e5502cd4d
---

# The tests pin the stage's aftermath, the opening and the tick at their edges

## Description

The mutation sweep of 2026-10-19 over the rest of `factory.application` (`planning/overnight/mutation-sweep-2026-10-19-part3.md`, its S0008) left eight live mutants in the stage's aftermath, the opening and the tick, each a side that no test reaches.

- **An empty entry.** A completed run with an allowed decision and the entry `""` stalls as `no_result` with the detail `the entry is empty`, which the stall note shows (`stage.py:197` and `:199`). The tests reach that stall only with a name prefix and a blank after it (`tester: `). `AgentRunResult` refuses a completed run whose entry is `None`, so `""` is the empty entry a run can bring.
- **A finding twice.** The same form finding twice before and twice after the agent is no new finding (`stage.py:511`). No test has a finding twice on both sides.
- **The opening's journal.** Opening a story with a `## Description` and no `## Journal` appends the journal (`opening.py:31`). The only such body in the tests has no section at all.
- **The tick's stops.** The `fetch_failed` and `checkout_restore_failed` stops carry the error's text as their detail (`tick.py:142` and `:158`). The tick hands the dispatcher the factory log, where the error cap of an event without a work item is written (`tick.py:112`). No tick test pins either.

This story pins these as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003. The sweep's row of a body whose last line ends in spaces is equivalent (decision 10 of `feature.md`): the reader strips the body before the opening sees it.

## Interface

No module under `src/factory/` changes. The behaviour pinned (`application`):

- `factory.application.stage.AfterAgent.process(launched)`: a completed run whose entry is `""`, or only the role's name and a colon, stalls as `no_result` with the detail `the entry is empty`.
- `AfterAgent.process`: of equal form findings (their line numbers masked), as many after the run as before are old ones; only those beyond that count are new, and only a new one stalls as `form_invalid`.
- `factory.application.opening.WorkItemOpening.prepare(work_item, path)` for a new branch: a backlog body without a `## Journal` section gets one at its end, also when it has other sections.
- `factory.application.tick.Tick.run()`: a fetch that raises `FetchFailed` ends the tick at the stop `fetch_failed`, a restore that raises `GitError` at `checkout_restore_failed`, each stop's detail the error's `str()`. At the error cap of an event without a work item the factory log gets `error cap reached on <key>: <last error>`.

Tests (the tester writes them):

- `tests/application/test_after_agent_edges.py` builds on `tests/stage_run_support.py` as it is: `open_story`, `run_stage`, `STORY`, `PATH`, `CREATED` and `CREATED_LINE`.
- `tests/application/test_opening_journal_edges.py` builds on `WorkItemOpening` and the `human`, `boundaries` and `definition` fixtures.
- `tests/application/test_tick_stop_details.py` runs with `pytestmark = pytest.mark.usefixtures("installed_agents")`, as `tests/application/test_tick.py` does, and reads the log with `log_lines` of `tests/log_support.py`. Its failing gits are small subclasses of `GitCli` of its own, built as the `checkout` fixture builds its own: `GitCli(tmp_path / CHECKOUT, GitOptions(kill_points=kill_points, identity=TEST_IDENTITY))`. The tick runs on `replace(boundaries, git=<it>)`. Its handler factory and its failing handler are shared, not copied. Under the standing leave of `CLAUDE.md` (*Tests*), the tester moves `_factory` of `tests/application/test_tick.py` (already copied in `tests/application/test_tick_stale_branch.py`) and `Failing` of `tests/application/test_dispatcher.py` (it raises the error it is given, `ValueError("boom")` by default) to a new shared module, `tests/tick_support.py`, as `handlers_of` and `Failing`. `test_tick.py`, `test_tick_stale_branch.py` and `test_dispatcher.py` then import them from there and keep every test's name and what it checks, and the tester's entry names the three files.

No other earlier test changes.

In criterion 2, `BLOCK` is `` ```bash\ntrue\n```\n ``, `WITHOUT_EXPECT` is `STORY.replace("```\nExpect: nothing.\n", "```\n")`, `TWICE` is `WITHOUT_EXPECT.replace(BLOCK, BLOCK + "\n```bash\nfalse\n```\n")` (two blocks without an `Expect:` line), and `THRICE` is `WITHOUT_EXPECT.replace(BLOCK, BLOCK + "\n```bash\nfalse\n```\n\n```bash\nfalse\n```\n")` (three).

## Acceptance criteria

1. An empty entry (rows of one parametrized test; `open_story(boundaries, human, agent_home)`, `AgentRunResult(end_reason="completed", decision="doing", entry=<entry>, duration=timedelta(minutes=1))` queued, `run_stage(boundaries)`): with the entry `""`, and with the entry `tester:`, `report.stall.reason` is `no_result`, and the first line of the one factory post on `report.pull_request` is exactly `Stalled (attempt 1 of 2): the agent gave no valid decision and entry: the entry is empty. Retrying on the next tick.`
2. The form findings counted (rows of one parametrized test; `open_story(boundaries, human, agent_home, state=WorkItemState(stage="review", journal=[CREATED]), body=TWICE, roles=("reviewer",))`; the run writes `PATH` as `boundaries.work_item_writer.render(WorkItemDocument(state=WorkItemState(stage="review", journal=[CREATED]), body=<after> + CREATED_LINE))` and completes with decision `docs` and entry `reviewed.`; `run_stage(boundaries)`):
   - `<after>` is `TWICE`: `report.stall` is `None` and `report.rule` is `1` (no new finding; the factory asks about the old ones).
   - `<after>` is `THRICE`: `report.stall.reason` is `form_invalid`, and the first line of the last factory post on `report.pull_request` is exactly `Stalled (attempt 1 of 2): the work item's form broke during the stage: the code block opened at line 27 is not followed by an "Expect:" line. Retrying on the next tick.` (one new finding, the third block's).
3. The opening's journal (one test): the human pushes `# First story\n\n## Description\n\nText.\n` to `factory/features/F0001-example/backlog/F0001-S0001-first.md` on `main` and starts it, a fetch, then `WorkItemOpening(boundaries, definition).prepare("F0001-S0001", PATH)`: its document's body is exactly `# First story\n\n## Description\n\nText.\n\n## Journal\n\n1. 2026-10-12 human: created.\n`.
4. The tick's stop details (rows of one parametrized test; `Tick(replace(boundaries, git=<git>), "factory-1", handlers_of({"idle": IdleHandler()})).run()`, then `[(stop.reason, stop.detail) for stop in boundaries.health.read().stops]`):
   - A git whose `fetch` raises `FetchFailed("git fetch", 128, "fatal: the remote end hung up")`: the outcome is `TickOutcome(stopped="fetch_failed")`, the stops exactly `[("fetch_failed", "git fetch failed (exit 128): fatal: the remote end hung up")]`.
   - A git whose `reset_to` raises `GitError("git reset", 128, "fatal: unable to write the index")`: `TickOutcome(stopped="checkout_restore_failed")`, the stops exactly `[("checkout_restore_failed", "git reset failed (exit 128): fatal: unable to write the index")]`.
5. The error cap in the factory log (one test): `Tick(boundaries, "factory-1", handlers_of({"idle": Failing(RuntimeError("handler failed"))}))` run three times: the dispatch outcomes are `error`, `error` and `reported`, and the lines of `log_lines(tmp_path)` that hold `error cap` are exactly `["2026-10-12T12:00:00Z error cap reached on idle:-: RuntimeError: handler failed"]`.
6. `make check` stays green.
7. docs: none. The operator guide already names the stall reasons, the two repository stops and the error cap's log line, and this story changes none of them.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.domain.decisions import agent_entry
from factory.domain.errors import FetchFailed
from factory.domain.events import Event
from factory.domain.post_texts import stall_note

print(agent_entry(role="tester", stage="tests", decision="doing", text="tester:", undone=[]))
print(stall_note("no_result", 1, 2, detail="the entry is empty"))
print(FetchFailed("git fetch", 128, "fatal: the remote end hung up"))
print(Event(kind="idle", work_item=None, remote_state="a" * 40).key)
EOF
```

Expect: four lines, `None`, `Stalled (attempt 1 of 2): the agent gave no valid decision and entry: the entry is empty. Retrying on the next tick.`, `git fetch failed (exit 128): fatal: the remote end hung up` and `idle:-`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`AfterAgent.process`, `WorkItemOpening.prepare(work_item, path)`, `Tick.run()`), states that no module under `src/factory/` changes, and names the test files, the support modules and the shared helper move (`handlers_of`, `Failing` in `tests/tick_support.py`) under the standing leave, with the three earlier test files the tester must name.
   Criteria: all five behaviour criteria are each testable by one test function with exact expected values. The empty entry has both rows (`""` and `tester:`). The form findings have the old-only side (`TWICE`, no stall, rule 1) and the new-finding side (`THRICE`, `form_invalid`). The opening has the missing-journal case. The tick has both stops with exact details, and the error cap has its log line. Criteria 6 (`make check`) and 7 (`docs: none`) close the list. The Interface states no limit or rejected input without a failing-side criterion. I did not run the numbers (for example "line 27") against the code; the tester will find out if they are wrong.
   Smoke test: it is a runnable `uv run -q python` heredoc using existing domain functions, and its `Expect:` line lists four checkable output lines.
   Architecture: tests only, under `tests/` mirroring `application/`, with shared helpers in a root support module as CLAUDE.md allows. Nothing is built in a layer and no code changes.
   Scope: it is within F0028 (S0008 in the feature's scope and stories list) and touches nothing in "Out of scope"; the equivalent mutants (decision 10) are left out as the Description says.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 5. The story pins behaviour the code already has, so the tests pass now instead of failing first. `make test` ended `test: green (48.5 s)` and `make lint` is green. I skipped the type check as the stage says. The coder's `make check` will cover it.

   Mapping:
   - criterion 1: tests/application/test_after_agent_edges.py::test_an_empty_entry_stalls_as_no_result (rows `empty` with entry `""`, `role-name-only` with entry `tester:`)
   - criterion 2: tests/application/test_after_agent_edges.py::test_only_findings_beyond_the_count_before_the_run_are_new (rows `as-many-as-before` with TWICE: no stall, rule 1; `one-more-than-before` with THRICE: `form_invalid` and the exact note naming line 27)
   - criterion 3: tests/application/test_opening_journal_edges.py::test_a_body_with_sections_and_no_journal_gets_the_journal_at_its_end
   - criterion 4: tests/application/test_tick_stop_details.py::test_a_repository_stop_carries_the_errors_text_as_its_detail (rows `fetch` and `restore`. The failing gits are `GitCli` subclasses `FailingFetch` and `FailingReset`, built on `tmp_path / CHECKOUT` with `GitOptions(kill_points=kill_points, identity=TEST_IDENTITY)`, and the tick runs on `replace(boundaries, git=...)`)
   - criterion 5: tests/application/test_tick_stop_details.py::test_the_error_cap_of_an_event_without_a_work_item_is_written_to_the_factory_log
   - criterion 6 (`make check`) and criterion 7 (docs: none): no test.

   Files created: tests/tick_support.py, tests/application/test_after_agent_edges.py, tests/application/test_opening_journal_edges.py, tests/application/test_tick_stop_details.py.

   Earlier test files changed under the standing leave of CLAUDE.md (*Tests*), as the Interface names them. Every test keeps its name and checks the same thing:
   - tests/application/test_tick.py: its `_factory` was removed and it now imports `handlers_of` from `tick_support`.
   - tests/application/test_tick_stale_branch.py: its copy of `_factory` was removed and it now imports `handlers_of`.
   - tests/application/test_dispatcher.py: its `Failing` was moved to `tick_support` and it now imports it from there.
   - Unused imports in these three files were dropped.
   - `test_tick.py` still has its own `Failing` class. It has no arguments, records into `.events` and raises `RuntimeError`. The Interface names only the dispatcher's `Failing` for the move, so I left this one alone.

   Modules the test run could not import: none. Everything under test already exists.

   Rejected: building the failing gits by mocking `GitCli`. The Interface asks for subclasses, and the code under test is not mocked.

   Open: nothing.

   `lint`: lint: green (0.0 s)
   `test`: test: green (46.3 s)
6. factory: started doing as self.
7. coder: Built nothing. The story pins behaviour the code already has, and its Interface says no module under `src/factory/` changes. The tester's tests (tests/application/test_after_agent_edges.py, tests/application/test_opening_journal_edges.py, tests/application/test_tick_stop_details.py, plus the shared tests/tick_support.py) pass against the code as it stands. I ran `make check` in the foreground and it ended `test: green (48.1 s)` and `check: green`, with total coverage at 99.14 %.

   Main choice: I left `src/` alone. The alternative I rejected was making changes so the diff has something in it, which would go beyond the description (R13).

   Refactor: there is no coder diff to review, so nothing was changed.

   Description: the journal did not change what the task means, so the Description stays as it is.

   Noticed but not touched: as the tester's entry says, `tests/application/test_tick.py` still has its own argument-free `Failing` class that records `.events`. It is separate from the shared `Failing` in `tests/tick_support.py`. The Interface did not name it for the move.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   I read the work item and `git diff main...HEAD -- . ':!factory'`: three new test modules, the new shared `tests/tick_support.py`, and three earlier test files changed. Nothing under `src/` changed.

   Acceptance criteria:
   - Criterion 1 is `test_an_empty_entry_stalls_as_no_result` in `tests/application/test_after_agent_edges.py`. Its two rows are `""` and `tester:`. Each checks for exactly one factory post and asserts its exact first line.
   - Criterion 2 is `test_only_findings_beyond_the_count_before_the_run_are_new`. The `TWICE` row checks no stall and `rule == 1`. The `THRICE` row checks `form_invalid` and the exact note about line 27 in the last post. Both sides of the count are covered.
   - Criterion 3 is in `tests/application/test_opening_journal_edges.py` and asserts the exact body.
   - Criterion 4 is `test_a_repository_stop_carries_the_errors_text_as_its_detail` in `tests/application/test_tick_stop_details.py`. Its two rows use the `GitCli` subclasses `FailingFetch` and `FailingReset`, built as the Interface says, and the tick runs on `replace(boundaries, git=...)`. `reset_to` is what `tick.py:183` calls during the restore.
   - Criterion 5 is in the same file. It checks the outcomes error, error, reported and the exact `error cap` log line.

   The coder's journal entry says `make check` ended with `check: green`.

   Architecture and security: only tests changed. The diff adds no markers that silence a check, no secrets, and no shell built from strings.

   Quality: the helpers are moved to one shared place, not copied again. The failing gits are small subclasses, not mocks. Everything has module and class docstrings.

   Work item hygiene: the journal explains the main choice (leave `src/` alone) and what was rejected. The Description matches what was built, and "docs: none" still holds.

   Earlier tests:
   - `tests/application/test_dispatcher.py`: changed under the standing leave to move a shared test helper. `Failing` moved to `tests/tick_support.py` and is imported from there. Every test keeps its name and checks the same thing.
   - `tests/application/test_tick.py`: changed under the standing leave to move a shared test helper. `_factory` was replaced by the shared `handlers_of`, and two imports that are no longer used were dropped. Every test keeps its name and checks the same thing.
   - `tests/application/test_tick_stale_branch.py`: changed under the standing leave to move a shared test helper. Its copy of `_factory` was replaced by `handlers_of`, and the imports that are no longer used were dropped. Every test keeps its name and checks the same thing.
10. factory: started docs as self.
11. documenter: Docs: none, as the docs criterion says. I changed no file. The diff is tests only (`tests/application/test_after_agent_edges.py`, `test_opening_journal_edges.py`, `test_tick_stop_details.py`, the new `tests/tick_support.py`, and the helper move in `test_dispatcher.py`, `test_tick.py` and `test_tick_stale_branch.py`). Nothing under `src/factory/` changed.

    Cross-read and found current: `docs/operator-guide.md`. Its stop table (lines 846 and 849) gives `fetch_failed` and `checkout_restore_failed` with git's message as the detail. Line 1401 gives the error-cap log line `error cap reached on <event>: <last error>` for an event without a work item. Both match what the new tests pin.

    I did not run `make check`, because I changed no file outside the documents (none at all). The factory's checks run after this stage.

    Nothing stale noticed. No findings.

    `check`: check: green (not run again: passed on tree d2877c496152 at 2026-10-20T02:35:43Z)
    `secrets`: secrets: green (0.2 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test: no findings.

    I ran the one command under `## Smoke test` from the repository root, exactly as written. It exited 0.

    ```
    None
    Stalled (attempt 1 of 2): the agent gave no valid decision and entry: the entry is empty. Retrying on the next tick.
    git fetch failed (exit 128): fatal: the remote end hung up
    idle:-
    ```

    It met its `Expect:` line. It printed four lines, each the one expected and in the expected order: `None`, the stall note, the `FetchFailed` text, and `idle:-`.

    The acceptance criteria compared with this output:
    - Criterion 1: the stall note's text is exactly the first line criterion 1 expects. `agent_entry` returns `None` for an entry that is only `tester:`, which agrees with the `no_result` stall that criterion pins.
    - Criterion 4: `str(FetchFailed(...))` is exactly the `fetch_failed` detail that criterion 4 expects. `GitError` has the same form, so the `git reset failed (exit 128): ...` detail fits too.
    - Criterion 5: an event without a work item has the key `idle:-`, which agrees with the log line `error cap reached on idle:-: RuntimeError: handler failed`.
    - Criteria 2 and 3 are not touched by the smoke test, and nothing in its output contradicts them.
    - Criteria 6 and 7: the earlier entries record `make check` as green and docs as none. The smoke test gives nothing against them.

    Nothing was changed. Open: nothing.
