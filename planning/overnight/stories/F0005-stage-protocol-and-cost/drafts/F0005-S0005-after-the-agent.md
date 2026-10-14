# After the agent: the branch, the undo, the entry, the form again

## Assignment (as of log entry 1)

Build what the factory does with an agent run's outcome before it decides anything: it believes what it observes, not what the agent reports (kept thing 8). It tests that the checkout is still on the work item's branch, turns every result it cannot keep into a stall (the service of S0004), applies the undo and the restore of F0004 so that the agent's changes outside its write paths and to the state and journal are gone, writes the agent's entry with speaker and kind decided by code (the agent's text with a leading name removed), adds a paragraph naming what was undone, and checks the story form again so that only a finding that was not there before the run stalls. The entry is built here and appended by the stage's result commit (S0007); only in the form-stall case it is appended here, above the stall. Covers GH2.5 as the stage protocol applies it (a run that died or reached its `time_limit` becomes a stall through the service of S0004) and the undo and restore for the runs that complete; keeps kept things 1 (code writes speaker and kind), 4 (state and journal restored), 5 (the form is checked before and after) and 8.

## Interface

`src/factory/domain/decisions.py` (grown by this story; its tests are in a module of their own)

```python
def agent_entry(
    *, role: str, stage: str, decision: str, text: str, undone: Sequence[str]
) -> NewEntry | None: ...
```

`src/factory/application/stage.py` (grown by this story)

```python
class AgentAftermath(BaseModel):
    started: StartedStage
    request: AgentRunRequest
    result: AgentRunResult
    decision: str
    document: WorkItemDocument
    entry: NewEntry
    undo: UndoReport
    form_findings: list[FormFinding]

class AfterAgent:
    def __init__(
        self, boundaries: Boundaries, instance: str, definition: PipelineDefinition
    ) -> None: ...
    def process(self, launched: LaunchedStage) -> AgentAftermath | StallResult: ...
```

Types: `NewEntry` from `factory.domain.journal`, `UndoReport` from `factory.application.undo`, `StallResult` from `factory.application.stalls`, `cost_records_path` from `factory.domain.paths`. `AgentAftermath` is frozen and forbids unknown keys. `AgentAftermath.document` is the work item after the undo and the restore: the stage-start state (claim included) and journal, with the agent's changes to the rest of the body kept when the stage's role may write the work item (otherwise the undo has put the whole file back and lists it in `reverted`, F0004-S0005 c12); the entry is not yet in it.

- `agent_entry` returns `NewEntry(speaker=role, kind=..., text=..., on=None)`. `kind` is `question` when `decision == QUESTION`, else `result`. The text is `text` stripped, with one leading `<role>:` or `<stage>:` removed (the role first; the colon directly after the name; whitespace after it dropped) and stripped again. When the result is blank it returns `None`. When `undone` is not empty, the text ends with a blank line and `The factory undid changes outside the write paths: <the paths sorted and joined by ", ">.`
- `AfterAgent.process` does these steps in this order and stops at the first that stalls: (1) the checkout's branch (`Git.status().branch`) must be `started.branch`, else stall `left_branch`; (2) a result that is not `ok` stalls with `stall_reason_of(result)`, its detail the first permission denial as `denied: <tool>: <detail>` when there is one (the first of several); (3) a decision that is not in `request.allowed_decisions` stalls with `decision_not_allowed`, its detail `decision '<decision>' is not one of <the allowed decisions joined by ", ">`; (4) `UndoService.undo(stage_start, path)`, then the work item file is read back; (5) `agent_entry` with `undone` the sorted reverted and deleted paths of the report, leaving out `cost_records_path(started.path)` (the factory rewrites that file itself after the undo, S0008, so it is no change worth telling the agent about); a `None` result stalls with `no_result` and the detail `the entry is empty`; (6) `StoryFormChecker.findings(document)`; a finding that is new stalls with `form_invalid`, its detail the messages of the new findings joined by `; ` (in the order of the findings after the run), and the document passed to the stall holds the agent's entry appended, so the entry stays above the stall entry.
- A finding is new when its message, with every run of digits replaced by `#`, occurs more often among the findings after the run than among `started.findings`; the messages embed line numbers (`the code block opened at line 12 is not followed by an "Expect:" line`), which move when the agent adds a paragraph above. Of equal messages the first ones are taken as old and the later ones as new.
- Every stall goes through `StallService.stall` with `StallContext(work_item, stage, branch, path, stage_start=started.stage_start, document=<see above or None>, pull_request=started.pull_request)`, and the stage's `attempts` rises once per `process`, never twice.
- `AgentAftermath.form_findings` holds every finding after the run, new or old.

Tests: `tests/domain/test_agent_entry.py` (new, so that S0004's `tests/domain/test_decisions.py` stays as it is), `tests/application/test_after_agent.py`. The latter starts stages with `StageLauncher` and the fake agent runtime; `ScriptedRun.writes` tampers with the work item file, writes outside the write paths and breaks the form; a subclass of `ObservingRuntime` in this story's own test module switches the branch; `tests/observing_runtime.py` stays as S0003 wrote it. Criteria 8, 14, 16, 17 and 18, in which the agent edits the work item's body, run at a stage whose role may write the work item (`review`, role `reviewer`, write paths `{work_item}` in the fixture's pipeline definition); at `tests` the undo puts the whole file back. Unless a criterion breaks the form, the work items are complete stories (every section of the fixture's form, criteria ending with `make check` … `green` and `docs:`, a smoke-test block followed by `Expect:`), because the fixture's backlog story `# First story` has findings.

## Acceptance criteria

1. For a completed result with an allowed decision, `process` returns an `AgentAftermath` whose `decision` is the result's decision, whose `result` is the runtime's result and whose `started` is the launched stage's.
2. When the checkout is not on the work item's branch after the run, `process` returns a `StallResult` with reason `left_branch`.
3. For a result that ended `died`, `time_limit`, `budget` or `no_result`, `process` returns a `StallResult` with the same reason, and `attempts` rose by exactly one.
4. When a result that ended `died` carries a permission denial for tool `Bash` with detail `git push origin main`, the stall note contains `denied: Bash: git push origin main`; with a second denial for tool `Edit`, the note names the first and not the second.
5. A decision that is not allowed (`review` at a stage whose `next` is `doing`) stalls with `decision_not_allowed`; the journal entry of the stall names the decision and the allowed decisions.
6. A file the agent wrote outside its write paths is gone from the work tree after `process`, and `AgentAftermath.undo` lists it under `reverted` or `deleted`.
7. An agent that rewrote the work item file's state and journal (another `stage`, `attempts` and `claim`, a changed journal) leaves `AgentAftermath.document` with the stage-start state, claim included, and the stage-start journal records.
8. An agent's own edit inside the work item file's body (a paragraph added under a section) is kept in `AgentAftermath.document` and in the work tree.
9. `AgentAftermath.entry` has speaker equal to the stage's role, kind `result` and the agent's text for a decision that is not `question`.
10. For the decision `question` the entry's kind is `question` and its speaker is the role.
11. A leading `<role>:` and a leading `<stage>:` in the agent's text are removed once (`tester: wrote tests` gives `wrote tests`), whitespace after the colon dropped; the same words in the middle of the text, and a name without a colon, stay.
12. When the undo reverted or deleted paths, the entry text ends with a blank line and `The factory undid changes outside the write paths: <paths sorted, joined by ", ">.`; when nothing was undone the text has no such paragraph.
13. An entry that is blank after the prefix is removed (`"tester: "`) stalls with `no_result` and the detail `the entry is empty`.
14. When the agent breaks the story form (its `## Acceptance criteria` section is deleted), `process` returns a `StallResult` with reason `form_invalid`, and in the pushed journal the agent's record (the role, kind `result`) comes directly before the `factory` stall record.
15. A form finding that exists before and after the run does not stall (`process` returns an `AgentAftermath` and `form_findings` lists it), and a finding the agent fixed does not stall either.
16. A finding whose message carries a line number does not stall when only the number changed: a smoke-test code block without `Expect:` exists before the run, the agent adds a paragraph above it, and `process` returns an `AgentAftermath`.
17. A second finding of the same kind is new: the agent adds a second smoke-test code block without `Expect:` to a story that had one, and `process` returns a `StallResult` with reason `form_invalid`.
18. The note of a `form_invalid` stall holds the messages of the new findings joined by `; `: the agent adds two new findings (it deletes the criteria section and the smoke test section) and the note contains both messages with `; ` between them, the old finding's message not among them.
19. `AgentAftermath.form_findings` lists all findings after the run, and a stage that ends clean has an empty list.
20. The own work item's cost-record file is not an undone path: an agent that overwrote the sidecar at `cost_records_path(path)` and wrote `src/b.py` outside its write paths gets an entry whose paragraph names `src/b.py` and not the sidecar; an agent that wrote only the sidecar gets an entry without the paragraph.
21. `AgentAftermath` is frozen and forbids unknown keys: assigning to `decision` (through `setattr`, the field's name in a variable) and building it with an unknown field raise `ValidationError`.
22. make check stays green.
23. docs: `docs/project-guide.md` describes what the factory does after an agent run, in order (branch test, stall on a result it cannot keep, undo and restore, the entry written by code with its prefix removed, the form checked again so that only a new finding stalls, new meaning more often than before once digits are masked), and that the agent's state and journal edits are always discarded and the own cost-record file is not named in the entry.

## Demo

```bash
uv run python -c "
from factory.domain.decisions import agent_entry
entry = agent_entry(role='tester', stage='tests', decision='doing', text='tester: wrote the tests', undone=['src/b.py', 'README.md'])
print(entry.speaker, entry.kind)
print(entry.text)
print(agent_entry(role='tester', stage='tests', decision='question', text='tester:   ', undone=[]))
"
```
Expect: 5 lines. Line 1 is `tester result`. Lines 2 to 4 are `wrote the tests`, an empty line, and `The factory undid changes outside the write paths: README.md, src/b.py.` Line 5 is `None`.

```bash
uv run pytest tests/application/test_after_agent.py
```
Expect: the last line reports `passed` and the output contains neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
