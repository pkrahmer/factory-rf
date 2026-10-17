---
stage: docs
pr: 179
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
2. intake: accepted
   - Interface: names concrete modules and signatures. `commit_subject` in `factory.application.handlers.recording` is reused, not copied. The table gives the four call sites. I checked them against `src/factory`: `claims.py:64`, `stage.py:357` (the message passed to `_commit_and_push`), `stalls.py:129` and `acceptance.py:121` are the only `Git.commit` calls outside `recording.py`. `acceptance.py` already imports the helper. The only behaviour the Interface states is the subject prefix, and criteria 1 to 4 test it.
   - Criteria: each is testable by a test function or parametrized rows. Criterion 1 is the three changed assertions in `test_claims.py`. Criterion 2 has three rows (forward, sent back, question). Criterion 3 has two rows, one with an agent's own commit that keeps its subject. Criterion 4 is one test. Criterion 5 pins the helper and the unchanged handler subjects. The rule has no failing side in the usual sense (no input is rejected). The merge of `origin/main` into a reopened branch is deliberately left alone, and FEATURE decision 53 records that.
   - Demo: both commands are runnable. The expected count of 7 matches the criteria: 3 + 2 + 1 for the new tests, plus 1 for the existing start test. The grep currently matches three lines (`acceptance.py:121`, `claims.py:64`, `stalls.py:129`) and should print only `status 1` after the change. Each `Expect:` line is checkable.
   - Architecture: the change stays inside `factory.application`, and the import runs between sibling modules within a layer with no cycle. The Interface adds no new interface, DTO or dependency.
   - Scope: it is within F0012 (the "What v1.1 writes into its commits" scope line, FEATURE decisions 51 to 53) and not in Out of scope. The test changes are covered by the human's leave in decision 52.
3. tester: the subject tests are written, and the 9 tests that cover the new prefix fail on purpose. Each of them compares a commit subject, and the code does not add the prefix yet. Nothing else in `make test` failed. `make lint` is green.
   - criterion 1: in `tests/application/test_claims.py`, the three subject assertions now expect `commit_subject(WORK_ITEM, f"{STAGE} starts as {INSTANCE}")`. `commit_subject` is imported from `factory.application.handlers.recording`. The three tests are `test_stage_start_commit_is_one_commit_on_the_previous_head_with_its_subject`, `test_a_rejected_push_raises_push_failed_and_leaves_the_remote_without_claim` and `test_a_kill_before_push_is_not_caught_and_leaves_the_remote_without_claim`.
   - criterion 2: `tests/application/test_stage_finish.py::test_the_commit_of_a_stage_end_carries_the_work_item_prefix`, with three rows: `forward` (tests → doing), `sent-back` (docs → doing) and `question` (tests, QUESTION → `tests ends: tests`). It uses the module's `_aftermath` and `_finish` helpers and reads `boundaries.git.log(report.commit)[0].subject`.
   - criterion 3: `tests/application/test_stalls.py::test_the_stall_commit_carries_the_work_item_prefix`, with two rows. `no-agent-commit` is a died run with writes inside the write paths. `agent-commit` adds a commit by the agent before the stall: the stall commit has the prefix and the agent's commit below it keeps its own subject.
   - criterion 4: `tests/application/test_acceptance_service.py::test_the_opening_commit_carries_the_work_item_prefix`, on `opened.commit` from `AcceptanceService.open("F0002")`.
   - criterion 5: no new test. The existing tests of the handler and acceptance subjects are unchanged and still pass. Per the Interface, the new tests compare against literal text, not against `commit_subject`, so a change to the helper itself makes them fail.
   - criteria 6 and 7: these are the coder's and the documenter's, so there are no tests for them.
   Files: three new test functions in the three modules above, and the change in `test_claims.py`. No new files. Every module imported fine. The failures are subject mismatches only, not import errors. I chose not to test the merge of `origin/main` on reopening: the assignment leaves that merge as it is.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/application/test_stalls.py::test_the_stall_commit_carries_the_work_item_prefix[agent-commit]
4. coder: all four factory commits on a work item's branch now take their subject from `commit_subject`. `make check` is green.
      - `src/factory/application/claims.py`: the stage-start commit is `commit_subject(_work_item_id(path), f"{stage} starts as {instance}")`. The new private helper `_work_item_id(path)` holds the file-name parse that used to sit in `_own_branch`, and `_own_branch` now calls it. That keeps the parse in one place instead of two.
      - `src/factory/application/stage.py`: `StageFinisher.finish` builds `commit_subject(started.work_item, f"{started.stage} ends: {move.stage}")` and passes it to `_commit_and_push`, which is unchanged.
      - `src/factory/application/stalls.py`: `_commit_and_push` commits `commit_subject(context.work_item, f"{context.stage} stalled")`.
      - `src/factory/application/acceptance.py`: `open` commits `commit_subject(work_item, "opens")`.
      - Design: I imported `commit_subject` from `factory.application.handlers.recording` as the Interface says, with no import cycle. I rejected the alternative of applying the prefix inside `_commit_and_push` or in the `Git` wrapper: that would also change the subjects of the handlers and of the agents' commits, which the assignment keeps.
      - Refactor: I read the diff (16 lines added, 6 removed) and nothing needed changing, so there is no refactor commit.
      - Checks: commit "feat(application): prefix the factory's own commits with the work item id". Both demo commands print what the ticket expects: `7 passed, 1126 deselected`, and the grep prints only `status 1`. `make duplicates`: 0 new, 39 known, 0 gone.
      - Open: the docs criterion (7) is the documenter's. I did not change the merge of `origin/main` on reopening, as the assignment asks.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
   - Criteria: criterion 1 is covered by the three changed assertions in `tests/application/test_claims.py`. Criterion 2 is covered by `test_the_commit_of_a_stage_end_carries_the_work_item_prefix` in `tests/application/test_stage_finish.py`, whose three rows (forward, sent-back, question) compare against literal subjects. Criterion 3 is covered by `test_the_stall_commit_carries_the_work_item_prefix` in `tests/application/test_stalls.py`. It has two rows, and the agent-commit row also checks that the agent's commit directly below keeps its own subject. Criterion 4 is covered by `test_the_opening_commit_carries_the_work_item_prefix` in `tests/application/test_acceptance_service.py`. The new tests use their modules' own helpers (`_aftermath`/`_finish`, `_started`/`_context`/`_stall`, `_push_todo`/`_service`) and copy no helper. For criterion 5, the diff leaves `commit_subject` and the handler tests untouched. The rule has no rejected input, so there is no failing side to test. The coder's entry says `make check` was green.
   - Architecture: the four call sites in `claims.py`, `stage.py`, `stalls.py` and `acceptance.py` import `commit_subject` from `factory.application.handlers.recording`. That module imports only `boundaries`, `git` and domain modules, so no cycle arises. Every change stays in `factory.application`. `grep 'git.commit(' src/factory` shows the subjects of all four commits built by `commit_subject`. `stage.py:359` passes on the message that `finish` builds with it, and `recording.py` is unchanged.
   - Security: nothing relevant changed. No markers were added and no strings reach a shell.
   - Quality: the new `_work_item_id` in `claims.py` takes the file-name parse out of `_own_branch` and is used by both, so the parse is not duplicated. Names are clear and there is no dead code.
   - Hygiene: the coder's entry names the main decision and the rejected alternative (adding the prefix in `_commit_and_push` or in the `Git` wrapper). `Assignment` matches what was built. Criterion 7 still describes what the documenter must write.
