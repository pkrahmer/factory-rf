# The undo is removed

## Description

Since F0005 the undo reverted, after every agent run, whatever the agent changed in the factory's own checkout outside its write paths, and named those paths in the entry's closing sentence `The factory undid changes outside the write paths: ...`. Since F0042 the take does the same job the other way round: it copies from the dataset only what the role may write, with the same refusal rule, and leaves the rest where it is; after S0008 (the inline environment and its setting are removed) nothing calls the undo. This story removes `UndoService` and `UndoReport` with their module; the three functions the take shares with it (`is_refused`, `read_baseline`, `restore_work_item`) move into `factory.application.take`, unchanged in what they do; and the entry's closing sentence says what happened: `The factory left out changes outside the write paths: ...`, as F0042's decision 9 planned for this story. The keyword of `agent_entry` that carries those paths is named `left_out` (decision 11 of `feature.md`). What stays: the take with its refusal rule (the write paths at the stage-start commit, the protected paths, every other file directly in an `in-progress/` folder, a `.claude` folder at any depth), the work item's state and journal put back from the stage-start commit, the sidecar rewritten from memory after the take, and the closing paragraph's place and form.

## Interface

Removed whole: `src/factory/application/undo.py`.

`factory.application.take` (`application`): gains `is_refused(path, settings, work_item_path) -> bool`, `read_baseline(...)` and `restore_work_item(...)` with the signatures and behaviour they have in `factory.application.undo` today; nothing else in the module changes.

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
- `tests/application/test_after_agent.py` and `tests/application/test_costs.py`: the constant `UNDONE_PARAGRAPH` holds the new sentence; `test_a_file_written_outside_the_write_paths_is_undone_and_reported`, `test_undone_paths_are_named_in_a_last_paragraph_of_the_entry`, `test_the_own_cost_record_file_is_not_named_as_undone`, `test_the_sidecar_is_written_again_after_the_undo` and `test_an_agent_inside_its_write_paths_is_not_told_of_the_sidecar_undo` keep their names and read it.
- `tests/application/test_stall_environment.py::test_the_stall_module_imports_no_name_of_the_undo` keeps its name and checks that `factory.application.stalls` imports no module `factory.application.undo` (which no longer exists) and no name `UndoService`.
- `tests/application/test_take.py`, `tests/application/test_take_edges.py`, `tests/take_support.py`, `tests/container_support.py`: imports that named `factory.application.undo` name `factory.application.take`.

## Acceptance criteria

1. The removed module and names (rows of one parametrized test): `importlib.util.find_spec("factory.application.undo")` is `None`; `is_refused`, `read_baseline` and `restore_work_item` are attributes of `factory.application.take`; no module under `src/factory` holds the string `undid` or imports a name `UndoService` or `UndoReport`.
2. The sentence (rows of one parametrized test over `agent_entry`): `left_out=["b.py", "a.py"]` ends the entry's text with a blank line and `The factory left out changes outside the write paths: a.py, b.py.`; `left_out=[]` adds no paragraph; a text blank after the role's prefix still gives `None`.
3. A whole stage on the `boundaries` fixture (a tester's stage whose scripted run writes `tests/test_new.py` and `src/forbidden.py`): the entry ends with `The factory left out changes outside the write paths: src/forbidden.py.`, and the result commit holds `tests/test_new.py` and not `src/forbidden.py`.
4. The refusal rule through the take (rows of one parametrized test over `TakeService.take` on `FakeSnapshots`): a changed `.claude/settings.json`, `docs/.claude/x` and `factory/features/F0001-example/in-progress/F0001-S0002-other.md` are each left out and named in `left`; a changed `tests/test_x.py` under the write path `tests/*` is taken; the work item's state and journal are put back from the stage-start commit while its section edit is kept.
5. `make check` stays green.
6. docs: `docs/project-guide/write-guard.md`, *The undo*: replaced by a section *The take's rule* (the refusal rule read at the stage-start commit, applied to the dataset's changes, the work item restored, the sidecar rewritten), and the file's title and its line in `docs/project-guide/README.md`, *The files*, say that it holds the write paths and the take's rule; `docs/project-guide/stage-environment.md`, *The take*: no "as the undo" comparison that names a module that is gone; `docs/operator-guide.md`, *What a stage run shows* and *A stall: the stall note*: the entry's closing sentence is `The factory left out changes outside the write paths: ...`. `docs/decisions.md`: the entries "The undo reads the write paths at the stage-start commit, and a work item the agent breaks is restored whole" and "The sidecar is rewritten from memory after every undo, and a crashed stage's records are discarded with it" each gain one closing line: "The take keeps this rule; the undo went with v1.2 F0044-S0009." `README.md`: none.

## Smoke test

```bash
uv run python -c 'import factory.application.undo' 2>/dev/null && echo present || echo gone
uv run python -c 'from factory.domain.decisions import agent_entry; print(agent_entry(role="tester", stage="tests", decision="doing", text="done", left_out=["b.py", "a.py"]).text.splitlines()[-1])'
```
Expect: two lines: `gone`; `The factory left out changes outside the write paths: a.py, b.py.`

## Journal
