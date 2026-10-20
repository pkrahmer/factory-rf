# New work goes in the order it became due

## Description

Tier 4 of the evaluation (new work) ranks its candidates by `work_item_order(id)`, and a due feature by `(<feature id>, 1, "")`, so the lowest feature id always wins. On 2026-10-20 F0037's acceptance waited three hours behind F0020, F0029 and F0030, one of whose stories had been started after the acceptance was due (the feature's decision 1). This story ranks the candidates of tier 4 by their queue time instead: the time a work item became due, read from `origin/main`'s history (decision 2). A story's queue time is its start; a due feature's queue time, and its running acceptance's, is the change that made the acceptance due. The id order stays for equal queue times and for candidates without one (decision 3). Unchanged: tiers 1 to 3, so a waiting work item still holds back all new work and a held claim still means nothing else runs; the attempts cap; the board's and `factory-watch`'s row order (decisions 4 and 5). It is for the human, who expects work to be taken up in the order it became due.

## Interface

`src/factory/domain/evaluation.py` (`domain`):

```python
class EvaluationInput(BaseModel):
    ...
    queued_at: dict[WorkItemId | FeatureId, UtcDatetime] = {}
```

- `queued_at` maps a work item id (a story in progress or a running acceptance) or a feature id (a feature in `due`) to its queue time. It defaults to empty, so every construction written before stays valid; a key that is neither a work item id nor a feature id is refused with `ValidationError`.
- Tier 4 takes the candidate with the earliest queue time. Candidates with equal queue times go in `work_item_order` (for a due feature, `(<feature id>, 1, "")`, as today). A candidate without a queue time goes after every candidate with one, and those without one go in `work_item_order`. So an `EvaluationInput` without queue times ranks exactly as today.
- Nothing else in `evaluate` reads `queued_at`: tiers 1 to 3 and the attempts cap stay as they are, and the first candidate at the attempts cap still gives `ask` (`attempts cap`).

`src/factory/application/watcher.py` (`application`):

- `Watcher.evaluate` fills `queued_at` from `origin/main`, for both the tick's watcher and the observer's:
  - a story in progress: the committer time of the newest commit on `origin/main` that added its file at its `in-progress/` path (a move from `backlog/` counts as an addition there). A later commit that only changes the file does not change it.
  - a feature in `due`, and a running acceptance by its own feature (whose status is no longer `due` once it is opened): the committer time of the newest commit on `origin/main` that changed a file of one of the feature's stories (not of an acceptance) in its `backlog/`, `in-progress/` or `done/`. A commit that changes only the feature's `feature.md` or one of its acceptance reports does not change it.
  - a candidate for which no such commit is found gets no entry.
- The times are read through the `Git` interface. When the reading needs more than `Git.log` offers today, `Git` (`src/factory/application/git.py`) and `GitCli` (`src/factory/adapters/git_cli.py`) gain one optional parameter of `log` or one new operation, tested in `tests/adapters/`; every existing call keeps its meaning.
- A test that depends on which of two queue times is earlier sets the committer times of its commits (`GIT_COMMITTER_DATE`, as `tests/adapters/test_git_cli_history.py` does), so no test depends on the second its commits fall into.

Tests: the tester writes the new tests under `tests/domain/` and `tests/application/`. No earlier test changes (the feature's decision 7).

## Acceptance criteria

1. The earliest queue time wins whatever the ids (rows of one parametrized test of `evaluate`, nothing waiting and nothing claimed): the due feature `F0037` at 06:49:45 against the story `F0030-S0001` at 07:42:34 gives `acceptance_due` for `F0037`; the same due feature against the story `F0029-S0002` at 06:48:44 gives `run` for `F0029-S0002`; the story `F0041-S0001` at 10:00:00 against `F0027-S0003` at 10:00:01 gives `run` for `F0041-S0001`; the running acceptance `F0041-A0002` at 12:56:32 against the story `F0027-S0002` at 12:56:42 gives `run` for `F0041-A0002`.
2. Equal queue times go in work item order, one second apart do not (rows of one parametrized test): `F0001-S0001` and `F0002-S0001` at the same time give `F0001-S0001`, and with `F0002-S0001` one second earlier give `F0002-S0001`; the due feature `F0002` and the story `F0003-S0001` at the same time give `acceptance_due` for `F0002`; the story `F0002-S0002` and the running acceptance `F0002-A0001` at the same time give the story.
3. A candidate without a queue time goes last (rows of one parametrized test): `F0001-S0001` without one and `F0009-S0001` with one give `F0009-S0001`; the due feature `F0001` without one and the story `F0009-S0001` with one give `run` for `F0009-S0001`; with no queue times at all, `F0001-S0001` and `F0009-S0001` give `F0001-S0001`, and the due feature `F0002` and `F0003-S0001` give `acceptance_due` for `F0002`, as today.
4. `EvaluationInput` takes `queued_at` keyed by work item ids and feature ids, defaults it to empty, and refuses a malformed key such as `F002` with `ValidationError` (rows of one parametrized test).
5. The other tiers and the attempts cap are unchanged (rows of one parametrized test): a blocked work item with the earliest queue time and a runnable later one give `idle`, its detail naming the blocked work item; the same work item no longer blocked goes before the later one; the earliest candidate at the attempts cap gives `ask` (`attempts cap`) though a later one could run; a claimed work item held by another instance gives `idle` whatever the queue times.
6. The watcher reads a story's queue time from its start (one test on a real remote, with set committer times): a story moved into `in-progress/` at T1 and edited on `main` at T2 has the queue time T1; a story started at T1, moved back to `backlog/` and started again at T3 has T3.
7. The watcher reads a due feature's queue time from the change that made it due (one test on a real remote, with set committer times): a feature whose last story is archived at T4 has T4, also after a later commit that changes only its `feature.md`; its running acceptance, once opened, has T4 as well.
8. The tick runs the older work first, against the id order (rows of one parametrized test of `Tick` on a real remote, with set committer times): with the feature `F0002` due at T5 and the story `F0001-S0001` started after T5, the tick's event is `acceptance_due` for `F0002`; with the feature `F0002` due at T5 and the story `F0003-S0001` started before T5, it is `run` for `F0003-S0001`.
9. `make check` stays green.
10. docs: `docs/project-guide/watching.md`, *The four tiers*, tier 4: the candidates are ranked by their queue time, as this story's Interface defines it, with `work_item_order` for equal times and after every timed candidate for one without a time; the sentence "So a feature's acceptance comes after its own stories and before the next feature's" goes, since a due acceptance now ranks by the time it became due. `docs/operator-guide.md`, the paragraph that begins "A running acceptance is a work item like a story and is picked by the same order, by id": new work goes in the order it became due (a story from its start on `main`, an acceptance from the archive of its feature's last story), equal times and work without a known time in id order; a waiting work item and a held claim still come first; a clock that is off moves the order by as much (the feature's decision 6). The board's row order stays as the operator guide states it. `docs/decisions.md`: a new entry *New work goes in the order it became due*, dated with the story: the decision of the feature's decisions 2 and 3, the reasons (the time a work item has waited, read from the remote, the only truth, so every instance and `factory-watch` see the same order; nothing new is recorded), and as rejected the backlog order of today, which let a low feature id started late overtake work that had waited for hours, and a commit's position in the first-parent history. `README.md`: none.

## Smoke test

```bash
uv run pytest tests/domain/test_evaluation_due.py tests/application/test_watcher_acceptance.py tests/application/test_tick.py 2>&1 | tail -1
```
Expect: one line that reports only passed tests, `<n> passed in <seconds>s`, and no failed or errored test

```bash
uv run python - <<'PY'
from datetime import UTC, datetime
from factory.domain.evaluation import EvaluationInput, evaluate
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, initial_state
definition = PipelineDefinition(
    contract="1.0",
    stages={"intake": StageDefinition(role="intake", next=["done"]), "done": StageDefinition()},
    roles={"intake": RoleDefinition(write_paths=["{work_item}"])},
)
story = WorkItemSnapshot(
    id="F0030-S0001", path="factory/features/F0030-x/in-progress/F0030-S0001-x.md",
    folder="in-progress", branch="work-item/F0030-S0001", branch_commit=None,
    document=WorkItemDocument(state=initial_state("intake"), body="# T\n"),
)
def facts(queued):
    return EvaluationInput(definition=definition, snapshots=[story], main_commit="a" * 40, due=["F0037"], queued_at=queued)
def never(number):
    raise AssertionError(number)
at = lambda h, m, s: datetime(2026, 10, 20, h, m, s, tzinfo=UTC)
for queued in ({}, {"F0037": at(6, 49, 45), "F0030-S0001": at(7, 42, 34)}):
    event = evaluate(facts(queued), never, lambda state: "none")
    print(event.key)
PY
```
Expect: two lines, `run:F0030-S0001` (no queue times: the id order of today) and `acceptance_due:F0037` (the due feature waited longer)

## Journal
