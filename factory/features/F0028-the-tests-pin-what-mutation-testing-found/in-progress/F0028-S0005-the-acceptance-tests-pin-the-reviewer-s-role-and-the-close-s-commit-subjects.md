---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 316
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T02:00:54.354020Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T02:00:54.361146Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T02:01:10.692143Z'
  stage: intake
  run: ad4ec654695a4dd788ef14d8b9189135
---

# The acceptance tests pin the reviewer's role and the close's commit subjects

## Description

The mutation sweeps of 2026-10-19 over `factory.application` (`planning/overnight/mutation-sweep-2026-10-19-part2.md`, its story 3 and part of its story 6) left three live mutants of the reviewer's role in `factory.application.acceptance` that no test reaches, and eight of the close's two commit subjects. At the hand-over, the approval's description takes its *Findings in short* from the acceptance reviewer's last `result` (`acceptance.py:244` and `:270`), and at the close the refusal is booked from the human's comments after that same record (`acceptance.py:361`). No test has a later `result` of another speaker in the report, so a handler that passed no role, and so took any speaker's last result, would pass. The domain half of this gap is S0003's criterion 1; this story pins the handlers' half. The close also makes two commits whose subjects the human reads in the history, `close recorded` on the branch (`acceptance.py:400`) and `closed, refused` on main (`acceptance.py:422`), and no test pins either. This story pins these as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003. The sweep's two other rows here are equivalent (decision 10 of `feature.md`): the stage finish's description and an archived story without a state.

## Interface

No module under `src/factory/` changes. The behaviour pinned (`application`):

- `factory.application.acceptance.AcceptanceHandOver.handle(event)`: the description's `## Findings in short` is the text of the last journal record whose speaker is the acceptance stage's role and whose kind is `result`; a later `result` of another speaker changes nothing.
- `factory.application.acceptance.AcceptanceClosed.handle(event)`: the refusal's reason is the human's comments after that same record; a later `result` of another speaker moves nothing. The close is committed on the branch as `work item <id>: close recorded`, the booked report on main as `work item <id>: closed, refused`.

Tests (the tester writes them): `tests/application/test_acceptance_reviewer_role.py`. It builds on the `walk` fixture of `tests/conftest.py` and on `FIRST`, `FIRST_RECORDS`, `REVIEWER` and `report_of` of `tests/acceptance_walk.py`, and on the `kill_points` fixture. Each test opens the acceptance with `number = walk.open(FIRST)` and pushes its report with `walk.record(FIRST, number, FIRST_RECORDS, stage="approval", ...)`, which appends the factory's `started.`. It then appends the row's entries (`append_entry` of each `NewEntry`), renders the document with `boundaries.work_item_writer` and has the human push it to `work-item/F0002-A0001` at `report_of(FIRST)`, then ticks with `walk.tick()`. No earlier test changes.

`ROLE` is `acceptance-reviewer` (`REVIEWER`). A human comment entry is `NewEntry(speaker="human", kind="comment", text=..., on=date(2026, 10, 12))`.

## Acceptance criteria

1. The hand-over's findings (rows of one parametrized test; the report pushed with `stage="approval"`, then one `walk.tick()`, whose event is `hand_over`):
   - The entries `(ROLE, result, "accepted; the feature holds together.")`: `section_text(hosting.description(number), "Findings in short")` is exactly `accepted; the feature holds together.`
   - The same entry followed by `(tester, result, "red")`: exactly `accepted; the feature holds together.` as well (a later result of another speaker).
2. The close's reason (rows of one parametrized test; the report pushed with `stage="approval"` and `handed_over="approval"`, then `walk.close(number, "Cut the second story.")` and one `walk.tick()`, whose event is `closed`):
   - The entries `(ROLE, result, "not accepted")`, `(human, comment, "Too wide.")` and `(tester, result, "red")`: `section_text(walk.booked(FIRST).body, "Recommendation")` is exactly `Refused by the human on 2026-10-12: Too wide. Cut the second story.` (a later result of another speaker).
   - The same entries without the tester's: exactly the same paragraph.
3. The close's commit subjects (one test; the first report of criterion 2; `kill_points.arm(KillPoint.AFTER_PUSH)` before the closing tick, which then raises `InjectedKill` right after the branch's push; then a second `walk.tick()`):
   - After the first tick and a `boundaries.git.fetch()`, `boundaries.git.log("origin/work-item/F0002-A0001", since=<the branch's head before that tick>)` is exactly one commit, whose subject is `work item F0002-A0001: close recorded`.
   - After the second tick, `boundaries.git.log("origin/main", since=<main's head before the first tick>)` is exactly one commit, whose subject is `work item F0002-A0001: closed, refused`.
4. `make check` stays green.
5. docs: none. The operator guide already says that the description shows the reviewer's findings and that the refusal is the human's comments after the reviewer's last result, and this story changes neither.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.application.handlers.recording import commit_subject
from factory.domain.acceptance import AcceptanceState, acceptance_description, refusal_reason
from factory.domain.journal import JournalRecord
from factory.domain.sections import section_text
from factory.domain.work_item import WorkItemDocument

entries = [
    ("factory", "started", "started."),
    ("acceptance-reviewer", "result", "not accepted"),
    ("human", "comment", "Too wide."),
    ("tester", "result", "red"),
]
journal = [JournalRecord(number=n, speaker=s, kind=k) for n, (s, k, _) in enumerate(entries, 1)]
lines = [f"{n}. 2026-10-12 {s}: {t}" if s == "human" else f"{n}. {s}: {t}" for n, (s, _, t) in enumerate(entries, 1)]
state = AcceptanceState(stage="approval", stories=["F0002-S0001"], journal=journal)
document = WorkItemDocument(state=state, body="# Acceptance\n\n## Journal\n\n" + "\n".join(lines) + "\n")
print(section_text(acceptance_description(document, "acceptance-reviewer"), "Findings in short"))
print(refusal_reason(document, "acceptance-reviewer"))
print(commit_subject("F0002-A0001", "closed, refused"))
EOF
```

Expect: three lines, `not accepted`, `Too wide.` and `work item F0002-A0001: closed, refused`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names concrete handlers (`AcceptanceHandOver.handle`, `AcceptanceClosed.handle`), the test module and the shared fixtures and helpers it builds on. The behaviours it states are the findings text, the refusal reason, and the two commit subjects. Nothing under `src/` changes. The smoke test's functions exist with those signatures (`acceptance_description` and `refusal_reason` take a document and a role, `commit_subject` takes an id and a text).
   - Criteria: each is testable by one test function with exact expected values. Criterion 1 has the role's own result and a later other-speaker result. Criterion 2 has the later other-speaker result and the case without it. Criterion 3 has both subjects, the branch's and main's. The rules' failing side, a result of another speaker not counting, is covered in 1 and 2. Criteria 4 and 5 close the list as the form requires.
   - Smoke test: the script is runnable and uses the existing domain functions. The Expect line names three exact output lines.
   - Architecture: tests only, in `tests/application/` as the mirror rule requires. No wiring or layer change.
   - Scope: within F0028's scope list (S0005 in `feature.md`), tests only, and none of its Out of scope items. Decision 10 of the feature records the two equivalent rows as excluded.
