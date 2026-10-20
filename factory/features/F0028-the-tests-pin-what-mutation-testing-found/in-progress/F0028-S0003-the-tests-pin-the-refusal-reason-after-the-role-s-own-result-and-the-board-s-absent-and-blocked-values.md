---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 314
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T01:42:04.769232Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T01:42:04.775662Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T01:42:19.956328Z'
  stage: intake
  run: 468894a97ae0416ba39133122923cb6d
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T01:42:40.007053Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T01:44:39.925146Z'
  stage: tests
  run: a649c5fdcddc48eb8445d70a43d0e745
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T01:45:00.637659Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T01:46:52.457193Z'
  stage: doing
  run: d9152193dd8446e3b903e552ce38b726
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T01:47:12.807308Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T01:47:42.672299Z'
  stage: review
  run: 9fb4b0c9f13a43a8b15b2da9b50b9aa6
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T01:48:02.947600Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T01:48:15.616855Z'
  stage: docs
  run: c20d14232455491d9b990a29e314eece
---

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

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete functions (`refusal_reason`, `book_refusal`, `work_item_row`, `render_board`) with the behaviour pinned, the two test modules and the shared `tests/acceptance_support.py`; no `src/` change, as the feature's decision 1 says.
   Criteria: each is testable by one test function or one parametrized test with exact expected values. Every Interface rule has one: the three rows of criterion 1 cover "after the role's own last result" with a later result of another role, a later question of the role and a later result of the role itself; criteria 2 and 3 cover the whole body, both with and without a `## Recommendation`; criteria 4 and 5 cover the absent values and the `-` and `blocked=<reason>` rendering. The failing side of each rule is a row.
   Smoke test: a runnable `uv run -q python` heredoc that uses only the domain imports. Its `Expect:` line gives the four output lines, which can be checked.
   Architecture: the tests sit in `tests/domain/` and test `factory.domain` only; the shared helper moves to a module at the `tests/` root under the standing leave in CLAUDE.md, which keeps the earlier tests' names and checks.
   Scope: inside F0028's Scope (S0003 line) and not in its Out of scope; the dead guard at `acceptance.py:332` stays (decision 4).
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 5. The code already behaves the way the story describes, so `make test` is green on purpose and the tests are not red. The coder has nothing to change in `src/`.

   - criterion 1: tests/domain/test_acceptance_refusal_edges.py::test_the_refusal_reason_starts_after_the_roles_own_last_result (rows `other-role-result`, `role-question`, `role-result`)
   - criterion 2: tests/domain/test_acceptance_refusal_edges.py::test_a_refusal_books_the_reason_after_the_roles_own_last_result
   - criterion 3: tests/domain/test_acceptance_refusal_edges.py::test_a_refusal_writes_the_whole_body_with_the_recommendation_before_the_journal
   - criterion 4: tests/domain/test_board_absent_values.py::test_a_work_item_without_a_state_shows_every_state_value_as_absent
   - criterion 5: tests/domain/test_board_absent_values.py::test_a_board_line_writes_an_absent_value_as_a_dash_and_a_blocked_row_with_its_reason (rows `absent`, `blocked`). Each row checks the whole `render_board([], [row])` output, not just the line.
   - criterion 6: the factory's `make check`.
   - criterion 7: there are no docs to change.

   Files created: tests/acceptance_support.py, tests/domain/test_acceptance_refusal_edges.py, tests/domain/test_board_absent_values.py.

   Earlier test file changed under the standing leave in CLAUDE.md (*Tests*): tests/domain/test_acceptance_booking.py. I moved its `_document` helper to tests/acceptance_support.py, where it is named `report_of` because it is now imported from another module. The booking tests import it from there and call `report_of` where they called `_document`. Every test keeps its name and checks the same thing.

   Run: `make test` was green ("test: green") and `make lint` was green. The test run could import every module. I skipped the type check, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: test: green (38.0 s)
6. factory: started doing as self.
7. coder: Built nothing. No file under `src/factory/` changes. The tester's tests (tests/domain/test_acceptance_refusal_edges.py, tests/domain/test_board_absent_values.py, with the shared tests/acceptance_support.py) already pass against the current `factory.domain.acceptance` and `factory.domain.board`. The Interface says no module under `src/` changes, and the description says the coder has nothing to change.

   Main choice: leave `src/` untouched. I rejected "tidying" `refusal_reason`, `book_refusal` or `render_board` while I was in there, because this story pins existing behaviour and a code change would be scope beyond the description (R13).

   Refactor step: there is no diff of mine to refactor.

   Check: `make check` passed in the foreground (`test: green (39.9 s)`, total coverage 99.14 %, `check: green`).

   The journal changed nothing in the task's meaning, so `## Description` stays as it is.

   Noticed but not touched: the dead guard at `acceptance.py:332` stays, as decision 4 of the feature says. `_work_item_line`'s time-zone survivor is equivalent in a container that runs in UTC, as the description says.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   I read the diff, `tests/acceptance_support.py`, `tests/domain/test_acceptance_booking.py`, `tests/domain/test_acceptance_refusal_edges.py` and `tests/domain/test_board_absent_values.py`, and checked them against the work item.
   - Criterion 1: `test_the_refusal_reason_starts_after_the_roles_own_last_result` has three rows (`other-role-result`, `role-question`, `role-result`). They hold the criterion's exact entries and expected reasons, and they cover the failing side of the Interface rule: a later `result` of another speaker and a later record of the role of another kind leave the reason unchanged.
   - Criterion 2: `test_a_refusal_books_the_reason_after_the_roles_own_last_result` compares the whole body with the criterion's text, character for character.
   - Criterion 3: `test_a_refusal_writes_the_whole_body_with_the_recommendation_before_the_journal` has the criterion's state and body, and checks the whole body, ending in one newline.
   - Criterion 4: `test_a_work_item_without_a_state_shows_every_state_value_as_absent` checks the `BoardRow` for equality and the exact `render_board` output.
   - Criterion 5: one parametrized test with the rows `absent` and `blocked`; each checks the whole `render_board([], [row])` output.
   - The Interface states no numeric limits, so there is no boundary to test on both sides.
   - Coder's entry 7: the factory's `make check` was green.
   - Architecture and security: nothing under `src/` changes, and the diff adds no suppression marker.
   - Hygiene: the description and the docs criterion (`none`) match what was built.

   `ROLE` and `ON` repeat the module constants that other acceptance test modules also hold. I did not count that as a copied helper: the project's test modules each declare these constants themselves.

   Earlier tests:
   - tests/domain/test_acceptance_booking.py: changed under the standing leave to move a shared test helper in `CLAUDE.md` (*Tests*), which the story's Interface also names. Its `_document` moved to `tests/acceptance_support.py` as `report_of`. Its three call sites now use `report_of`, and every test keeps its name and what it checks.
10. factory: started docs as self.
11. documenter: No findings. The docs criterion is `none`, so I wrote nothing and changed no file.

    Cross-read against the diff, which is tests only (tests/acceptance_support.py, the two new test modules, and the helper move in tests/domain/test_acceptance_booking.py), with nothing under `src/` changed:
    - `docs/operator-guide.md`, the close/refusal paragraph (line 1234): it says the reason is the human's comments after the reviewer's last result, which matches the pinned behaviour. Current.
    - `docs/operator-guide.md`, the board line example (line 1161): it uses the `stage=… blocked=- claim=… pull_request=…` form that the new tests pin. Current.

    Stale text I noticed that is not mine to fix: none.

    I did not run `make check`, because I changed no file. The factory's check after this stage decides.

    `check`: check: green (not run again: passed on tree e11d2b1585e1 at 2026-10-20T01:45:59Z)
    `secrets`: secrets: green (0.2 s)
    `documents`: documents ok
