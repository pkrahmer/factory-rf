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
  instance: self
  stage: intake
  started_at: '2026-10-20T02:29:31.613661Z'
  lease_duration: 60
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
