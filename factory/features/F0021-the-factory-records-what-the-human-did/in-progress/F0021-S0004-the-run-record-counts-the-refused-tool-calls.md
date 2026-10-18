---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 238
comments_read: [6256436044, 6256513714, 6256619702]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T23:19:33.245967Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T23:19:33.251788Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-18T23:19:47.534417Z'
  stage: intake
  run: c54d58610dec4f2cbf8af679bc1f225e
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-18T23:22:06.368183Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-18T23:22:24.094146Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-18T23:22:44.679907Z'
  stage: intake
  run: e86c73b195fc495ea203ad5b02c50d3f
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-18T23:23:05.284248Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-18T23:25:28.838357Z'
  stage: tests
  run: 16f9f49dddac449ba375c31e7aab49a2
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-18T23:25:48.968346Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-10-18T23:28:57.890228Z'
  stage: doing
  run: 4027b9c7b2b44040af468653dbb45792
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-10-18T23:30:13.040371Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-18T23:30:30.680153Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-18T23:30:47.973393Z'
  stage: doing
  run: f9bda80d1fd44fe881302a37e0ff4779
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-18T23:31:08.929129Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-10-18T23:34:12.960771Z'
  stage: tests
  run: bfb5de6234ab40fe882e0713f04143c7
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-18T23:34:33.079295Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-10-18T23:36:27.814298Z'
  stage: doing
  run: 039b355ce7fa42399fb0a408535647c4
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-18T23:36:47.830345Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-10-18T23:37:28.830740Z'
  stage: review
  run: 9e260e01706f423992caae9e3c171e88
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-18T23:37:48.935842Z'
  stage: docs
- number: 21
  speaker: documenter
  kind: result
  at: '2026-10-18T23:39:10.311507Z'
  stage: docs
  run: 141d889a390d4e4f9b19b90f91cb624a
- number: 22
  speaker: factory
  kind: started
  at: '2026-10-18T23:39:30.592537Z'
  stage: smoke-test
- number: 23
  speaker: smoke-tester
  kind: result
  at: '2026-10-18T23:40:05.972198Z'
  stage: smoke-test
  run: 06b62efc8d6049c3a237611fbb471364
- number: 24
  speaker: factory
  kind: started
  at: '2026-10-18T23:40:26.274674Z'
  stage: doing
- number: 25
  speaker: coder
  kind: question
  at: '2026-10-18T23:40:51.585004Z'
  stage: doing
  run: 20db31ba2cae4443be179bf0c4dfaa4c
  blocked: question
- number: 26
  speaker: human
  kind: comment
  at: '2026-10-18T23:42:07.239096Z'
  stage: doing
- number: 27
  speaker: factory
  kind: started
  at: '2026-10-18T23:42:24.814329Z'
  stage: doing
- number: 28
  speaker: coder
  kind: result
  at: '2026-10-18T23:44:33.320397Z'
  stage: doing
  run: 998f4f0fa9e04f10861c44e3b3751b9d
---

# The run record counts the refused tool calls

## Description

The agent runtime already reports the tool calls it refused, but the factory's run record does not keep them. This story gives the run record room for what the runtime reports: the cost record of a completed run gains `denials`, the number of tool calls the agent runtime reports as refused (the result's `permission_denials`, whatever refused them: a permission or deny rule of the runtime's settings or anything else the runtime reports there; under opencode, F0020 fills the same list), and `denied_paths`, the files those calls named (the feature's decision 8). Both are optional and left out of the sidecar line when unknown, so every line written before stays as it is; F0020 adds its spend-limit waits beside them in the same way (decision 9). A refusal the runtime does not report as a refused tool call, such as a write the kernel refuses, is only text in a tool's output inside the agent's transcript; it is not parsed and not counted. The stop records are S0003's.

## Interface

`factory.domain.agent_runs.PermissionDenial` (`domain`): a new field `path: str | None = None`, the file the refused call named.

`factory.adapters.claude_runtime` (`adapters`): `_denials` sets `path` to the denial's `tool_input["file_path"]` when `tool_input` is an object and that value is a string, or else its `tool_input["notebook_path"]` when that value is a string; otherwise `None`. `detail` stays as today.

`factory.domain.cost_records.CostRecord` (`domain`): two new last fields, after `instance`:

```python
denials: NonNegativeInt | None = None
denied_paths: list[str] | None = None
```

- A `started` record with either set is refused, like its other measures.

`factory.application.costs.CostRecorder.complete` (`application`): the completed record gets `denials=len(result.permission_denials)` and `denied_paths` the `path` of each denial that has one, each path once, in the order the runtime reported them; for a run that ended `died` or `time_limit` (no reply from the runtime) both stay `None`.

`factory.adapters.cost_records_jsonl` (`adapters`): the line leaves `denials` out when it is `None` and `denied_paths` out when it is `None`, as it leaves out a `None` `instance`; when set they are written after `instance`, and the reader reads them back.

Test modules (new): `tests/adapters/test_claude_runtime_denial_paths.py`, `tests/domain/test_cost_record_denials.py`, `tests/application/test_costs_denials.py`, `tests/adapters/test_cost_records_jsonl_denials.py`. Earlier tests this story changes, under the feature's decision 14: `tests/adapters/test_claude_runtime_resume.py`, the expected `Write` denial gaining `path="x"`, and nothing else.

## Acceptance criteria

1. `_denials` of the `claude -p` runtime's reply, rows of one parametrized test: a `Write` with `{"file_path": "src/a.py"}` gives `path` `src/a.py`; a `NotebookEdit` with `{"notebook_path": "n.ipynb"}` gives `n.ipynb`; a call with both keys gives the `file_path`; a `Bash` with `{"command": "git push"}` gives `None`; `{"file_path": 3}` gives `None`; `{"file_path": 3, "notebook_path": "n.ipynb"}` gives `n.ipynb`; a `tool_input` that is a string gives `None`. `detail` is as today in every row.
2. `CostRecord`, rows of one parametrized test: a `completed` record with `denials=0` and with `denials=2` and `denied_paths=["src/a.py"]` is accepted; `denials=-1` is refused; a `started` record with `denials=0`, and one with `denied_paths=[]`, is refused.
3. `CostRecorder.complete`, rows of one parametrized test over the end reasons: a `completed`, a `budget` and a `no_result` run with the denials `Write src/a.py`, `Bash` (no path), `Edit src/a.py`, `Write docs/b.md` give `denials` 4 and `denied_paths` `["src/a.py", "docs/b.md"]`; a `completed` run without denials gives `denials` 0 and `denied_paths` `[]`; a `died` and a `time_limit` run give `None` for both.
4. The cost record writer, rows of one parametrized test: a record with both `None` is written as today, without `denials` and `denied_paths` keys; a record with `denials` 2 and `denied_paths` `["src/a.py"]` is written with `"denials":2,"denied_paths":["src/a.py"]` after `instance`; `denials` 2 with `denied_paths` `None` is written with only `"denials":2`; `denials` 0 with `denied_paths` `[]` is written with `"denials":0,"denied_paths":[]`; each line read back equals its record.
5. `make check` stays green.
6. docs:
    - `docs/operator-guide.md`, *The cost table* or *What a work item cost*: the sidecar's `denials` and `denied_paths`, and that only the tool calls the runtime reports as refused are in them, not a refusal that is only text in a tool's output.
    - `docs/project-guide.md`, *Cost records*: the two new fields and their `None`.

## Smoke test

```bash
uv run -q python -c '
import json
from datetime import UTC, datetime
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordWriter
from factory.domain.cost_records import CostRecord

fields = dict(
    run="a" * 32, work_item="F0001-S0001", stage="doing", role="coder", attempt=0,
    started_at=datetime(2026, 10, 18, 10, 0, tzinfo=UTC),
)
started = CostRecord(status="started", **fields)
done = CostRecord(
    status="completed", duration_seconds=1.0, end_reason="completed",
    denials=2, denied_paths=["src/a.py"], **fields,
)
for line in JsonLinesCostRecordWriter().render([started, done]).splitlines():
    record = json.loads(line)
    print(record.get("denials", "absent"), record.get("denied_paths", "absent"))
'
```

Expect: two lines, `absent absent` and `2 ['src/a.py']`.

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: Format check passed. Questions:

   1. Criterion 1 / Interface: `_denials` takes `file_path` "or else" `notebook_path`, "when that value is a string". When `file_path` is present but not a string (`{"file_path": 3, "notebook_path": "n.ipynb"}`), does `path` become `n.ipynb` or `None`? The row `{"file_path": 3}` alone doesn't decide it. I would choose: `file_path` is used only when it is a string, otherwise fall back to `notebook_path` (`n.ipynb`). Please state the rule and add a row for it.

   2. Criterion 4 / Interface: the writer leaves `denials` out when `None` and `denied_paths` out when `None`, each on its own. No row has one set and the other `None`, so a coder who ties the two together passes. I would add rows: `denials=2` with `denied_paths=None` (only `"denials":2` written) and `denials=0` with `denied_paths=[]` (written as `"denials":0,"denied_paths":[]`, so an empty list is kept and not left out). Please confirm or reword.
4. 2026-10-18 human: 1. Yes: `file_path` is used only when it is a string, otherwise fall back to `notebook_path` (`n.ipynb` in your row); add that row.
   2. Yes: add both rows (`denials=2` with `denied_paths=None` writes only `"denials":2`; `denials=0` with `denied_paths=[]` writes `"denials":0,"denied_paths":[]`).
5. factory: started intake as self.
6. intake: accepted
   - Interface: names concrete modules and fields (`PermissionDenial.path`, `claude_runtime._denials`, `CostRecord.denials`/`denied_paths`, `CostRecorder.complete`, `cost_records_jsonl`) and the test modules. I carried in the human's answer (journal entry 4, point 1): `file_path` is used only when it is a string, otherwise `notebook_path` is tried. I reworded that Interface sentence to say so.
   - Criteria: each is one parametrized test function. Each rule has both sides: a path, no path, a non-string value and a string `tool_input` for `_denials`; accepted and refused values, and a `started` record, for `CostRecord`; the three reported end reasons, a run with no denials, and `died`/`time_limit` for `complete`. Order, once-only paths and path-less denials are all covered by the criterion 3 rows. From entry 4, point 1, I added the row `{"file_path": 3, "notebook_path": "n.ipynb"}` giving `n.ipynb` to criterion 1. From entry 4, point 2, I added two rows to criterion 4: `denials=2` with `denied_paths=None` writes only `"denials":2`, and `denials=0` with `denied_paths=[]` writes `"denials":0,"denied_paths":[]`.
   - Smoke test: runnable. It uses `JsonLinesCostRecordWriter().render`, and its `Expect:` line (`absent absent` and `2 ['src/a.py']`) can be checked against the output. I did not run it. The record fields in it match the Interface.
   - Architecture: the changes sit in the right layers (domain DTOs, application recorder, adapters for the runtime and the JSONL writer). The runtime-specific parsing stays in the adapter.
   - Scope: within the feature's S0004 and decision 8. The stop records and F0020's items are not touched. The change to the earlier test `test_claude_runtime_resume.py` is covered by decision 14.
7. factory: started tests as self.
8. tester: Wrote one parametrized test per acceptance criterion, from the Interface and the criteria. Every row the criteria list is a row of its test, including the two rows the human added in entry 4.

   - criterion 1: tests/adapters/test_claude_runtime_denial_paths.py::test_a_denial_names_the_file_or_notebook_path_of_its_call. It runs the `claude -p` stand-in with one denial per row. It reuses `_reply`, `_request` and `_runtime` from tests/adapters/test_claude_runtime_resume.py, as earlier jsonl tests import helpers from test_cost_records_jsonl. Every row's expected `detail` is `json.dumps(tool_input, sort_keys=True)`, as today.
   - criterion 2: tests/domain/test_cost_record_denials.py::test_only_a_completed_record_carries_a_non_negative_denial_count_and_paths. It builds the record through a variable typed `type[BaseModel]`. Accepted rows: completed with 0, and with 2 plus `["src/a.py"]`. Refused rows: -1, started with `denials=0`, started with `denied_paths=[]`.
   - criterion 3: tests/application/test_costs_denials.py::test_completed_record_counts_the_denials_and_their_paths_once_each_in_order. Rows: completed, budget and no_result with the four denials; completed with none; died; time_limit. It checks both the returned record and the sidecar read back.
   - criterion 4: tests/adapters/test_cost_records_jsonl_denials.py::test_the_writer_writes_the_denials_after_the_instance_only_when_set. Each record has `instance` set, so the test can check that the denial keys come after it. Rows: neither key, both, count only, 0 with `[]`. Each rendered line is parsed back and must equal its record.
   - criteria 5 and 6 (make check, docs): no test, by their nature.

   Files created: the four test modules above. Earlier test changed, under the feature's decision 14 as the Interface names it: tests/adapters/test_claude_runtime_resume.py, where the expected `Write` denial gains `path="x"`. Nothing else in that file changed.

   `make test`: tests/application/test_costs_denials.py could not be collected, because `PermissionDenial` has no `path` field yet. That module builds the denials at module level. The other new tests fail on the missing `path`, `denials` and `denied_paths` fields. No module failed to import. `make lint` is green. The type check was skipped, as this stage allows.

   Nothing open.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/application/test_costs_denials.py - pydantic_core._pydantic_core....
9. factory: started doing as self.
10. coder: Stopped with the code done. Every criterion's test passes except two failures in tests, which I may not edit. Lint, types, layers, sast, secrets and licenses are green. Other checks pass too: `test_claude_runtime_denial_paths.py`, `test_cost_record_denials.py`, `test_cost_records_jsonl_denials.py` and the changed `test_claude_runtime_resume.py`.

    Built (in the working tree):
    - `src/factory/domain/agent_runs.py`: `PermissionDenial.path: str | None = None`.
    - `src/factory/adapters/claude_runtime.py`: `_denied_path` takes `file_path` when it is a string, or else `notebook_path`. Otherwise it gives `None`. `_denials` sets `path` from it, and `detail` is unchanged.
    - `src/factory/domain/cost_records.py`: `denials` and `denied_paths` after `instance`. Both are added to the measures a `started` record refuses.
    - `src/factory/application/costs.py`: `_completed` sets `denials=len(...)` and `denied_paths` (each path once, in report order, via `_denied_paths`). For `died`/`time_limit` both are `None`.
    - `src/factory/adapters/cost_records_jsonl.py`: the line leaves out `instance`, `denials` and `denied_paths` when they are `None`. This is one loop instead of a second and third copy of the `instance` branch.

    Main choice: `_completed` decides "no reply" from the end reason (`died`, `time_limit`), as the Interface says. I rejected the alternative of a `dict[str, object]` helper merged into the record. CLAUDE.md forbids dicts crossing a function boundary, so the condition is inlined.

    The two failing tests:

    1. `tests/application/test_costs_denials.py::test_completed_record_counts_the_denials_and_their_paths_once_each_in_order`, rows `completed` and `completed-none`. The test builds `AgentRunResult(end_reason="completed", ...)` without `decision` and `entry`. `AgentRunResult` already refuses that ("a completed run needs a decision"), so the row fails before it reaches `CostRecorder`. Options:
       - (a) The tester gives those two rows a `decision` and an `entry`, for example `decision="review", entry="done"`.
       - (b) Relax `AgentRunResult`. That is out of scope.

       I would choose (a).

    2. `tests/application/test_costs.py::test_the_sidecar_is_written_again_after_the_undo[overwritten]` and `[deleted]`, an earlier story's test. Its expected completed `CostRecord` leaves `denials`/`denied_paths` as `None`. The Interface says a completed run without denials gives `denials=0, denied_paths=[]`, so the test contradicts the Interface. The Interface's list of earlier tests this story changes names only `test_claude_runtime_resume.py`. Options:
       - (a) Allow the tester to add `denials=0, denied_paths=[]` to that test's expected record.
       - (b) Change the Interface so a completed run without denials keeps `None`. That would contradict criterion 3's `completed-none` row.

       I would choose (a).

    Noticed, not touched: `tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject[tests-doing]` failed once under the full parallel `make check`. It passed three times when run alone. It looks like a load-dependent flake unrelated to this work item.

    Refactor pass: I read the diff and nothing needs changing. The journal did not change the meaning of the task beyond what intake already wrote into the Description.
11. 2026-10-18 human: 1. (a): the tester gives the rows `completed` and `completed-none` of `test_completed_record_counts_the_denials_and_their_paths_once_each_in_order` a valid `decision` and `entry` (e.g. `decision="review", entry="done"`).
    2. (a): leave, in the form of decisions 13 and 14: in `tests/application/test_costs.py::test_the_sidecar_is_written_again_after_the_undo`, the expected completed `CostRecord` gains `denials=0, denied_paths=[]`, and nothing else. Any other expected completed `CostRecord` of an earlier test gains the two fields in the same way; the tester names each file in its entry.
12. factory: started doing as self.
13. coder: The human's answer in entry 11 calls for test changes. I may not make those, so I'm handing back to the tester with nothing new in code. The implementation from entry 10 is already committed on the branch: `src/factory/domain/agent_runs.py`, `src/factory/adapters/claude_runtime.py`, `src/factory/domain/cost_records.py`, `src/factory/application/costs.py` and `src/factory/adapters/cost_records_jsonl.py`. I did not rerun `make check` this round, because nothing in `src/` changed.

    Test changes for the tester:
    1. `tests/application/test_costs_denials.py::test_completed_record_counts_the_denials_and_their_paths_once_each_in_order`: rows `completed` and `completed-none` each get a valid `decision` and `entry` (e.g. `decision="review", entry="done"`) in their `AgentRunResult`. Nothing else changes.
    2. `tests/application/test_costs.py::test_the_sidecar_is_written_again_after_the_undo`: the expected completed `CostRecord` gains `denials=0, denied_paths=[]`. Nothing else changes.

    Per the same answer, any other earlier test that expects a completed `CostRecord` produced by `CostRecorder.complete` gains the two fields the same way. The tester names each file it changes.

    Earlier test modules that build completed records, for the tester to check: `tests/application/test_recovery_crash.py`, `tests/domain/test_bills.py`, `tests/domain/test_bills_model_time.py`, `tests/adapters/test_cost_records_jsonl.py` and `tests/bill_support.py`. The ones that build a record by hand rather than through `complete` stay valid as they are, since both fields default to `None`.

    What the journal changed: no task meaning. It only changed the test data, so I left the Description as it is.

    Still open from entry 10 and not touched: the possibly flaky `tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject[tests-doing]`.
14. factory: started tests as self.
15. tester: I made the two test changes from the human's answer in entry 11, which the coder handed over in entry 13. No code changed.

    1. `tests/application/test_costs_denials.py::test_completed_record_counts_the_denials_and_their_paths_once_each_in_order`: for the `completed` and `completed-none` rows, the `AgentRunResult` now gets `decision="review"` and `entry="done"`. The other end reasons still get `None`, so the `died`, `time-limit`, `budget` and `no-result` rows build the same result as before. I wrote the two values as conditional keyword arguments instead of unpacking a dict, so `mypy --strict` checks each field against its type. Nothing else in that test changed. I wrote this test in entry 8.
    2. `tests/application/test_costs.py::test_the_sidecar_is_written_again_after_the_undo`, an earlier story's test: the expected completed `CostRecord` gains `denials=0, denied_paths=[]` and nothing else. This is under the human's leave in entry 11.

    Other earlier tests: entry 11 also allows the same change to any other expected completed `CostRecord` of an earlier test, but none needed it. The other tests that call `CostRecorder.complete` (`test_cost_image.py`, `test_cost_instance.py`, `test_costs_model_seconds.py`) do not compare a whole completed record, and they pass as they are. No other earlier test file changed.

    The criterion mapping is the same as in entry 8:
    - criterion 1: tests/adapters/test_claude_runtime_denial_paths.py::test_a_denial_names_the_file_or_notebook_path_of_its_call
    - criterion 2: tests/domain/test_cost_record_denials.py::test_only_a_completed_record_carries_a_non_negative_denial_count_and_paths
    - criterion 3: tests/application/test_costs_denials.py::test_completed_record_counts_the_denials_and_their_paths_once_each_in_order
    - criterion 4: tests/adapters/test_cost_records_jsonl_denials.py::test_the_writer_writes_the_denials_after_the_instance_only_when_set

    Files changed: tests/application/test_costs_denials.py and tests/application/test_costs.py. No new files. Every module imported.

    Checks: `make lint` is green. `make test` is green (`test: green (45.5 s)`, coverage 99.08 %). I ran `make test` twice: my first command filtered out all of its output, so I ran it again to see the result.

    Still open from entries 10 and 13, not touched: the possibly flaky `tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject[tests-doing]`.

    `lint`: lint: green (0.0 s)
    `test`: test: green (41.6 s)
16. factory: started doing as self.
17. coder: This round needed no code change. The tester's changes from entry 15 make the implementation committed in entry 10 pass, and `make check` is green (`check: green`, coverage 99.08 %).

    What was built, already on the branch:
    - `src/factory/domain/agent_runs.py`: adds `PermissionDenial.path: str | None = None`.
    - `src/factory/adapters/claude_runtime.py`: `_denied_path` returns `file_path` if it is a string, otherwise `notebook_path` if that is a string, otherwise `None`. `_denials` fills `path` from it; `detail` is unchanged.
    - `src/factory/domain/cost_records.py`: adds `denials: NonNegativeInt | None` and `denied_paths: list[str] | None` after `instance`. Both are on the list of measures a `started` record refuses.
    - `src/factory/application/costs.py`: `_completed` sets `denials=len(result.permission_denials)`. `denied_paths` comes from `_denied_paths`, which keeps each path once in the order reported. For a run that ended `died` or `time_limit` both stay `None`.
    - `src/factory/adapters/cost_records_jsonl.py`: a single loop drops `instance`, `denials` and `denied_paths` from the line when they are `None`.

    Main choice: `_completed` decides whether the runtime replied by looking at the end reason (`died`, `time_limit`), which is what the Interface says. I rejected building the two fields in a separate `dict` helper and merging it into the record, because CLAUDE.md does not allow a dict to cross a function boundary.

    Refactor pass: I read the whole diff against `main` again and found nothing to change.

    What the journal changed: entries 11 and 15 changed only test data, not what the task means, so the Description stays as it is.

    Noticed, not touched: in an earlier round, `tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject[tests-doing]` failed once under the full parallel run and then passed alone. It did not fail this time. It may be a flaky test that depends on load, and it is unrelated to this work item.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
18. factory: started review as self.
19. reviewer: no findings

    What I checked:
    - Criterion 1: `tests/adapters/test_claude_runtime_denial_paths.py` has all seven rows, including the human's row from entry 4 (`file_path` 3 falling back to `notebook_path`). Each row also checks `detail` as today. `_denied_path` in `src/factory/adapters/claude_runtime.py` tries `file_path` and then `notebook_path`, each only when it is a string, and gives `None` for any `tool_input` that is not an object.
    - Criterion 2: `tests/domain/test_cost_record_denials.py` tests `NonNegativeInt` on both sides (0 accepted, -1 refused). A `started` record is refused with `denials=0` and with `denied_paths=[]`, so the started check tests for `None`, not truthiness. Wrong-typed fields go through `type[BaseModel]`.
    - Criterion 3: `tests/application/test_costs_denials.py` covers all six end-reason rows and reads the sidecar back. The `completed-none` row (0 and `[]`) against the `died` and `time_limit` rows (`None`) pins the end-reason check in `_completed`. Order and once-only are pinned by `["src/a.py", "docs/b.md"]` from four denials. `dict.fromkeys` keeps each path once in report order without a hand-written helper.
    - Criterion 4: `tests/adapters/test_cost_records_jsonl_denials.py` has all four rows, including entry 4's count-only and zero-and-empty rows. It checks the keys come after a set `instance` and that each line reads back. In `cost_records_jsonl.py`, the writer now leaves out all three optional keys in one loop instead of copying the `instance` branch.
    - Criterion 5: entry 17 records `check: green` and `duplicates: 0 new`.
    - Architecture: `path` is on the domain DTO, the runtime-specific parsing stays in the adapter, the counting is in the application, and no dict crosses a function boundary. Security: no suppression markers and no strings built into commands. Docstrings: `PermissionDenial` and `CostRecord` describe the new fields.
    - Work item: the Description matches the code. Entries 10 and 17 state the main choice (deciding "no reply" from the end reason) and what was rejected. The docs criterion still names what the operator guide and the project guide must say.

    Earlier tests:
    - tests/adapters/test_claude_runtime_resume.py: the story's Interface names it with the human's word (the feature's decision 14). The only change is the expected `Write` denial gaining `path="x"`.
    - tests/application/test_costs.py: the human's answer in journal entry 11, point 2. The only change is the expected completed `CostRecord` in `test_the_sidecar_is_written_again_after_the_undo` gaining `denials=0, denied_paths=[]`.
20. factory: started docs as self.
21. documenter: Docs written from the docs criterion; no findings. The code matches the Interface and the criteria.

    Files changed:
    - `docs/operator-guide.md`: new section "Refused tool calls in the sidecar", between *An unknown cost* and *The cost line*. It covers `denials` and `denied_paths`, when they are absent, and that only tool calls the runtime reports as refused are counted, not a refusal that is only text in a tool's output. It also says `factory-bill` does not print them. I took that from the cost table section, which lists no such column; I did not check the code.
    - `docs/project-guide.md`, *Cost records*:
      - the field list, the `started` rule, a `denials` >= 0 rule and the "complete" bullet now name the two fields. The bullet says how `complete` fills them, including `died` and `time_limit` giving `None` and a replied run without denials giving `0` and `[]`.
      - the line-format paragraph says the writer leaves out `instance`, `denials` and `denied_paths` when each is `None`.
      - the runtime section (`detail` sentence) now says how a denial's `path` is chosen: `file_path` if it is a string, else `notebook_path`, else `None`.

    Cross-read and found current: the README, the `AgentRunResult` paragraph in `docs/project-guide.md` (it only mentions `permission_denials`), the guard section (it reads `tool_input.file_path` by its own rules, unrelated), and `docs/decisions.md` (nothing about the cost record fields).

    I ran no examples, because I wrote none. I ran no `make check`, because I changed only documents; the factory's run after this stage is the gate.

    The sidecar `.costs.jsonl` of this work item shows as modified in the working tree. That is the factory's own file, not mine.

    Stale text that is not mine: none seen. The coder's note about `tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject[tests-doing]`, which failed once under load, is still open and unrelated to this work item.

    `check`: check: green
    `documents`: documents ok
22. factory: started smoke-test as self.
23. smoke-tester: Ran the one command under `## Smoke test` exactly as written, from the repository root. I fixed nothing.

    Command 1 (`uv run -q python -c '…'`, which renders a `started` and a `completed` record and prints `denials` and `denied_paths` for each line):

    ```
    Traceback (most recent call last):
      File "<string>", line 16, in <module>
      File "/work/checkout/src/factory/adapters/cost_records_jsonl.py", line 90, in render
        _check_new_run(record, number, seen_runs)
      File "/work/checkout/src/factory/adapters/cost_records_jsonl.py", line 39, in _check_new_run
        raise CostRecordFormatError(number, f"duplicate run: {record.run}")
    factory.domain.errors.CostRecordFormatError: line 2: duplicate run: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    exit: 1
    ```

    Expect: two lines, `absent absent` and `2 ['src/a.py']`. **Not met.** The command exits 1 and prints neither line.

    Why it fails: the script gives both records the same `run` (`"a" * 32`, from the shared `fields`). `JsonLinesCostRecordWriter.render` refuses a second line for the same run in `_check_new_run`, because a run's line is replaced when it completes. That check is already on `origin/main` (`git show origin/main:src/factory/adapters/cost_records_jsonl.py`, lines 36–39 and 89). This story's diff to the module only changes `_line_of_record`, which now leaves out `instance`, `denials` and `denied_paths` when each is `None`. So the error comes from the smoke test's data, not from this story's code.

    I checked the acceptance criteria against what the smoke test showed. It contradicts none of them, because the error happens before any line is written. It shows nothing about criterion 4 either way.

    Findings:
    1. Command 1. Expected: two lines, `absent absent` and `2 ['src/a.py']`. Observed: `CostRecordFormatError: line 2: duplicate run: aaaa…`, exit 1, no output lines. Criterion: none is contradicted; the command errors.

    For the next stage: the code can't fix this without dropping the duplicate-run check, which is already on `main` and outside this story. Two ways out need the human, because `## Smoke test` is theirs:
    - (a) Give the two records in the smoke test different `run` values (for example `"b" * 32` for `done`). This is the one I would choose.
    - (b) Render each record in its own `render` call.

    The coder should probably ask the human (R8) rather than change code.
24. factory: started doing as self.
25. coder: The smoke test fails because of its own data, not because of this story's code. I changed nothing this round, and the code from entry 10 is unchanged on the branch.

    Finding (entry 23): the script under `## Smoke test` gives the `started` and the `completed` record the same `run` (`"a" * 32` from the shared `fields`). `JsonLinesCostRecordWriter.render` (`src/factory/adapters/cost_records_jsonl.py`, `_check_new_run`) refuses a second line for the same run with `CostRecordFormatError: line 2: duplicate run`. That check is already on `origin/main`, and this story's diff to the module touches only `_line_of_record`. The only way to fix it in code would be to drop the duplicate-run check, which is outside this story and would break the rule that a run's line is replaced when it completes.

    I checked the expectation with distinct runs. I ran the same script with `run="a" * 32` for `started` and `run="b" * 32` for `done`, and it printed exactly the two expected lines, `absent absent` and `2 ['src/a.py']`.

    Question: `## Smoke test` is the human's text, so how should it change?
    - (a) Give the two records different `run` values: take `run` out of `fields` and pass `run="a" * 32` to `started` and `run="b" * 32` to `done`. The `Expect:` line stays as it is. This is the one I would choose.
    - (b) Render each record in its own `render` call. The output is the same, but the script reads less like one sidecar.
    - (c) Leave the smoke test as it is and accept the failure. I would not choose this.

    If you choose (a) or (b), the Description itself is unaffected. Only the `## Smoke test` block changes, and nothing in `src/` or `tests/` does.

    Noticed, not touched: the possibly flaky `tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject[tests-doing]` from entry 10 is still open.
26. 2026-10-18 human: (a): give the two records different `run` values (take `run` out of `fields`; `run="a" * 32` for `started`, `run="b" * 32` for `done`); the `Expect:` line stays. The reviewer has leave to make exactly this edit to `## Smoke test` on its next run, and nothing else; the code goes forward unchanged.
27. factory: started doing as self.
28. coder: No code changed this round. In entry 26 the human answered the smoke-test finding (entry 23): option (a). The two records in `## Smoke test` get different `run` values, and the reviewer has leave to make exactly that edit on its next run. The code goes forward unchanged. That edit to `## Smoke test` is the reviewer's, so I did not make it.

    What was built, already on the branch since entry 10, with paths:
    - `src/factory/domain/agent_runs.py`: `PermissionDenial.path: str | None = None`.
    - `src/factory/adapters/claude_runtime.py`: `_denied_path` gives `file_path` when it is a string, or else `notebook_path` when that is a string, or else `None`. `_denials` fills `path` from it, and `detail` is unchanged.
    - `src/factory/domain/cost_records.py`: new fields `denials` and `denied_paths` after `instance`. A `started` record refuses both.
    - `src/factory/application/costs.py`: `_completed` sets `denials` and `denied_paths`. `denied_paths` keeps each path once, in the order the runtime reported it. Both stay `None` for `died` and `time_limit`.
    - `src/factory/adapters/cost_records_jsonl.py`: one loop leaves `instance`, `denials` and `denied_paths` out of the line when each is `None`.

    Main choice (unchanged): `_completed` decides from the end reason whether the runtime replied. I rejected building the fields in a `dict` helper and merging it in, because CLAUDE.md does not allow a dict to cross a function boundary.

    Since then a merge from `origin/main` came into the branch. I ran `make check` again on it, and it is green (`check: green`, coverage 99.08 %). Refactor pass: nothing to change, because the diff to `src/` is the same as before.

    What the journal changed: only the smoke test's data, not what the task means. The Description stays as it is.

    Noticed, not touched: `tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject[tests-doing]` failed once under load in an earlier round. It may be a flaky test, and it is unrelated to this work item.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
