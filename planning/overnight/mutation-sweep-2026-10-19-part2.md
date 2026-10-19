# Mutation sweep of factory-rf, 2026-10-19, part 2

The brief: `planning/overnight/briefs/mutation-sweep.md`, continued after the first report, `planning/overnight/mutation-sweep-2026-10-19.md`, which swept `factory.domain` only. This run swept the next layers in the brief's order, `application` first, with a limit of 120 minutes of mutmut. The copy was a fresh copy of factory-rf in `C:/Users/pasca/AppData/Local/Temp/mutsweep2/repo`, with no `.git`, no `mutants/`, no `image/secrets/` and no `planning/`, already converted to LF line endings. Its `.venv` held every locked dependency group, so nothing was installed. Every run was a throwaway container of `factory-self-factory` (`--network none --cpus 2`, the image's own user, `UV_CACHE_DIR` inside the copy, no volume but the copy). The copy has been removed.

## 1. The run

- **mutmut** 3.8.0, run as `pyproject.toml`'s `[tool.mutmut]` sets it up (its `also_copy` and its 13 deselected tests), limited to the layer by the module pattern `"factory.application.*"`. One run: `umask 022`, a `TMPDIR` of its own, `--max-children 2` (two cores, because two factory instances ran beside it), `timeout 7200`. Its `.git` folders under `mutants/` were removed afterwards, as `make mutants` does.
- **Count**: 14,951 mutants in 128 modules (the first sweep counted 14,714; `main` has grown since): domain 3,742, application 5,877, entry 1,415, adapters 3,917. `contract` still holds no Python module, only the `*.schema.json` files, so it has no mutants.
- **Time**: **7,200 s, 120 minutes of mutmut**, stopped by `timeout` (exit 124) inside `application`. About 12 minutes of that went to mutmut's one-off steps: generating the mutants (40 s), the clean run and the stats run. The mutants then ran at about 0.55 a second on two cores. That is about as fast as the first sweep's 0.63 a second on three cores, because the application tests are lighter per mutant than the tests of the widely imported domain modules.
- No fault in the copy this time. The LF copy passed the clean run and the stats run on the first try.

Counts by status, `factory.application` (the only layer swept):

| module | killed | survived | timeout | not checked |
|---|---|---|---|---|
| acceptance | 667 | 27 | | 23 |
| acceptance_reading | 112 | 7 | | 239 |
| board | 59 | 3 | | |
| claims | 12 | | | 133 |
| costs | 64 | | | 108 |
| disk_records | 52 | | | |
| dispatcher | 99 | 1 | | 38 |
| handlers.closed | 233 | 13 | | 2 |
| handlers.comments | 167 | 13 | | 1 |
| handlers.hand_over | 99 | 6 | | 2 |
| handlers.lookups | 27 | | | |
| handlers.merged | 72 | 3 | | 1 |
| handlers.questions | 138 | 8 | | 2 |
| handlers.recording | 39 | | | 62 |
| handlers.reject | 122 | 10 | | 1 |
| handlers.run | 19 | 1 | | 4 |
| handlers.run_gate | | | | 36 |
| opening | | | | 125 |
| pipeline_loading | 10 | | | 56 |
| preflight | 545 | 5 | | |
| project_commands | 8 | | | |
| provider_limits | 41 | | | 71 |
| recovery | 300 | 35 | | 35 |
| scheduler | 88 | 2 | 1 | |
| sealed_runs | | | | 12 |
| stage | 141 | 8 | | 569 |
| stalls | 169 | 7 | | 14 |
| stops | 99 | 1 | | 78 |
| task | | | | 123 |
| tick | 14 | 1 | | 134 |
| undo | 16 | | | 98 |
| watcher | 14 | | | 79 |
| work_items | 19 | 2 | | 180 |
| write_paths | | | | 52 |
| **application** | **3,445** | **153** | **1** | **2,278** |
| domain, entry, adapters (not run here) | | | | 9,074 |
| **all** | **3,445** | **153** | **1** | **11,352** |

Modules with no mutants of their own (interfaces whose methods are only docstrings, such as `agent_runtime`, `git`, `hosting`, `boundaries`, `files`, `machine`) do not appear.

## 2. Triage

Of the 154 checked mutants that were not killed: **71 equivalent**, **76 missing test** (15 behaviours, 23 commit subjects, 38 messages only), **6 dead or redundant code**, **1 timed out**. The 2,278 application mutants that were not checked are listed together at the end. Rows that share a line and a reason are grouped. The mutant numbers are mutmut's: `mutmut show factory.application.<module>.x_<function>__mutmut_<n>`, or `xǁ<Class>ǁ<method>__mutmut_<n>` for a method.

Three causes explain 49 of the 71 equivalent mutants:
- **The no-state guard cannot fire (41 mutants).** Every handler reaches its work item through `target_of` (`handlers/recording.py:30`), which already requires a state. Some handlers instead go on from a document they built themselves by appending to one that has a state. So the error handed to `require_state` (`_no_state()`, its argument or its message) is never raised, and replacing it with `None` changes nothing.
- **The clock's zone (3 mutants).** `astimezone(None)` is the local zone, and the test container runs in UTC (as in the first sweep).
- **A value no reader uses (5 mutants).** The rerun event's `pull_request` and `remote_state`, which `RunHandler` does not read. The probe's argument to `find_open_pull_request`, where only whether the call raises matters.

| mutant | module:line | status | class | reason |
|---|---|---|---|---|
| _reviewer_role 3 | acceptance:76 | survived | equivalent | `stages.get(None)` is `None`, as the guarded branch gives |
| open 38, 40, 42 | acceptance:125 | survived | equivalent | the feature directory always exists (its feature file was just read), so at most one folder level is created and `parents` never matters |
| _book 19, 21, 23 | acceptance:417 | survived | equivalent | the same: `done/` sits in the existing feature directory |
| open 61 | acceptance:129 | survived | missing test (message) | `PushFailed`'s branch is not pinned when the opening push fails |
| _feature_title 9, 16, 20, 21 | acceptance:176, 179 | survived | missing test (message) | the "missing on origin/main" and "the feature file has no title line" messages are not pinned |
| _waits 6 | acceptance:188 | survived | missing test | no test has an archived story without a state; it must give no waits (the mutant reads `None.journal`) |
| AcceptanceHandOver.handle 52, _show 12 | acceptance (hand over) | survived | missing test | the description's *Findings in short* must come from the reviewer role's last `result`; no test has a later result by another speaker, so `role=None` (any speaker) passes |
| AcceptanceClosed.handle 43 | acceptance:361 | survived | missing test | the same gap when the refusal is booked (`book_refusal(role=None)`); the first sweep found it in `domain.acceptance.refusal_reason` |
| AcceptanceClosed._today 1 | acceptance:380 | survived | equivalent | UTC container |
| AcceptanceClosed._record_close 27, 30 | acceptance:396 | survived | equivalent | only the human ever records a `close`, so the speaker filter changes nothing |
| AcceptanceClosed._record_close 55, 56, 59, 60 | acceptance:399 | survived | missing test (commit subject) | the subject "close recorded" is not pinned |
| AcceptanceClosed._book 40, 41, 44, 45 | acceptance:422 | survived | missing test (commit subject) | the subject "closed, refused" is not pinned |
| AcceptanceReader.document 7, 8, 9, 10; _document 7, 11, 12 | acceptance_reading | survived | missing test (message) | the message and the path of `WorkItemFormatError` ("missing on <ref>", "not an acceptance's state") are not pinned |
| BoardReader.read 5, 6, 7 | board:40 | survived | missing test | no board test has a story in progress that would be missed in the feature rows: the stories `in-progress` must count in the feature's column |
| _error_stop 26 | dispatcher:135 | survived | missing test | no test reaches the error cap with a work item without a state; its stop must carry no pull request (the mutant reads `None.pull_request`) |
| _opencode_login_hint 6, 7 | preflight:313 | survived | missing test (message) | the operator-facing fallback "the factory user" when `agent_user` is unset is not pinned |
| MachineChecks._hosting_service 1 | preflight:381 | survived | equivalent | the probe only checks that the call does not raise; the branch it asks for does not matter |
| Preflight._run_probe 3, 5 | preflight:535 | survived | equivalent | `reset_to(origin/main)` on the next line puts `main` at the same commit either way |
| RecoveryHandler.handle 10; _remote_head 4, 5, 6, 7 | recovery:99, 200 | survived | dead or redundant code | the discard has just checked the remote branch out (the code's own comment); the guard is there for the type, so its `kind` and message never surface |
| RecoveryHandler.handle 27, 28 | recovery:103 | survived | missing test (commit subject) | the subject "<crash or expiry> of stage <stage> recorded" is not pinned |
| RecoveryHandler.handle 50, 53; _note_expiry 4, 7; _record_pull_request 8, 11 | recovery:109, 123, 170 | survived | equivalent (unreachable guard) | the state was required by `target_of` and kept by every append since |
| RecoveryHandler.handle 61, 65 | recovery:116 | survived | equivalent | `RunHandler` reads only the work item of the rerun event, not its pull request |
| _note_expiry 10, 13 | recovery:124 | survived | equivalent | only the factory writes an `expiry` record |
| _note_expiry 11, 14 | recovery:124 | survived | missing test | an expiry at the crash cap: the last factory record is then the crash-cap question, so the note's post key must still take the *expiry* record's number; no test pins the key there |
| _note_expiry 18, 19, 20, 21; ask_crash_cap 11, 26; _dead_run 5, 10, 15, 20 | recovery | survived | missing test (message) | the `CannotHandle` kinds and reasons ("no expiry entry", "not blocked on the crash cap", "no question by the factory", "claim is <status>", "no branch on the remote") are not pinned |
| _record_pull_request 20, 21, 24, 25 | recovery:174 | survived | missing test (commit subject) | the subject "pull request opened" is not pinned |
| _record_pull_request 36, 37 | recovery:176 | survived | equivalent | the returned `branch_commit` goes only into the rerun event's `remote_state`, which `RunHandler` does not read |
| pause_after 3 | scheduler:26 | survived | missing test (message) | the "must not be negative" message is not pinned (the `ValueError` is) |
| pause_after 6 | scheduler:31 | survived | equivalent | at exactly `MAX_PAUSE` one more doubling is capped by `min(pause, MAX_PAUSE)` |
| Scheduler.__init__ 1 | scheduler:49 | timeout | slow or timed out | `_prepare = None` makes every iteration fail, and the loop goes on; the test's time limit caught it; no fault in the code |
| AfterAgent._stall 1 | stage:247 | survived | equivalent | every caller of `_stall` passes a detail |
| AfterAgent._stall 10, 18; StageFinisher._stall_red 22, 30 | stage:258, 367 | survived | equivalent | without the pull request, the stall service's `ensure_pull_request` finds the same open one |
| StageFinisher._stall_red 20 | stage:365 | survived | missing test | without `stage_start` the red-check stall does not undo; the agent's changes were undone before the checks, so only a file a *check* writes outside the write paths would show it, and no test has one |
| StageFinisher._description 3 | stage:416 | survived | missing test | the same reviewer-role gap as the hand-over above, at the acceptance's stage finish |
| _masked 8 | stage:504 | survived | equivalent | the mask is only compared with itself (old and new findings are masked alike) |
| StallService.stall 1 | stalls:64 | survived | missing test | the merge-conflict stall (`stage.py:455`) passes no detail; no test pins that its note and entry carry none |
| StallService.stall 36 | stalls:81 | survived | equivalent (unreachable guard) | the stalled document was just built from one with a state |
| StallService.stall 80 | stalls:95 | survived | dead or redundant code | `StallResult.undo` is read by no code under `src/`; one test pins only its absence |
| StallService._undo 7, 9 | stalls:103 | survived | missing test | no test has an agent that commits on its work branch and then switches to another branch; the stall must start the branch again at the stage-start commit, not at the agent's commit |
| StallService._commit_and_push 18, 19 | stalls:138 | survived | missing test (message) | `PushFailed`'s branch and outcome are not pinned for a stall |
| StopService._require_commit_beyond_main 11 | stops:121 | survived | missing test (message) | the "not on the remote with a commit beyond main" detail is not pinned |
| _Stopped.__init__ 1 | tick:58 | survived | equivalent | the tick reads `.reason`, never the exception's text |
| RemoteWorkItems._started_document 7, 8 | work_items | survived | missing test (message) | the message and the path of "missing on origin/main" are not pinned |
| closed: _no_state 1, 2, 3; _with_state 4; _send_back 49; _record_close 18; _record_decision 4 | handlers/closed | survived | equivalent (unreachable guard) | see the first cause above |
| closed: _record_close 30 | handlers/closed:95 | survived | equivalent | UTC container |
| closed: _send_back 14 | handlers/closed | survived | missing test (message) | "approval stage <x> has no stage to send back to" is not pinned |
| closed: _record_decision 72, 73, 76, 77 | handlers/closed | survived | missing test (commit subject) | the subject "sent back" is not pinned |
| comments: _no_state 1, 2, 3; append 12; copy 12; _question_post 3; _ending_the_wait 20 | handlers/comments | survived | equivalent (unreachable guard) | see the first cause above |
| comments: _entry_of 17 | handlers/comments:49 | survived | equivalent | UTC container |
| comments: copy 31, 32, 35, 36 | handlers/comments | survived | missing test (commit subject) | the subject "comments from the pull request" is not pinned |
| comments: _answer_after 3 | handlers/comments:120 | survived | equivalent | the comments compared are the human's unread ones; the factory's post is never among them, and ids are unique |
| hand_over: _no_state 1, 2, 5, 6; handle 16 | handlers/hand_over | survived | equivalent (unreachable guard) | see the first cause above |
| hand_over: handle 25 | handlers/hand_over | survived | missing test (message) | "stage <x> of <id> is not an approval" is not pinned |
| merged: _archived 24, 25, 29 | handlers/merged:43–45 | survived | equivalent (unreachable guard) | see the first cause above |
| questions: _no_state 1, 2, 3; _record_attempts_cap_question 21, 59 | handlers/questions | survived | equivalent (unreachable guard) | see the first cause above |
| questions: handle 13; _record_attempts_cap_question 16; _post 10 | handlers/questions | survived | missing test (message) | "waits for no question", "has no stall to ask about", "has no recorded question" are not pinned |
| reject: _no_state 1, 2, 5, 6; handle 12, 47; _moved_back 25 | handlers/reject | survived | equivalent (unreachable guard) | see the first cause above |
| reject: handle 31 | handlers/reject | survived | missing test (commit subject) | the work item id in the move-back commit's subject is not pinned |
| reject: _illegal_change 10, 14 | handlers/reject | survived | missing test (message) | "has no stage change to move back" and "is a correction" are not pinned |
| run: handle 6 | handlers/run:33 | survived | missing test (message) | "not a run event: <kind>" is not pinned |
| 2,278 application mutants (see section 4) | stage, work_items, acceptance_reading, tick, claims, opening, task, costs, undo, watcher, stops, provider_limits, recording, pipeline_loading, write_paths, dispatcher, run_gate, recovery, acceptance, stalls, sealed_runs, and 5 handlers with 1–4 each | not checked | slow or timed out | not reached in the 120 minutes; no fault |

Per class: equivalent 71 (41 of them the unreachable no-state guard), missing test 76 (15 behaviours, 23 commit subjects, 38 messages), dead or redundant 6, slow or timed out 1 (+ 2,278 not checked).

The dead code is listed here only, as in the first report. Removing it is a change to the code, so it is not a story. It is the `head is None` guard of `RecoveryHandler._remote_head` (5 mutants) and the `undo` field of `StallResult`, which nothing reads (1 mutant). The 41 unreachable no-state guards are needed for `mypy`'s narrowing, so they are not dead code. A shared helper that raises one fixed error would make them cheaper, but that is not a finding here.

## 3. Proposed stories

The first report's five stories stand. This run extends two of them and adds two. All belong to the feature "the tests pin what mutation testing found". Each changes tests only and fits a coder's 40-minute `time_limit`.

3. **(Extended) Acceptance refusal and the board, and the reviewer's role in the description.** In addition to the first report's criteria: `factory.application.acceptance` and `factory.application.stage`, tests in `tests/application/test_acceptance_hand_over.py`, `test_acceptance_closed.py` and `test_stage_run_acceptance.py`. Criteria: the approval's description takes *Findings in short* from the reviewer role's last `result` when a later `result` by another speaker exists, both at the hand-over and at the stage finish; a closed acceptance books the refusal from the reviewer role's result in the same case; an archived story without a state adds no human waits to the acceptance.
5. **(Extended, low value) The messages of internal guards.** In addition to the first report's 22 domain mutants, 36 application mutants: the `CannotHandle` reasons of the recovery, closed, hand-over, questions and reject handlers; the `WorkItemFormatError` messages and paths of `acceptance`, `acceptance_reading` and `work_items`; `PushFailed`'s branch and outcome from `acceptance.open` and `StallService`; the `ValueError` messages of `pause_after` and `RunHandler`; and the detail of `StopService._require_commit_beyond_main`. Each is a row of a parametrized test in its module's test file. Take this story only if pinned messages are wanted.
6. **(New) The subjects of the commits the factory records.** `factory.application.acceptance`, `recovery`, `handlers.closed`, `handlers.comments` and `handlers.reject`, tests in `tests/application/test_acceptance_closed.py`, `test_recovery_crash.py`, `test_recovery_expiry.py` and the handler tests under `tests/application/handlers/`. Criteria: the subject of the newest commit on the branch or on `main`, as `git log` shows it, is exactly `<id>: close recorded`, `<id>: closed, refused`, `<id>: crash of stage <stage> recorded` (and `expiry of …`), `<id>: pull request opened`, `<id>: sent back`, `<id>: comments from the pull request`, and the move-back subject with its work item id (23 mutants). The human reads these in the history, so they are behaviour, not wording.
7. **(New) Recovery, stalls, the board and the dispatcher at their edges.** `factory.application.recovery`, `stalls`, `stage`, `board`, `dispatcher` and `preflight`, tests in `tests/application/test_recovery_cap.py`, `test_stalls.py`, `test_stage_finish.py`, `test_board_reader.py`, `test_dispatcher.py` and `test_preflight.py`. Criteria: an expiry that reaches the crash cap posts its expiry note under the key of the *expiry* record, not the question's; a merge-conflict stall's note and entry carry no detail; when the agent committed on its branch and then switched to another one, the stall starts the branch again at the stage-start commit; a red check that wrote a file outside the write paths has it undone by the stall; the board's feature row counts the feature's stories in progress; the error cap on a work item without a state posts its stop with no pull request; with `agent_user` unset, the opencode login hint names "the factory user".

## 4. What was not swept, and why

- **2,278 mutants of `factory.application`**, not checked: `stage` 569, `acceptance_reading` 239, `work_items` 180, `tick` 134, `claims` 133, `opening` 125, `task` 123, `costs` 108, `undo` 98, `watcher` 79, `stops` 78, `provider_limits` 71, `handlers.recording` 62, `pipeline_loading` 56, `write_paths` 52, `dispatcher` 38, `handlers.run_gate` 36, `recovery` 35, `acceptance` 23, `stalls` 14, `sealed_runs` 12, `handlers.run` 4, and 1–2 each in `handlers.closed`, `comments`, `hand_over`, `merged`, `questions`, `reject`. The 120 minutes ran out. At the measured 0.55 a second on two cores they take about 70 more minutes, plus about 12 minutes of mutmut's one-off steps.
- **`factory.contract`**: holds no Python, so it has nothing to mutate.
- **`factory.entry` (1,415) and `factory.adapters` (3,917)**: not started. At the same speed they take about 2 h 40 min more, or less with three cores.
- **`factory.domain` (3,742)**: not run again here. The first report's results stand for it, including its 650 mutants that were not checked. Since then `main` has added about 107 domain mutants, which neither run has checked.
- The results stayed in the copy's `mutants/` only, which was removed as the brief asks. The next sweep starts each layer from scratch, so it can take one layer a night, in this order: the application remainder, `entry`, then `adapters`.
