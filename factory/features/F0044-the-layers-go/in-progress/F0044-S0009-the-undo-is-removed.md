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
  started_at: '2026-10-25T19:20:42.386125Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T19:20:42.380099Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T19:20:42.386125Z'
  stage: intake
---

# The undo is removed

## Description

Since F0005 the undo reverted, after every agent run, whatever the agent changed in the factory's own checkout outside its write paths, and named those paths in the entry's closing sentence `The factory undid changes outside the write paths: ...`. Since F0042 the take does the same job the other way round: it copies from the dataset only what the role may write, with the same refusal rule, and leaves the rest where it is; after S0008 (the inline environment and its setting are removed) nothing calls the undo. This story removes `UndoService` and `UndoReport` with their module; the three functions the take shares with it (`is_refused`, `read_baseline`, `restore_work_item`) move into `factory.application.take`, unchanged in what they do; and the entry's closing sentence says what happened: `The factory left out changes outside the write paths: ...`, as F0042's decision 9 planned for this story. The keyword of `agent_entry` that carries those paths is named `left_out` (decision 11 of `feature.md`). What stays: the take with its refusal rule (the write paths at the stage-start commit, the protected paths, every other file directly in an `in-progress/` folder, a `.claude` folder at any depth), the work item's state and journal put back from the stage-start commit, the sidecar rewritten from memory after the take, and the closing paragraph's place and form.

## Interface

Removed whole: `src/factory/application/undo.py`.

`factory.application.take` (`application`): gains `is_refused(path, settings, work_item_path) -> bool`, `read_baseline(...)` and `restore_work_item(...)` with the signatures and behaviour they have in `factory.application.undo` today, together with the private `_is_in_an_in_progress_folder` that `is_refused` calls and the imports the three need; nothing else in the module changes. `factory.application.write_paths.WritePathService`'s docstring names the take alone ("for the take and the undo alike" goes).

`factory.domain.decisions` (`domain`):

```python
_LEFT_OUT_PARAGRAPH = "The factory left out changes outside the write paths: "


def agent_entry(
    *, role: str, stage: str, decision: str, text: str, left_out: Sequence[str]
) -> NewEntry | None: ...
```

- `left_out` paths, when there are any, are named sorted and joined by `, ` in a closing paragraph `The factory left out changes outside the write paths: <paths>.`, after a blank line, as `undone` was; none adds no paragraph.

`factory.application.stage.AfterAgent` (`application`) passes `left_out=` the take's `left` less the own cost records path, as it passed `undone=`.

Tests (the leave is decision 25 of `feature.md`):

- Deleted whole: `tests/application/test_undo.py`, `tests/application/test_undo_nested_claude.py`.
- `tests/undo_support.py`: `undo_stage` and the imports of `UndoReport` and `UndoService` go; its other helpers stay for the take's tests (the module may be renamed under the standing leave).
- `tests/domain/test_agent_entry.py`: its six tests call `agent_entry(..., left_out=...)`; `test_undone_paths_end_the_text_with_a_paragraph_sorted_and_joined` and `test_nothing_undone_adds_no_paragraph` read the new sentence; every test keeps its name.
- `tests/application/test_after_agent.py`, `tests/application/test_costs.py` and F0042's `tests/application/test_stage_environment_calls.py`: the constant `UNDONE_PARAGRAPH` holds the new sentence; `test_after_agent.py::test_undone_paths_are_named_in_a_last_paragraph_of_the_entry` and `::test_the_own_cost_record_file_is_not_named_as_undone`, `test_costs.py::test_an_agent_inside_its_write_paths_is_not_told_of_the_sidecar_undo` and `test_stage_environment_calls.py::test_after_the_agent_the_environment_takes_and_its_report_closes_the_entry` (its rows `one-path` and `own-cost-records-left-out`) keep their names and read it; `test_after_agent.py::test_a_file_written_outside_the_write_paths_is_undone_and_reported` and `test_costs.py::test_the_sidecar_is_written_again_after_the_undo` read no sentence and stay as they are.
- The pre-check ran the suite on a copy with this story's code over S0008's removal of the inline environment: every test that failed is named above.
- `tests/application/test_stall_environment.py::test_the_stall_module_imports_no_name_of_the_undo` keeps its name and checks that `factory.application.stalls` imports no module `factory.application.undo` (which no longer exists) and no name `UndoService`.
- No other test imports `factory.application.undo`: `tests/application/test_take.py`, `tests/application/test_take_edges.py`, `tests/application/test_container_environment.py`, `tests/application/test_container_environment_take.py`, `tests/application/test_container_sync_origin.py`, `tests/application/test_stall_container.py` and `tests/container_support.py` import only `tests/undo_support.py`'s helpers that stay; they change only when the tester renames that module under the standing leave.

## Acceptance criteria

1. The removed module and names (rows of one parametrized test): `importlib.util.find_spec("factory.application.undo")` is `None`; `is_refused`, `read_baseline` and `restore_work_item` are attributes of `factory.application.take`; no module under `src/factory` holds the string `undid` or imports a name `UndoService` or `UndoReport`.
2. The sentence (rows of one parametrized test over `agent_entry`): `left_out=["b.py", "a.py"]` ends the entry's text with a blank line and `The factory left out changes outside the write paths: a.py, b.py.`; `left_out=[]` adds no paragraph; a text blank after the role's prefix still gives `None`.
3. A whole stage on the `boundaries` fixture (a tester's stage whose scripted run writes `tests/test_new.py` and `src/forbidden.py` and overwrites the work item's own `.costs.jsonl`): the entry ends with `The factory left out changes outside the write paths: src/forbidden.py.` and names no `.costs.jsonl`, and the result commit holds `tests/test_new.py`, not `src/forbidden.py`, and the factory's own cost records, not the agent's text.
4. The refusal rule through the take (rows of one parametrized test over `TakeService.take` on `FakeSnapshots`): under the write paths `["*"]`, so that each refusal is the rule's own and not the write paths', a changed `.claude/settings.json`, `src/.claude/skills/x/SKILL.md` and `factory/features/F0001-example/in-progress/F0001-S0002-other.md` are each left out and named in `left`, and a changed `src/.claudex/notes.md` is taken; under the write paths `["tests/*"]` a changed `src/b.py` is left out and a changed `tests/test_x.py` is taken; the work item's state and journal are put back from the stage-start commit while its section edit is kept.
5. `make check` stays green.
6. docs: `docs/project-guide/write-guard.md`, *The undo*: replaced by a section *The take's rule* (the refusal rule read at the stage-start commit, applied to the dataset's changes, the work item restored, the sidecar rewritten), and the file's title and its line in `docs/project-guide/README.md`, *The files*, say that it holds the write paths and the take's rule; `docs/project-guide/stage-environment.md`, *The take*: no "as the undo" comparison that names a module that is gone; `docs/operator-guide.md`, *What a stage run shows* and *A stall: the stall note*: the entry's closing sentence is `The factory left out changes outside the write paths: ...`; *A project's own skills*: a nested `.claude/` write is left out by the take, not removed by an undo. `docs/project-guide/stages.md`, *Starting a stage*, *Opening a work item*, *`StallService.stall`*, *After the agent run* and *`StageFinisher.finish`*: the take in place of the undo, `agent_entry(..., left_out=)` and the new sentence. `docs/project-guide/costs.md`, *When a record is created, completed and committed*: the sidecar is rewritten after the take, with no undo. `docs/project-guide/git-and-hosting.md`, *The git wrapper*, *Restoring the checkout* and *Which part uses which operation*: no undo among the users of `changed_paths`, `revert_paths` and `reset_to` (the take's restore of a broken work item uses `revert_paths`). `docs/project-guide/README.md`, *Shared test helpers*: the line of `undo_support.py` (or its new name) without `undo_stage` and without the undo. `docs/decisions.md`: the entries "The undo reads the write paths at the stage-start commit, and a work item the agent breaks is restored whole" and "The sidecar is rewritten from memory after every undo, and a crashed stage's records are discarded with it" each gain one closing line: "The take keeps this rule; the undo went with v1.2 F0044-S0009."; in the entry "One snapshot instead of many layers", the line "The journal sentence stays `The factory undid changes outside the write paths: ...` until F0044 (decision 9 of the feature F0042)." gains at its end: "Since F0044-S0009 it is `The factory left out changes outside the write paths: ...`." `README.md`: none.

## Smoke test

```bash
uv run python -c 'import factory.application.undo' 2>/dev/null && echo present || echo gone
uv run python -c 'from factory.domain.decisions import agent_entry; print(agent_entry(role="tester", stage="tests", decision="doing", text="done", left_out=["b.py", "a.py"]).text.splitlines()[-1])'
```
Expect: two lines: `gone`; `The factory left out changes outside the write paths: a.py, b.py.`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
