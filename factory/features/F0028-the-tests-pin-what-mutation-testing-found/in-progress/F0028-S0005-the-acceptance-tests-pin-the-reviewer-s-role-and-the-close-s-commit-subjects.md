---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 316
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-20T02:07:25.837003Z'
  lease_duration: 60
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
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T02:01:31.056217Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T02:03:52.951608Z'
  stage: tests
  run: 278e5dd5929943a798ce95fc7f411471
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T02:04:13.132593Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T02:06:06.379958Z'
  stage: doing
  run: c32b1255588d4076b2cc409042f76aab
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T02:06:27.180634Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T02:07:05.105989Z'
  stage: review
  run: 33e7bfc014004ab690cd2a8d803997c6
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T02:07:25.837003Z'
  stage: docs
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
4. factory: started tests as self.
5. tester: Wrote the acceptance tests for the reviewer's role and the close's two commit subjects. They use the `walk`, `kill_points`, `human` and `hosting` fixtures and the helpers in `tests/acceptance_walk.py`. No earlier test changed and no shared helper moved.

   - criterion 1: tests/application/test_acceptance_reviewer_role.py::test_the_hand_over_s_findings_are_the_reviewer_s_last_result (rows `the-reviewer-alone` and `a-later-result-of-another-speaker`)
   - criterion 2: tests/application/test_acceptance_reviewer_role.py::test_the_close_s_reason_is_the_human_s_comments_after_the_reviewer_s_last_result (rows `a-later-result-of-another-speaker` and `the-reviewer-and-the-human-alone`)
   - criterion 3: tests/application/test_acceptance_reviewer_role.py::test_the_close_is_committed_as_close_recorded_on_the_branch_and_closed_refused_on_main. It reads the heads before the first tick with `remote_commit` from `git_support`. The first tick raises `InjectedKill` under `pytest.raises`. After each tick it calls `boundaries.git.fetch()` and then `boundaries.git.log(..., since=...)`, and expects exactly one commit with the stated subject.
   - criteria 4 and 5: no test (`make check`; docs: none).

   Files created: tests/application/test_acceptance_reviewer_role.py.
   Modules the test run could not import: none.

   The tests are not red. The story says the code already behaves this way and the coder has nothing to change, so they pass now, as in F0025-S0003. `make test` was green (`test: green (40.2 s)`) and `make lint` is green after `ruff format` on the new file. I skipped the type check, as this stage's instructions say; `make check` covers it afterwards.

   Choices I made, all within the criteria:
   - The test module's own `_push_entries` helper appends each `NewEntry` and has the human push the rendered report to `report_of(FIRST)`.
   - The criterion 2 and 3 tests share their entry constants at module level (`NOT_ACCEPTED`, `TOO_WIDE`, `RED`).
   - `ROLE` is set to `REVIEWER`.

   `lint`: lint: green (0.0 s)
   `test`: test: green (39.8 s)
6. factory: started doing as self.
7. coder: Changed no code. As the story says, the code already does what the tester's tests in `tests/application/test_acceptance_reviewer_role.py` pin: the hand-over's findings and the close's reason both come from the acceptance reviewer's last `result`, and the close makes the commits `close recorded` on the branch and `closed, refused` on main. Those tests pass against the current `src/factory/application/acceptance.py`. `make check` is green (`test: green (40.4 s)`, `check: green`).

   Built: nothing. No path under `src/` changed.

   Main choice: I left `src/` untouched. The other option was to tidy the handlers in `acceptance.py` while I was there, and I rejected it: the story's Interface says no module under `src/factory/` changes, and anything more would go beyond the story's scope (R13).

   Refactor: my diff is empty, so there was nothing to refactor.

   Description: no journal entry changed what the task means, so `## Description` stays as written.

   Noticed, not touched: none.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'`. It adds one file, `tests/application/test_acceptance_reviewer_role.py`, and changes nothing under `src/`. I read the file against each criterion and against the helpers it calls in `tests/acceptance_walk.py`, `GitCli.log` and `acceptance.py:400`/`:422`.

   - Criterion 1: `test_the_hand_over_s_findings_are_the_reviewer_s_last_result` is one parametrized test with two rows, `[ACCEPTED]` and `[ACCEPTED, RED]`. It checks that the event is `hand_over` and that the findings are exactly `accepted; the feature holds together.`. In the second row a later `tester` result comes after the reviewer's, so a handler that took any speaker's last result would show `red` and fail. The rule's failing side is tested.
   - Criterion 2: `test_the_close_s_reason_is_the_human_s_comments_after_the_reviewer_s_last_result` is one parametrized test with the two rows the criterion names. It pushes with `stage="approval"` and `handed_over="approval"`, calls `walk.close(number, "Cut the second story.")`, checks that the event is `closed`, and compares the `Recommendation` with the exact refusal paragraph.
   - Criterion 3: `test_the_close_is_committed_as_close_recorded_on_the_branch_and_closed_refused_on_main` reads the branch's and main's heads with `remote_commit` before the first tick and arms `KillPoint.AFTER_PUSH`. The first tick raises `InjectedKill` under `pytest.raises`. After a fetch, the branch log since its old head must unpack to exactly one commit, `work item F0002-A0001: close recorded`. After the second tick, main's log since its old head must be exactly one commit, `closed, refused`. These subjects match `acceptance.py:400` and `:422`.
   - Criteria 4 and 5: the coder's entry 7 records `check: green`. The docs criterion "docs: none" is still true, because no behaviour changed.
   - Architecture and security: the change is test-only, in the mirrored folder. It adds no suppression markers and no secrets.
   - Quality: `_push_entries` is a three-line helper that does what the Interface prescribes. `acceptance_walk.py` has no helper that appends entries to a document `walk.record` returned and pushes it again. The similar loops in `test_acceptance_closed.py:119` and `test_question_causes_recorded.py:48` build their documents from their own fixtures, so I don't count it as a copy.
   - Work item: the journal states the main choice (no change under `src/`) and the option rejected (tidying `acceptance.py`), and the Description matches what was built.
   - `duplicates: 5 new` (entry 7) cannot come from this diff, because `make duplicates` reads only `src/factory`, which this diff leaves alone.

   Earlier tests: none. `git diff --name-status main...HEAD` shows only `A` for `tests/application/test_acceptance_reviewer_role.py`, and the other entries are the work item's own files under `factory/`.
10. factory: started docs as self.
