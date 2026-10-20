# The tests pin the refusal reason after the role's own result, and the board's absent and blocked values

## Description

The mutation sweep of 2026-10-19 left two gaps in `factory.domain.acceptance` and two in `factory.domain.board`. When the human closes an acceptance's pull request, the refusal reason is the human's comments after the acceptance reviewer's last `result`. No test has a later record that could be taken for that result: a `result` of another role, or a `question` of the reviewer itself. So a reason that started after *any* last result, or after the reviewer's last record of any kind, would pass. And no test pins the whole body a refusal writes when the report has a journal but no `## Recommendation`, whose last line ends in exactly one newline. On the board, no test has a work item without a state (a backlog story), whose row shows stage, blocked, claim and pull request as absent, and no line shows a blocked work item. This story pins these as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003. The sweep's dead guard at `acceptance.py:332` stays as it is (decision 4 of `feature.md`); `_work_item_line`'s time-zone survivor is equivalent in a container that runs in UTC.

## Interface

No module under `src/factory/` changes. The behaviour pinned (`domain`):

- `factory.domain.acceptance.refusal_reason(document, role)`: the human's `comment` records numbered after the last record whose speaker is `role` *and* whose kind is `result`; a later `result` of another speaker and a later record of `role` of another kind move nothing.
- `factory.domain.acceptance.book_refusal(document, role=..., on=..., bill=...)`: uses that reason; with a `## Journal` and no `## Recommendation` the new section stands right before the journal, and the body ends in the `done` entry and one newline.
- `factory.domain.board.work_item_row(snapshot)`: a snapshot whose document has no state gives `None` for `stage`, `blocked`, `claim`, `running_since` and `pull_request`.
- `factory.domain.board.render_board(features, rows)`: a `None` value is written `-`, a blocked row `blocked=<reason>`.

Tests (the tester writes them): `tests/domain/test_acceptance_refusal_edges.py` and `tests/domain/test_board_absent_values.py`. The first builds its reports with `_document` of `tests/domain/test_acceptance_booking.py` (a report whose journal holds the entries, a human's line dated `2026-10-12`), which the tester moves to a shared module, `tests/acceptance_support.py`, under the standing leave of `CLAUDE.md` (*Tests*): `tests/domain/test_acceptance_booking.py` then imports it from there and keeps every test's name and what it checks. No other earlier test changes.

`ROLE` is `acceptance-reviewer`. The bill is `bill([])`, whose `cost_line` is `0 runs, 0.0 min, 0 turns, 0 tokens in (0 more from cache), 0 out, $0.00`, and `on` is `date(2026, 10, 12)`.

## Acceptance criteria

1. The reason starts after the role's own last result (rows of one parametrized test; each a `_document` of the entries, the expected `refusal_reason(document, ROLE)`):
   - `(factory, started, "started.")`, `(ROLE, result, "not accepted")`, `(human, comment, "Too wide.")`, `(tester, result, "red")`, `(human, comment, "Cut the second story.")`: `Too wide. Cut the second story.` (a later result of another role).
   - `(factory, started, "started.")`, `(ROLE, result, "not accepted")`, `(human, comment, "Too wide.")`, `(ROLE, question, "Which story?")`, `(human, comment, "Cut the second story.")`: `Too wide. Cut the second story.` (a later question of the role).
   - `(factory, started, "started.")`, `(ROLE, result, "not accepted")`, `(human, comment, "Too wide.")`, `(ROLE, result, "still not accepted")`, `(human, comment, "Cut the second story.")`: `Cut the second story.` (a later result of the role itself).
2. The refusal books that reason (one test): `book_refusal` of the first report of criterion 1 with `role=ROLE`, `on` and the bill gives exactly the body `# Acceptance of Todo service\n\n## Recommendation\n\nRefused by the human on 2026-10-12: Too wide. Cut the second story.\n\n## Journal\n\n1. factory: started.\n2. acceptance-reviewer: not accepted\n3. 2026-10-12 human: Too wide.\n4. tester: red\n5. 2026-10-12 human: Cut the second story.\n6. factory: done (pull request closed by the human); cost: 0 runs, 0.0 min, 0 turns, 0 tokens in (0 more from cache), 0 out, $0.00\n`.
3. The whole refused body before a journal (one test): the report `# Acceptance of Todo service\n\n## Findings in short\n\ntoo wide\n\n## Journal\n\n1. factory: started.\n` with the state `AcceptanceState(stage="approval", stories=["F0002-S0001"], journal=[JournalRecord(number=1, speaker="factory", kind="started")])`, booked with `role=ROLE`, `on` and the bill, gives exactly the body `# Acceptance of Todo service\n\n## Findings in short\n\ntoo wide\n\n## Recommendation\n\nRefused by the human on 2026-10-12: no reason given\n\n## Journal\n\n1. factory: started.\n2. factory: done (pull request closed by the human); cost: 0 runs, 0.0 min, 0 turns, 0 tokens in (0 more from cache), 0 out, $0.00\n`.
4. A work item without a state (one test): the snapshot `WorkItemSnapshot(id="F0001-S0001", path="factory/features/F0001-demo/backlog/F0001-S0001-story.md", folder="backlog", branch="work-item/F0001-S0001", branch_commit=None, document=WorkItemDocument(state=None, body="# Domain model\n"))` gives `work_item_row` equal to `BoardRow(work_item="F0001-S0001", title="Domain model", folder="backlog", stage=None, blocked=None, claim=None, running_since=None, pull_request=None)`, and `render_board([], [row])` is exactly `features\nwork items\nF0001-S0001  Domain model  backlog  stage=-  blocked=-  claim=-  running_since=-  pull_request=-\n`.
5. Absent and present values on a board line (rows of one parametrized test, `render_board([], [row])`): the row of criterion 4 gives the line `F0001-S0001  Domain model  backlog  stage=-  blocked=-  claim=-  running_since=-  pull_request=-`; `BoardRow(work_item="F0001-S0001", title="Domain model", folder="in-progress", stage="tests", blocked="question", claim=None, running_since=None, pull_request=7)` gives the line `F0001-S0001  Domain model  in-progress  stage=tests  blocked=question  claim=-  running_since=-  pull_request=7`.
6. `make check` stays green.
7. docs: none. The operator guide already says that the reason is the human's comments after the reviewer's last result and shows a board line, and this story changes neither.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.domain.acceptance import AcceptanceState, refusal_reason
from factory.domain.board import render_board, work_item_row
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot

entries = [
    ("factory", "started", "started."),
    ("acceptance-reviewer", "result", "not accepted"),
    ("human", "comment", "Too wide."),
    ("tester", "result", "red"),
    ("human", "comment", "Cut the second story."),
]
journal = [JournalRecord(number=n, speaker=s, kind=k) for n, (s, k, _) in enumerate(entries, 1)]
lines = [f"{n}. 2026-10-12 {s}: {t}" if s == "human" else f"{n}. {s}: {t}" for n, (s, _, t) in enumerate(entries, 1)]
state = AcceptanceState(stage="approval", stories=["F0002-S0001"], journal=journal)
document = WorkItemDocument(state=state, body="# Acceptance\n\n## Journal\n\n" + "\n".join(lines) + "\n")
print(refusal_reason(document, "acceptance-reviewer"))
snapshot = WorkItemSnapshot(
    id="F0001-S0001",
    path="factory/features/F0001-demo/backlog/F0001-S0001-story.md",
    folder="backlog",
    branch="work-item/F0001-S0001",
    branch_commit=None,
    document=WorkItemDocument(state=None, body="# Domain model\n"),
)
print(render_board([], [work_item_row(snapshot)]), end="")
EOF
```

Expect: four lines, `Too wide. Cut the second story.`, `features`, `work items` and `F0001-S0001  Domain model  backlog  stage=-  blocked=-  claim=-  running_since=-  pull_request=-`

## Journal
