---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The commits on a work item's branch carry its id

## Assignment (as of log entry 1)

v1.1 makes four kinds of commit on a work item's branch that name no work item: a stage's start (`<stage> starts as <instance>`), a stage's end (`<stage> ends: <next>`, the commit that carries the coder's source), a stall (`<stage> stalled`) and an acceptance's opening (`<id> opens`). Only the handlers' and recovery's commits use `commit_subject` and so read `work item <id>: <text>`. Every shipped agent's `## Rules` says that git links code to work items through the commit subject, and the template's `make mutants` (F0012-S0029) finds a feature's modules by the subject `work item <feature>-S<nnnn>: ...`; with today's subjects it would find no module of a v1.1 project, because the commit that carries a story's source is `doing ends: review`. This story gives each of the four commits the prefix of `commit_subject`, so that every commit the factory makes on a work item's branch with `Git.commit` begins `work item <id>: `. The merge of `origin/main` into a reopened branch (`WorkItemOpening`, `git merge --no-edit`) keeps git's own subject; `git log --name-only` lists no files for a merge, so `make mutants` does not need it. The human decided so on 2026-10-17 (FEATURE decision 51). Nothing else about the commits changes: the commits an agent makes keep the subjects the agent gave them, and the handlers' subjects stay as they are. The tester changes the three subject assertions of `tests/application/test_claims.py` and adds one test to each of three other test modules (FEATURE decision 52).

## Interface

`commit_subject(work_item, text)` stays in `factory.application.handlers.recording` and gives `work item <work_item>: <text>`; `claims.py`, `stage.py`, `stalls.py` and `acceptance.py` import it from there (`acceptance.py` already does; `factory.application.handlers` has an empty `__init__`, so no import cycle arises). The four commits are made as follows, and no other `git.commit` call changes:

| Commit | Where | Subject |
|---|---|---|
| a stage's start | `ClaimService.claim` (`src/factory/application/claims.py`) | `commit_subject(<id>, f"{stage} starts as {instance}")`, `<id>` the work item id in the file name of `path` (`parse_work_item_file_name`, as `_own_branch` reads it) |
| a stage's end | `StageFinisher.finish` (`src/factory/application/stage.py`), the message it gives `_commit_and_push`, now `f"{started.stage} ends: {move.stage}"` | `commit_subject(started.work_item, f"{started.stage} ends: {move.stage}")` |
| a stall | `StallService._commit_and_push` (`src/factory/application/stalls.py`) | `commit_subject(context.work_item, f"{context.stage} stalled")` |
| an acceptance's opening | `AcceptanceService.open` (`src/factory/application/acceptance.py`) | `commit_subject(work_item, "opens")` |

Tests, by the human's leave (FEATURE decision 52), and no other change to an earlier story's test:

- `tests/application/test_claims.py`: the three assertions `assert <commit>.subject == f"{STAGE} starts as {INSTANCE}"` (in `test_stage_start_commit_is_one_commit_on_the_previous_head_with_its_subject`, in the test of a rejected push, and in the test of a kill before the push) expect `commit_subject(WORK_ITEM, f"{STAGE} starts as {INSTANCE}")` instead, imported from `factory.application.handlers.recording`.
- New tests, each in the module that already holds the setup of its commit, with that module's own helpers (no second copy of a helper): `test_the_commit_of_a_stage_end_carries_the_work_item_prefix` in `tests/application/test_stage_finish.py`, `test_the_stall_commit_carries_the_work_item_prefix` in `tests/application/test_stalls.py` and `test_the_opening_commit_carries_the_work_item_prefix` in `tests/application/test_acceptance_service.py`. Each reads the subject with `boundaries.git.log(<commit>)[0].subject` and compares it with a literal text, not with `commit_subject`, so that a change of the helper itself fails them.

## Acceptance criteria

1. The stage-start commit of a claim has the subject `work item F0001-S0001: intake starts as factory-1` (the tester changes the three assertions of `tests/application/test_claims.py` named above; the rejected-push and kill-before-push tests read the local commit, which has the same subject).
2. The commit that ends a stage has the subject `work item <id>: <stage> ends: <next>`: three rows of one parametrized test in `tests/application/test_stage_finish.py`, with the pipeline definition and work item that module builds (`WORK_ITEM` `F0001-S0001`): the `tests` stage ends forward (the agent's decision `doing`) with `work item F0001-S0001: tests ends: doing`; the `docs` stage is sent back (decision `doing`) with `work item F0001-S0001: docs ends: doing`; the `tests` stage ends on a question (the agent's decision is the question) with `work item F0001-S0001: tests ends: tests`.
3. The commit of a stall has the subject `work item <id>: <stage> stalled`: two rows of one parametrized test in `tests/application/test_stalls.py`, a stall of the `tests` stage after a run that died having written inside the write paths (`work item F0001-S0001: tests stalled`), and the same stall after an agent that made a commit of its own, whose commit keeps the subject the agent gave it while the stall commit above it has the prefix.
4. An acceptance opens with the subject `work item F0002-A0001: opens`: one test in `tests/application/test_acceptance_service.py`, on the commit that `AcceptanceService.open("F0002")` pushes.
5. The prefix is that of `commit_subject` and nothing is added to it: `commit_subject("F0001-S0001", "x")` is still `work item F0001-S0001: x`, and the handlers' and recovery's subjects are unchanged (the existing tests of `tests/application/handlers/` and `tests/application/test_acceptance_*.py` that compare them stay as they are and pass).
6. `make check` stays green.
7. docs: in `docs/project-guide.md`, the bullet in *Recording the human's act* that says "Nothing parses commit subjects" says instead that every commit the factory makes on a work item's branch begins `work item <id>: ` (the stage's start, its end, a stall, an acceptance's opening and the handlers' records), except the merge of `origin/main` into a reopened branch, which keeps git's subject, and that a project's `make mutants` reads it to find the modules a feature changed; step 4 of the claim list in *The claim service* names the subject `work item <id>: <stage> starts as <instance>`; `docs/decisions.md` gets one entry, in the form of its other entries, saying why the four commits carry the prefix (F0012 decision 51). No other document changes, no v1 word of the document check is used outside a `## Replaced from v1` section, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider -k "carries_the_work_item_prefix or test_stage_start_commit_is_one_commit_on_the_previous_head" tests/application | tail -1
```
Expect: one line, `7 passed, <m> deselected in <t>s`, with no `failed` or `error` count (three rows of criterion 2, two of criterion 3, one test each for criteria 1 and 4).

```bash
grep -rn 'git.commit(f"' src/factory; echo "status $?"
```
Expect: only the line `status 1`: no commit of the factory is made with a subject that is not built by `commit_subject`.

## Log (append only)

1. 2026-10-17 human: created.
