---
stage: demo
pr: 208
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The running run's cost record, in the guides

## Assignment (as of log entry 1)

During the tiny story of 2026-10-18 (the night log's row of 06:09) the coder wrote that the factory's cost log, the work item's `.costs.jsonl`, "shows as modified in the working tree". The code shows that this is expected and harmless (FEATURE decision 9). `StageLauncher.launch` calls `CostRecorder.begin` right before the agent runs, and `begin` writes the running run's `started` record into the sidecar in the work tree, uncommitted. The record travels in the stage's next commit, the result commit or the stall commit. So `git status` shows the file as modified while an agent runs, or as untracked on a work item's first run. Nothing treats it as the agent's write. The sidecar lies outside every write path. The undo reverts every cost-record file in an `in-progress` folder, and the factory then writes the records again from memory, so whatever the agent does to the file changes nothing in the commit. The journal entry's list of undone paths leaves the sidecar out. The agent cannot commit it, because the checkout's `.git` is the factory's alone. Its one real effect, the run id in the agent's own `make check`, is S0001's. The guides do not say any of this yet, so an agent or an operator who sees the file may take it for a fault. This story is documentation only. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes, and the tester and the coder each end with an entry saying so. The docs criterion carries the text. No rule is added to the shipped agents (FEATURE decision 9).

## Interface

None: no code, no image file, no template file, no agent file and no test changes. The documents the documenter changes are `docs/project-guide.md`, `docs/operator-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: the project guide's *When a record is created, completed and committed* (under *Cost records*) says, in or after its bullet *Created at the start*, that from `begin` until the stage's commit the sidecar holds the running run's `started` record and is not committed. An agent's `git status` or `git diff` therefore shows the work item's `.costs.jsonl` as modified, or as untracked on the work item's first run. The text says that this is expected: the file is the factory's; the undo reverts whatever the agent does to it and the factory writes it again from memory (the bullet *Rewritten after every undo*); the agent cannot commit it; and an agent leaves it alone. It also says that the agent's own `make check` scans it, which is why a project's secrets scan leaves the cost records out. The operator guide's *What a stage run shows* gets one sentence after its list. While an agent runs, the work item's `.costs.jsonl` is modified in the work tree and not committed: it holds the running run's record, which the result commit or the stall commit carries, and an agent that mentions it in its entry has seen the factory's file, not made a change of its own (seen by the coder of the tiny story, 2026-10-18). The decision log's entry "The sidecar is rewritten from memory after every undo, and a crashed stage's records are discarded with it" gets one sentence: while an agent runs, it therefore sees the sidecar modified, holding the running run's `started` record, and that stays so, because the alternative, pushing the started record before the run, is the one that entry rejects (first noticed by an agent on 2026-10-18). Each of the three new passages names the record with the words "the running run's" (for example "the running run's `started` record"), which no document uses today, so the demo can find all three. No other document changes, the documents use no word the document check refuses, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -c "the running run's" docs/project-guide.md docs/operator-guide.md docs/decisions.md
```
Expect: three lines, one per file in that order, each `<file>:<n>` with `n` at least 1 (none of them ends `:0`).

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-18 human: created.
2. intake: accepted. Documentation-only story, accepted as written.
   - Interface: it states "None" and names the three documents the documenter changes (`docs/project-guide.md`, `docs/operator-guide.md`, `docs/decisions.md`). There is no module or signature to check and no behaviour comment that needs a criterion. The anchors it cites exist: the project guide's "When a record is created, completed and committed" with its bullets "Created at the start" and "Rewritten after every undo"; the operator guide's "What a stage run shows"; the decision log's "The sidecar is rewritten from memory after every undo, and a crashed stage's records are discarded with it".
   - Criteria: criterion 1 (nothing under src/image/template/claude/tests changes) can be checked by a diff. Criterion 3 names the exact text for each of the three documents. It has no rule with a failing side. The guard against an unwanted change is criterion 1 plus the document check.
   - Demo: both commands are runnable. The grep counts "the running run's" in the three files and gives 0 in each today, so the expectation (`:n` with n ≥ 1 in all three) can be checked. `check_documents` must print `documents ok`.
   - Architecture: nothing in the code layers is touched, and the story adds no rule to the shipped agents (FEATURE decision 9).
   - Scope: the story matches FEATURE.md's third scope item and decision 9. Its dependency is met: S0001 is in `done/`, and `template/Makefile` and `demo/todo-service/project/Makefile` already carry the `.costs.jsonl` filter, so the project-guide claim about the secrets scan is true.
3. tester: no tests written or changed. This story only changes documentation: the Interface says "None", and criterion 1 says nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes. Following criterion 1, I am ending with this entry to say I changed nothing under those paths.
   - criterion 1: no test. A diff checks it, and none of my changes are under `tests/` or the other paths.
   - criterion 2: no test of its own. The factory runs `make check` as the gate.
   - criterion 3 (docs): no test. The documenter writes the text, and the demo's grep and `python -m factory.entry.check_documents` check it.
   - Files created: none. There are no modules the test runner cannot import, because no new tests exist.
   - I did not run `make test`: with no new tests there is nothing red to confirm. `make lint` is green, and the working tree was clean before this entry.
   - Rejected: a test that greps the docs for "the running run's". Criterion 1 forbids changes under `tests/`, and a test that pins document wording is not in the Interface.
   - Next stage: the coder also changes nothing and ends with an entry saying so, then the documenter writes the three passages.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (31.9 s)
4. coder: no code written or changed. This story only changes documentation: the Interface says "None", and criterion 1 says nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes. Following criterion 1, I am ending with this entry to say I changed nothing under those paths. There were no failing tests to make pass, because the tester added none.
      - Commits: none of my own. The branch holds only the factory's stage commits.
      - Refactor: none. There is no diff of mine to clean up.
      - Rejected: writing the three doc passages here. The coder does not write `docs/` (CLAUDE.md, Docs), so the documenter stage writes them from criterion 3.
      - Open: the documenter writes the passages that the demo's grep for "the running run's" and `check_documents` check.

      `make check`: check: green (test: green, 33.2 s, coverage 99.47 %)

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Scope: `git diff main...HEAD -- . ':!factory'` is empty, so nothing outside the ticket changed. Criterion 1 holds: nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changed, and the tester's entry (3) and the coder's entry (4) both say so.
      - Criterion 2: the factory's `make check` after the coder was green (`check: green`, coverage 99.47 %). `make duplicates` reports 0 new findings.
      - Criterion 3 is the docs criterion, and the documenter writes it next. It still describes what the reader must know, and it names the three passages and the phrase "the running run's" that the demo's grep looks for.
      - Architecture, security, quality: there is no diff, so there is nothing to judge.
      - Ticket hygiene: `Assignment` matches what was built, which is nothing so far, as the story intends. The tester's and the coder's entries say what each rejected: a test that pins document wording, and writing `docs/` in the coder stage.
6. documenter: wrote the three passages of criterion 3; no code, test or comment touched.
   - `docs/project-guide.md`: new bullet after *Created at the start* under *When a record is created, completed and committed*. It covers the uncommitted `started` record, the modified or untracked `.costs.jsonl` in `git status`, why that is expected (the undo reverts it, the factory rewrites it from memory, the agent cannot commit it, the agent leaves it alone), and the agent's own `make check` scanning it, which is why a project's secrets scan leaves the cost records out.
   - `docs/operator-guide.md`: one paragraph after the list in *What a stage run shows*.
   - `docs/decisions.md`: one sentence at the end of the sidecar entry, tied to the rejected alternative of pushing the started record before the run.
   - Each passage uses "the running run's". The demo grep gives 1 in each file. `python -m factory.entry.check_documents` prints `documents ok`.
   - I did not run `make check`, since only documents changed. The factory's run after this stage is the gate.
   - Cross-read: the project guide's *Rewritten after every undo* bullet and the operator guide's stall section agree with the new text. Nothing stale seen.
   - No findings.

   `make check`: check: green
   `make documents`: documents ok
