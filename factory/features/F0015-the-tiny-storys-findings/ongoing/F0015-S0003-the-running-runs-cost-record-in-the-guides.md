---
stage: ready
pr: null
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
