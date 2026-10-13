# Documentation after work item data

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

Repair what F0002's stories left in the documentation, read as a whole. Each story wrote its own part correctly, but some sentences were true only at the time of their story, one error type is missing from the list of errors, and the README's status is behind. The operator guide's only example, the one command a newcomer can run, exits 2 on this repository without the guide saying why. This is a documentation-only story: no code and no test changes. The tester writes no tests, the coder has nothing to build, and the work is the documenter's, from the docs criterion. If the human would rather make these edits by hand, this draft can be dropped.

What to repair:

- `docs/project-guide.md`, "Reading and writing a work item file": "Wiring does not use them yet." is stale. `factory.entry.wiring.build_work_item_reader` returns `FrontmatterWorkItemReader` for the check command.
- `docs/project-guide.md`, "The state": "The reader of the next story names a fault by that location." Name the reader instead of a story.
- `docs/project-guide.md`, "Cost records": "This story is the format only". Say what the classes cover and that creation, completion and bills come later (F0005), without referring to a story.
- `docs/project-guide.md`, "Errors": add `CostRecordFormatError(line, fault)`, a `FactoryError`, beside `WorkItemFormatError`.
- `README.md`, status sentence: add the identifiers and paths of work items, the sections of a Markdown body, the story form check and the cost records.
- `docs/operator-guide.md`, "Checking a story before it starts". The example path names this repository's feature in a `backlog` folder this repository does not have, and this repository has no `factory/story-form.md`. Running the example here prints `cannot read factory/story-form.md: ...` and exits 2. Say that the command checks a project laid out the v1.1 way (`factory/story-form.md`, `feature.md`, `backlog`/`in-progress`/`done`). Say too that factory-rf's own `factory/` tree is v1's (`drafts/`, `ongoing/`, `FEATURE.md`, `TICKET.md`), so the command does not apply to it. Use an example path that is plainly a placeholder. Replace "`ongoing` is the pipeline's folder" with "`drafts` and `ongoing` are v1's folders and not work item locations".

## Interface

None: no code changes.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/project-guide.md` no longer says that wiring does not use the work item reader, and names no story in "The state" or "Cost records". Its "Errors" section lists `CostRecordFormatError`. The README's status sentence names identifiers and paths, sections, the story form check and the cost records. The operator guide says which project layout `factory-check-story` checks, says that this repository's own `factory/` tree is v1's and is not checked by it, and calls `drafts` and `ongoing` v1's folders.

## Demo

```bash
grep -c "Wiring does not use them yet" docs/project-guide.md; grep -c "next story\|This story" docs/project-guide.md
```
Expect: two lines, `0` and `0`.

```bash
sed -n '/^## Errors/,/^## The hosting service/p' docs/project-guide.md | grep -c CostRecordFormatError
```
Expect: a number of at least 1.

```bash
uv run factory-check-story factory/features/F0002-work-item-data/done/F0002-S0008-the-story-check-command.md; echo "status $?"
```
Expect: `cannot read factory/story-form.md: ...` and `status 2`. The operator guide now explains this outcome for this repository's own v1 tree.

## Log (append only)

1. 2026-10-13 human: created.
