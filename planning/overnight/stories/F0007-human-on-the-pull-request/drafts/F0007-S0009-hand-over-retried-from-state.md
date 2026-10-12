# The hand-over at the approval, retried from state

## Assignment (as of log entry 1)

Build the handler of `hand_over` events. When a work item reaches an approval stage, the pull request must show the human what to decide: the handler assembles the pull request description by code from fixed sections of the story and the latest `result` entries of the tester, reviewer, documenter and smoke tester (found by speaker and kind in the journal's data, never by the text), replaces the description, marks the pull request ready for review, posts the cost table (read from the cost record file in the repository), and only then records `handed_over = <stage>` in the work item and pushes. Because the record comes last and every effect is safe to repeat (the description is replaced, the draft flag is set, the post is keyed), a failure or a kill anywhere leaves `handed_over` unset, the watcher raises the event again, and the next tick completes the hand-over without a second post. A hand-over that fails every time is reported on the pull request at the error cap. It covers ST1.2 and ST1.3, uses SI1.1 (speaker and kind as data) and keeps kept thing 11 (draft says the factory works, ready says the human decides) and kept thing 20 (the bill is posted at the approval). No morning observation.

## Interface

`src/factory/domain/sections.py` (adds one constant next to `ACCEPTANCE_CRITERIA` and `SMOKE_TEST`, in the same form)

```python
DESCRIPTION = "Description"
```

`src/factory/domain/hand_over.py`

```python
HAND_OVER_CLOSING = (
    "Merge to accept the story. To send it back, close the pull request with a comment that says "
    "what should change; a close without one is answered with a question. Comments written while "
    "the story waits here are recorded in its journal and become the reason if you then close."
)
REPORT_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Tests", "tester"),
    ("Review", "reviewer"),
    ("Documentation", "documenter"),
    ("Smoke test", "smoke-tester"),
)

def hand_over_description(document: WorkItemDocument, commits: Sequence[CommitInfo]) -> str: ...
```

`src/factory/domain/post_texts.py` (adds one function)

```python
def cost_table_post(table: str) -> str: ...
```

`src/factory/application/handlers/hand_over.py`

```python
class HandOverHandler:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `cost_table_post(table)` is `Cost of this work item so far`, a blank line, and the table.
- `hand_over_description(document, commits)` is made of these parts, in this order, joined by one blank line, and ends with one newline:
  1. a line `## Description`, a blank line, and `section_text(document.body, DESCRIPTION)`;
  2. a line `## Acceptance criteria`, a blank line, and `section_text(document.body, ACCEPTANCE_CRITERIA)`;
  3. for each `(title, speaker)` in `REPORT_SECTIONS`, in that order: a line `## <title>`, a blank line, and the text of the work item's latest journal record with that speaker and kind `result` (found with `last_record(document, speaker=speaker, kind="result")`, its text read with `entry_text`);
  4. a line `## Commits`, a blank line, and a fenced block with one line per commit, in the order given: the first seven characters of the commit id, a space, and the subject;
  5. `HAND_OVER_CLOSING`.
  A section that is missing, and a speaker with no `result` record, give the text `none`.
- `HandOverHandler.handle` takes `target_of(event)` and `require_pull_request(target, "hand_over")`. It calls `WorkItemRecorder.check_out(branch)` and reads the work item. A stage that is not an approval stage of `definition` raises `CannotHandle("hand_over", ...)`. When `state.handed_over == state.stage` there is nothing to do and it returns without any effect.
- Otherwise, in this order: read the cost records from `cost_records_path(snapshot.path)` in the checkout; take `Git.log("origin/<branch>", since="origin/main")` as the commits; `HostingService.set_description(number, hand_over_description(...))`; `HostingService.set_draft(number, False)`; post `cost_table_post(cost_table(bills_by_stage(records)))` with `PostKey(work_item=<id>, kind="cost_table", n=str(<number of the latest record of kind result, 0 when there is none>))`; and last, set `handed_over` to the stage and record with the subject `commit_subject(id, "handed over at <stage>")`.
- Every failure leaves `handle` by raising. Nothing is recorded before the last step.

Tests: `tests/domain/test_hand_over.py` and `tests/application/handlers/test_hand_over.py`. The journal records of the test documents are built independently of the body's visible text; the dispatcher tests are built as in S0008.

## Acceptance criteria

1. `hand_over_description` contains the headings `## Description`, `## Acceptance criteria`, `## Tests`, `## Review`, `## Documentation`, `## Smoke test` and `## Commits`, in that order, with `HAND_OVER_CLOSING` as its last paragraph, and ends with one newline.
2. The Description and Acceptance criteria sections hold the story's own sections, verbatim; a section the story lacks gives `none`.
3. A report section holds the text of the latest `result` record by its speaker; when the tester has two `result` records, the later one is used.
4. A report section whose speaker has no `result` record holds `none`.
5. A report section is found by the records' data and not by the visible text: an entry whose visible line names another speaker is still attributed to the speaker in its record.
6. The Commits section is a fenced block with one line per commit in the order given, each the first seven characters of the id, a space and the subject; with no commit the block is empty.
7. `cost_table_post("T")` is `Cost of this work item so far`, a blank line and `T`.
8. `HAND_OVER_CLOSING` is exactly the text of the Interface and states that a merge accepts, that a close with a comment sends the story back, and that a close without one is answered with a question.
9. `HandOverHandler.handle` for a work item at the approval sets the pull request's description to `hand_over_description` of the work item and of `Git.log("origin/<branch>", since="origin/main")`, and marks the pull request ready for review (not a draft).
10. It posts one comment on the pull request: `cost_table_post(cost_table(bills_by_stage(records)))` of the cost records committed on the work item's branch, with key kind `cost_table` and `n` equal to the number of the latest `result` record; the post is the same in a fresh clone of the repository.
11. It then records `handed_over == <stage>` in the work item and pushes: the remote branch gains one commit, and the journal and the other state fields are as they were.
12. The record comes last: when `post_comment` fails, `handle` raises `HostingServiceError`, the description is already set, and the remote branch holds no `handed_over`.
13. After that failure, handling the event again completes the hand-over and leaves exactly one cost table post (ST1.2).
14. A kill at `after-post` leaves one cost table post and no `handed_over`; handling the event again records `handed_over` and leaves exactly one cost table post.
15. A work item whose `handed_over` already equals its stage is handled without any effect: no description change, no post, no commit.
16. A work item at a stage that is not an approval raises `CannotHandle` with kind `hand_over`, and nothing is changed or posted.
17. For a work item whose state has no pull request, `handle` raises `CannotHandle` with kind `hand_over`, and nothing is changed or posted.
18. A hand-over that fails every time (ST1.3), dispatched four times on the same remote state, gives the outcomes `error`, `error`, `reported`, `capped`; the handler is called three times; the pull request has no factory post of kind `error` after the second dispatch, exactly one after the third and still exactly one after the fourth.
19. make check stays green.
20. docs: `docs/operator-guide.md` describes the pull request description at the approval (its sections, that it replaces what the human wrote there), the cost table post, that a hand-over that fails is retried on the next tick and reported once at the error cap; the other three documents do not change.

## Demo

```bash
uv run python -c "
from datetime import UTC, datetime
from factory.domain.git import CommitInfo
from factory.domain.hand_over import HAND_OVER_CLOSING, hand_over_description
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState
records = [JournalRecord(number=1, speaker='human', kind='created'), JournalRecord(number=2, speaker='tester', kind='result')]
body = '# T\n\n## Description\n\nBuild it.\n\n## Acceptance criteria\n\n1. One.\n\n## Journal\n\n1. 2026-10-12 human: created.\n2. tester: wrote the tests.\n'
document = WorkItemDocument(state=WorkItemState(stage='approval', journal=records), body=body)
commit = CommitInfo(commit='a' * 40, parents=[], subject='feat: build it', author='coder', committed_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC))
text = hand_over_description(document, [commit])
print([line for line in text.splitlines() if line.startswith('## ')])
print(text.split('## Tests')[1].split('## Review')[0].strip())
print(text.split('## Review')[1].split('## Documentation')[0].strip())
print('aaaaaaa feat: build it' in text, text.rstrip().endswith(HAND_OVER_CLOSING))
"
```
Expect: four lines: `['## Description', '## Acceptance criteria', '## Tests', '## Review', '## Documentation', '## Smoke test', '## Commits']`; then `wrote the tests.`; then `none` (no reviewer record); then `True True`.

## Log (append only)

1. 2026-10-12 human: created.
