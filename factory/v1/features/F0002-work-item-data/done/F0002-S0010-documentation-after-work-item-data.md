---
stage: done
pr: 38
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Documentation after work item data

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

Repair what F0002's stories left in the documentation, read as a whole. Each story wrote its own part correctly, but some sentences were true only at the time of their story, one error type is missing from the list of errors, and the README's status is behind. The operator guide's only example, the one command a newcomer can run, exits 2 on this repository without the guide saying why. This is a documentation-only story: no code and no test changes. The tester writes no tests, the coder has nothing to build, and the work is the documenter's, from the docs criterion. If the human would rather make these edits by hand, this draft can be dropped.

What to repair:

- `docs/project-guide.md`, "Reading and writing a work item file": "Wiring does not use them yet." is half stale. `factory.entry.wiring.build_work_item_reader` returns `FrontmatterWorkItemReader` for the check command; the writer is not wired yet. Say both.
- `docs/project-guide.md`, "The state": "The reader of the next story names a fault by that location." Name the reader instead of a story.
- `docs/project-guide.md`, "Cost records": "This story is the format only". Say what the classes cover and that creation, completion and bills come later (F0005), without referring to a story.
- `docs/project-guide.md`, "Errors": add `CostRecordFormatError(line, fault)`, a `FactoryError`, beside `WorkItemFormatError`; and `NothingToCommit`, the `GitError` that `commit` raises when nothing is staged, beside `FetchFailed`.
- `README.md`, status sentence: add the identifiers and paths of work items, the sections of a Markdown body, the story form check and the cost records.
- `docs/operator-guide.md`, "Checking a story before it starts". The example path names this repository's feature in a `backlog` folder this repository does not have, and this repository has no `factory/story-form.md`. Running the example here prints `cannot read factory/story-form.md: ...` and exits 2. Say that the command checks a project laid out the v1.1 way (`factory/story-form.md`, `feature.md`, `backlog`/`in-progress`/`done`). Say too that factory-rf's own `factory/` tree is v1's (`drafts/`, `ongoing/`, `FEATURE.md`, `TICKET.md`), so the command does not apply to it until this repository moves to v1.1's layout (the human's answer of 2026-10-13). Use an example path that is plainly a placeholder, and run it in a temporary directory laid out the v1.1 way, showing the `<path>: ok` it prints. Replace "`ongoing` is the pipeline's folder" with "`drafts` and `ongoing` are v1's folders and not work item locations".

## Interface

None: no code changes.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/project-guide.md` says that wiring uses the work item reader (`build_work_item_reader`, for the check command) and not yet the writer, and names no story in "The state" or "Cost records". Its "Errors" section lists `CostRecordFormatError` and `NothingToCommit`. The README's status sentence names identifiers and paths, sections, the story form check and the cost records. The operator guide says which project layout `factory-check-story` checks, says that this repository's own `factory/` tree is v1's and is not checked by it until the tree moves to v1.1's layout, and calls `drafts` and `ongoing` v1's folders.

## Demo

```bash
grep -c "Wiring does not use them yet" docs/project-guide.md; grep -c "next story\|This story" docs/project-guide.md
```
Expect: two lines, `0` and `0`. grep exits 1 when it counts nothing; that exit is the expected result, not an error.

```bash
sed -n '/^## Errors/,/^## The hosting service/p' docs/project-guide.md | grep -o "CostRecordFormatError\|NothingToCommit" | sort -u
```
Expect: two lines, `CostRecordFormatError` and `NothingToCommit`.

```bash
uv run factory-check-story factory/features/F0002-work-item-data/done/F0002-S0008-the-story-check-command.md; echo "status $?"
```
Expect: `cannot read factory/story-form.md: ...` and `status 2`. The operator guide now explains this outcome for this repository's own v1 tree.

## Log (append only)

1. 2026-10-13 human: created.
2. intake: accepted
   - Interface: "None: no code changes", which fits a documentation-only story. There is nothing to name.
   - Criteria: criterion 1 is the gate. Criterion 2 is the docs criterion, and it states checkable facts: the wiring sentence, no story named in "The state" or "Cost records", the two error types listed, the README status topics, and the operator guide's layout statement and folder wording. The story has no rule with a failing side. It is documentation only and the tester writes no tests.
   - Demo: all three commands are runnable. I checked the first against docs/project-guide.md. "Wiring does not use them yet" is at line 456, "next story" at line 403 and "This story" at line 543, so the Demo's two counts match the three spots the assignment repairs. Each Expect line is checkable, and the grep exit-1 case is stated.
   - Architecture: there are no layer or interface changes. Only docs are touched, and the documenter owns them.
   - Scope: this is within F0002 (it is listed in FEATURE.md as proposed by the feature acceptance). Decision 17 covers the v1-tree statement. Nothing in "Out of scope" is touched.
3. tester: no tests written, by design. This story only changes documentation. The Interface is "None: no code changes", the assignment says "The tester writes no tests", and intake confirmed this.
      - criterion 1 (`make check` stays green): this is the stage gate, and the factory's checks cover it. No test function is needed.
      - criterion 2 (docs): the documenter checks it, along with the Demo's grep commands. It describes the wording of the prose, not behaviour that pytest could check. The project does not test prose in docs, and a test here would only pin the text.
      - Files created: none. Modules the test runner could not import: none. I did not run `make test` because no new tests exist to fail. `make lint` is green.
      - Open: nothing for the coder to build. The next stage with real work is the documenter.

   `make lint`: lint: green
   `make test`: test: green
4. coder: nothing to build, by design. This story only changes documentation. The Interface says "None: no code changes", the assignment says "the coder has nothing to build", and intake and the tester confirm it.
      - Built: nothing. No commits, and no changes under `src/` or `tests/`.
      - Refactor: nothing to refactor, because there is no diff.
      - Checked: `make check` is green on the branch as handed over (coverage 99.64 %).
      - Open: all of the work belongs to the documenter, from criterion 2 and the Demo: `docs/project-guide.md` (wiring sentence, "The state", "Cost records", "Errors"), the `README.md` status sentence, and the `docs/operator-guide.md` section "Checking a story before it starts". The coder does not write those files, so I left them alone.

   `make check`: check: green
5. reviewer: no findings.
      - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch's four commits change only the ticket file. That is what a documentation-only story should look like at this stage: the Interface is "None: no code changes", and the tester and the coder both had nothing to do, by design.
      - 1. Acceptance criteria: criterion 1 (`make check` stays green) is the stage gate. The coder's entry says `make check` was green on the branch as handed over. Criterion 2 is the docs criterion, which the documenter writes next. No rule has a failing side, so no test is missing.
      - 2. Architecture, 3. Security, 4. Quality: there is nothing to judge, because there is no code, test or configuration diff.
      - 5. Ticket hygiene: the log explains why no tests and no code exist. `Assignment` matches what was built (nothing so far; the docs work is still to come). Criterion 2 still says what a reader must know once the story is done: the project guide's wiring, "The state", "Cost records" and "Errors" fixes, the README status topics, and the operator guide's statements about layout and v1 folders. The Demo's grep commands check them.
      - Open: all of the work is the documenter's, from criterion 2 and the Demo.
6. documenter: wrote the F0002 documentation repairs.
   - `docs/project-guide.md`: the wiring sentence now says that `build_work_item_reader` returns `FrontmatterWorkItemReader` for the check command and that the writer is not wired. "The state" says "the work item reader". "Cost records" says "The classes cover the format only" and that creation, completion and bills come later (F0005). "Errors" lists `NothingToCommit` beside `FetchFailed` and `CostRecordFormatError(line, fault)` beside `WorkItemFormatError`.
   - `README.md`: the status sentence now names the identifiers and paths of work items, the sections of a Markdown body, the story form check with its command, and the cost records.
   - `docs/operator-guide.md`, "Checking a story before it starts": the command checks a project laid out the v1.1 way. This repository's `factory/` tree is v1's, so the command prints `cannot read factory/story-form.md: ...`, exits 2, and does not apply until the tree moves to v1.1. The example now uses placeholder paths. I ran it in a temporary v1.1-layout directory and it printed `<path>: ok` with status 0. `drafts` and `ongoing` are called v1's folders and not work item locations.
   - `make check` is green after the last edit. The Demo's greps and the error-section check match what I wrote.
   - Cross-read against the diff: the diff is empty because the story changes no code. The Interface, the other sections of the project guide that I touched, and the operator guide's tables are current.
   - Stale but untouched: nothing.

   `make check`: check: green
7. demo: I ran all three Demo commands from the repository root. All three met their `Expect:` lines and nothing contradicts a criterion, so there are no findings.

   1. Stale sentences counted in `docs/project-guide.md`:
   ```
   $ grep -c "Wiring does not use them yet" docs/project-guide.md; grep -c "next story\|This story" docs/project-guide.md
   0
   0
   ```
   Met: two lines, `0` and `0`.

   2. Error types in the "Errors" section:
   ```
   $ sed -n '/^## Errors/,/^## The hosting service/p' docs/project-guide.md | grep -o "CostRecordFormatError\|NothingToCommit" | sort -u
   CostRecordFormatError
   NothingToCommit
   ```
   Met: the two expected names.

   3. Running the check command on this repository's v1 tree:
   ```
   $ uv run factory-check-story factory/features/F0002-work-item-data/done/F0002-S0008-the-story-check-command.md; echo "status $?"
   cannot read factory/story-form.md: [Errno 2] No such file or directory: '/work/factory-rf/factory/story-form.md'
   status 2
   ```
   Met: `cannot read factory/story-form.md: ...` and `status 2`.

   Checked against the criteria:
   - Criterion 2, project guide: `docs/project-guide.md:458` says that wiring uses the reader and not yet the writer, and names `build_work_item_reader` for the check command. "The state" (line 405) says "The work item reader names a fault by that location". "Cost records" (line 545) says "The classes cover the format only" and puts creation, completion and bills later, in F0005. Neither section names a story. "Errors" lists `CostRecordFormatError` and `NothingToCommit`.
   - Criterion 2, README: the status sentence in `README.md:3` names the identifiers and paths of work items, the sections of a Markdown body, the story form check with its command, and the cost records.
   - Criterion 2, operator guide: "Checking a story before it starts" in `docs/operator-guide.md` names the v1.1 layout (`factory/story-form.md`, `feature.md`, `backlog`/`in-progress`/`done`). It says this repository's `factory/` tree is v1's, so the command does not apply here until the tree moves to v1.1's layout, and it explains the exit 2 that command 3 shows. The example uses a placeholder path, and the guide says "`drafts` and `ongoing` are v1's folders and not work item locations".
   - Criterion 1: I did not run `make check` in this stage; the factory runs it after the demo. The documenter's entry reports it green.

   Open: nothing.
8. done (pull request merged); cost: 6 runs, 2.9 min, 35 turns, 62k tokens in (414k more from cache), 8k out, $0.55
