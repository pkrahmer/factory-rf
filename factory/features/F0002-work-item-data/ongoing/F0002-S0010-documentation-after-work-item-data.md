---
stage: review
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
