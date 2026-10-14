# Questions recorded, then posted

## Assignment (as of log entry 1)

Build the handler of `ask` events, so that every question reaches the human in two steps: the question is first recorded in the work item (committed and pushed), then posted on the pull request with a key made from the recorded journal entry's number, so that a repeat or a restart posts nothing twice. Four questions are recorded by other code and only posted here: an agent's question (`blocked` is `question`), the round-cap question (`round_cap`), the send-back question (`send_back`, recorded by S0005) and the crash-cap question (`crash_cap`, recorded by F0008). The attempts-cap question is recorded and then posted by this handler: when a work item has used all its attempts, the handler writes a `question` entry for the factory, sets `blocked` to `attempts_cap`, pushes, and posts the entry. The story keeps kept things 10 (a question is recorded and committed, then posted) and 11 (one post per stop, saying what each answer will do), and applies R22 and GH3.4's rule that a repeated post is a no-op to these posts. No morning observation.

## Interface

`src/factory/domain/post_texts.py` (adds one function)

```python
def attempts_cap_question(stage: str, attempts: int, last_stall: str) -> str: ...
```

`src/factory/application/handlers/questions.py`

```python
class AskHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `attempts_cap_question(stage, attempts, last_stall)` is `Stage <stage> stalled <attempts> times. The last time: <last_stall>`, then a blank line, then `Comment anything to retry: the attempts go back to 0 and the stage runs again. Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.`
- `handle` takes `target_of(event)` and `require_pull_request(target, "ask")`.
- A recorded question: when `state.blocked` is `question`, `attempts_cap`, `round_cap`, `crash_cap` or `send_back`, the question is the work item's latest journal record of kind `question` (found with `last_record`), whatever records follow it: the human's comments are recorded after a question that waits to be posted (S0007), and the post stays keyed to the question's own number. `handle` posts `<speaker>: <text>` with `HostingService.post_comment(number, text, PostKey(work_item=<id>, kind=<the blocked value>, n=str(<the record's number>)))`, where the text is `entry_text(document, <number>)` of the snapshot's document. It makes no commit. A `blocked` value with no `question` record raises `CannotHandle("ask", ...)`.
- The attempts-cap question: when `state.blocked` is unset and `state.attempts >= definition.attempts_cap`, `handle` first records, then posts. It calls `WorkItemRecorder.check_out(branch)`, reads the work item, takes the text of its latest `stall` entry as `last_stall`, appends `NewEntry(speaker=FACTORY, kind="question", text=attempts_cap_question(state.stage, state.attempts, last_stall))`, sets `blocked="attempts_cap"`, and records with the subject `commit_subject(id, "attempts cap question recorded")`. It then posts the new entry like any recorded question, with kind `attempts_cap`. A work item with no `stall` record raises `CannotHandle("ask", ...)` before anything is recorded.
- A work item with `blocked` unset and `attempts` below the cap raises `CannotHandle("ask", ...)`: it is not waiting for a question.
- A failing call (`HostingServiceError`, `GitError`, `PushFailed`) leaves the handler by raising; the recorded entry stays recorded.

F0006-S0002's `question_posted` compares the post's `n` with the number of the latest `question` record, so a comment recorded after the question does not make the watcher raise `ask` again.

Tests: `tests/application/handlers/test_questions.py` and, for the text, `tests/domain/test_question_post_texts.py` (a new file: `tests/domain/test_post_texts.py` is F0003-S0003's). The fixtures are those of S0001; the snapshots carry a document whose body holds the journal, so that `entry_text` finds the entries.

## Acceptance criteria

1. `attempts_cap_question("doing", 2, "the agent gave no result")` returns `Stage doing stalled 2 times. The last time: the agent gave no result`, a blank line, and `Comment anything to retry: the attempts go back to 0 and the stage runs again. Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.`
2. With `blocked == "question"` and a recorded question entry by `reviewer`, `handle` posts one comment on the work item's pull request whose text is `reviewer: ` followed by the entry's text and whose key is `PostKey(work_item=<id>, kind="question", n=<the entry's number>)`.
3. For `blocked` equal to `round_cap`, `crash_cap`, `send_back` and `attempts_cap` (the question already recorded, as after a failed post), `handle` posts with a key whose `kind` is that value and whose `n` is the number of the latest question entry, and makes no commit (four cases, one test).
4. When the journal holds several question entries, the post is made for the latest one.
5. With `blocked == "question"` and its question already posted, handling the same event again posts nothing more, and the work item's remote branch does not move.
6. With `blocked` set and no `question` record in the journal, `handle` raises `CannotHandle` with kind `ask` and posts nothing.
7. With `blocked` unset and `attempts` equal to `definition.attempts_cap` (2), `handle` pushes one commit to the work item's branch that holds a new journal entry (speaker `factory`, kind `question`, text `attempts_cap_question(stage, attempts, <the text of the latest stall entry>)`) and `blocked == "attempts_cap"`.
8. After recording it, `handle` posts the new entry's text with the prefix `factory: ` and the key `PostKey(kind="attempts_cap", n=<the new entry's number>)`.
9. With `blocked` unset and `attempts` one below the cap (1), `handle` raises `CannotHandle` with kind `ask` and records and posts nothing; with `attempts` above the cap (3) it records and posts as it does at the cap (two cases).
10. With `blocked` unset and `attempts` at the cap but no `stall` record, `handle` raises `CannotHandle` with kind `ask` and records nothing.
11. The attempts-cap question is recorded before it is posted: when `post_comment` fails, `handle` raises `HostingServiceError`, the work item's remote branch already holds the entry with `blocked == "attempts_cap"`, and no factory post exists.
12. After that failure, handling the event read again from the remote branch posts the question once and writes no second entry.
13. A kill at `after-post` leaves one post, and handling again posts nothing more.
14. A kill at `before-push` while the attempts-cap question is recorded leaves the remote branch as it was and no post; handling again records one entry and posts once.
15. For a work item whose state has no pull request, `handle` raises `CannotHandle` with kind `ask` and reason `work item <id> has no pull request`, and records and posts nothing.
16. When comment entries follow the latest question entry in the journal (the human wrote while the question waited to be posted), `handle` posts the question's own text with the key `n` equal to the question entry's number, not the last entry's number.
17. make check stays green.
18. docs: `docs/operator-guide.md` lists the questions the human can see on a pull request (an agent's, the round cap, the attempts cap, the send-back and the crash cap), how to answer each (a comment answers, a close discards the story or, at the approval, sends it back), and that a question is recorded before it is posted; `docs/project-guide.md` states that every post carries a key made from the recorded entry, so that a repeat posts nothing.

## Demo

```bash
uv run python -c "
from types import SimpleNamespace
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.handlers.questions import AskHandler
from factory.domain.events import Event
from factory.domain.journal import JournalRecord
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import attempts_cap_question
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
print(attempts_cap_question('doing', 2, 'the agent gave no result'))
definition = PipelineDefinition(contract='1.0', roles={'coder': {'write_paths': ['src/*']}}, stages={'review': {'role': 'coder', 'next': ['done']}, 'done': {}})
hosting = FakeHostingService()
pr = hosting.create_pull_request('work-item/F0001-S0001', 'F0001-S0001: demo', 'body', draft=True)
records = [JournalRecord(number=1, speaker='human', kind='created'), JournalRecord(number=2, speaker='reviewer', kind='question')]
body = '# T\n\n## Journal\n\n1. 2026-10-12 human: created.\n2. reviewer: Send it back?\n'
state = WorkItemState(stage='review', blocked='round_cap', pull_request=pr.number, journal=records)
document = WorkItemDocument(state=state, body=body)
snapshot = WorkItemSnapshot(id='F0001-S0001', path='factory/features/F0001-x/in-progress/F0001-S0001-y.md', folder='in-progress', branch='work-item/F0001-S0001', branch_commit='1' * 40, document=document)
event = Event(kind='ask', work_item=snapshot, remote_state='1' * 40)
handler = AskHandler(SimpleNamespace(hosting=hosting), definition)
handler.handle(event)
handler.handle(event)
posts = hosting.factory_posts(pr.number)
print(len(posts))
print(posts[0].body.splitlines())
"
```
Expect: first the attempts-cap question as two paragraphs: `Stage doing stalled 2 times. The last time: the agent gave no result`, a blank line, then `Comment anything to retry: the attempts go back to 0 and the stage runs again. Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.`; then the line `1` (the second `handle` posted nothing); then the list `['reviewer: Send it back?', '', '<!-- factory -->', '<!-- factory key=F0001-S0001:round_cap:2 -->']`.

## Log (append only)

1. 2026-10-12 human: created.
