# Drafter reports (Phase 2)

The drafters' replies, kept so that the cross-feature check and the improvers can act on their open questions.

## F0008-crash-recovery (00:24)

Three stories: S0001 a crash discards the stage and reruns it free (20 criteria; GH2.1–GH2.3, GH1.3 same-name); S0002 the crash cap asks the human (20; GH2.4); S0003 an expired lease, and notes that say retrying only when true (17; ST1.4, GH1.3 other-name). 13 decisions in FEATURE.md: a crash is charged only to a held claim (a kill between one stage's result push and the next claim raises no counter); the rerun happens in the same tick; the crash is one new commit on top of the stage-start commit (claim cleared, `crashes` + 1, journal kind `crash`); an own crash posts nothing; the count after the crash decides the cap; any comment answers the cap question (resets, reruns), a close discards; only a forward move or the answer resets `crashes`; an expiry counts as a crash.

Open questions and gaps in the interface sheet:
1. No names in the sheet for `factory.application.recovery`; chosen `RecoveryHandler(boundaries, definition, claims, run: Handler)` for both `crash` and `expired`, plus `ask_crash_cap`. The sheet has no handler registry (F0010-S0001's wiring and F0011 need one).
2. S0002 changes F0007's comments handler (a `crash_cap` answer resets `crashes`) and F0005's forward-move state in `factory.domain.decisions` by module only: check against F0005-S0006 and F0007-S0007.
3. The crash-cap question is reposted after a kill only if F0007-S0002's `ask` handler covers `blocked == "crash_cap"`, and F0006 raises `ask` for it.
4. F0006-S0002 must map an own claim to `crash`, an expired claim to `expired`, a held claim to `idle`.
5. The stage-start commit is taken to be the head of `origin/<branch>`; F0004 may want a `ClaimService` method for it.
6. The demos build `Boundaries` field by field (15 fields); they break if an earlier feature adds one.
7. `stall_note` is built by F0005-S0004; its "retrying" property is tested in F0008-S0003.
8. S0001 and S0002 have 20 criteria each.

## F0004-claim-and-write-paths (00:26)

Five stories: S0001 the stage-start commit is the claim (16; GH1.2, R19–R21); S0002 one service for claim, expiry and recognition (17; GH1.2 with search tests); S0003 write paths and protected paths read at the stage-start commit (21; R32, WE2.1, WE2.3); S0004 the write-path guard hook (17; WE2.1, WE2.3, R12); S0005 undo and restore after an agent run (19; WE2.1–WE2.3). 15 decisions: protected paths are a fixed list of ten patterns in the engine (the skeleton said "read from the pipeline definition"; the sheet and handover section 8 win); the guard keeps v1's fail-open reading of the payload, an unreadable settings file blocks everything, exit 2 refuses; the undo reverts every other work item in progress and the own cost file; a claim replaces any existing claim and appends a second "started" entry; a lease is expired at an age of at least `lease_duration`, never at a negative age.

Open questions:
1. Names F0004 owns that the sheet lacks: `domain.write_paths.matches_any`, `refusal`, `GuardVerdict`, `judge`, `read_guard_settings`, `GuardSettingsInvalid`, `started_text`; `PushFailed` created in S0001.
2. F0001-S0008's `ClaudeCodeRuntime` must write the guard settings file as `GuardSettings.model_dump_json()`.
3. The coder cannot write `pyproject.toml`: the human adds `factory-guard = "factory.entry.guard:run"` and the sheet's other console scripts.
4. The undo reverts the cost sidecar, so F0005-S0008 must write it after the undo.
5. F0005 must check out the work item's branch before it claims (S0001 requires `Git.status().branch == branch`).
6. F0008 may claim over an expired claim; S0001 allows it.
7. The drafts use v1's headings; v1.1's appear only in code and demos.
8. The demos build `Boundaries` by hand from 15 collaborators.

## F0003-stops-and-pipeline-definition (00:28)

Five stories (the skeleton proposed four; S0004 split): S0001 repository and machine stops, health status and time-stamped lines (22; ST3.4, R27); S0002 work item stops on the pull request, posted once (18; ST3.2, GH3.4); S0003 the pipeline definition schema and its defaults (23; R30, R13, ST8.1 schema half); S0004 loading the pipeline definition, installed agents and a reported stop (22; ST8.1, ST8.3 installed-agent half); S0005 load-time rules (22; ST8.2, ST8.3 write paths, ST8.4, ST8.5, GH1.4, R21). Other drafters may cite F0003-S0004 for ST8; the rules are in S0005. 17 decisions: one stop per reason; both destinations tried; stamp `YYYY-MM-DDTHH:MM:SSZ`; stops are keyed posts, a stop without a pull request reuses the branch's open one or opens a draft; unknown keys, unquoted `contract`, repeated YAML keys refused, all faults listed; `project_commands` replaces the default set; every role's agent must be installed; any minor of contract major 1; a `done` stage required; `human`, `factory`, `question` reserved; the time check is role `time_limit` plus every listed check and report ≤ `lease_duration` (at the defaults a stage with two checks and a report does not fit 60 minutes).

Open questions:
1. `Boundaries` created by F0003-S0001, but `build_boundaries` by F0002-S0005; wiring left to F0010-S0001.
2. `AgentDefinitionInvalid` created by F0003-S0004 (the sheet says F0010-S0006).
3. `StopPosted.opened` defined as true exactly when `stop.pull_request` was `None`.
4. `AgentDefinitionError.name` for a missing agents directory is `""`.
5. `project_commands` typed `dict[Name, ...]`.
6. Exact message texts fixed in S0005; the reader strips pydantic's `Value error, ` prefix.
7. The `boundaries` fixture and checkout path specified in S0001 (`Boundaries.checkout`).
8. S0004 assumes `Git.show_file` returns `None` for a file absent at an existing ref and raises `GitError` for an unknown ref: F0001 to confirm.
9. `fail_next` operation names assumed to be method names.
10. Four stories at 22–23 criteria; the coder's $4 may be tight for S0003 and S0004.

## F0011-proof-and-documents (00:30)

Four stories: S0001 kill-point tests (23; WE1.1, R36; `factory.domain.kill_point_cases`, tests and `tests/proof_support.py`); S0002 the thirteen fault-injection paths and reject walked (20; WE1.2, WE1.3; `factory.domain.fault_paths`); S0003 the stop table (16; ST3.5; `factory.domain.stop_table`, 15 rows); S0004 the four documents (19; WE6.1, WE6.2, WE6.4, WE6.5, R17; `factory.domain.documents` and `python -m factory.entry.check_documents`; WE6.3 not built, per answer 9). 15 decisions: a kill after a stage's result is pushed charges no crash; the restart advances the manual clock by 5 seconds; each path gets one kill or stall, none mapped to a removing item; L11 is a row with destination `none`; machine stops proved through `StopService` plus a search; the document check is not in `make check` and has no console script; the decision log is exempt from the replaced-phrase lists.

Open questions:
1. No signature in the sheet for the tick (F0006-S0004), the wiring or `InstanceSettings`; the stories name a helper `run_ticks` that wraps whatever F0006 builds.
2. Console scripts are outside the coder's write paths (answered: the session adds them in a setup commit).
3. S0001 and S0002 assume the first push of a work item's first stage is its claim (answer 8).
4. A `duplicate` with no branch: F0007-S0008 must handle it.
5. Path 12 reads the acceptance's `outcome` and `done/` location through F0009's `AcceptanceState` and F0006's snapshot reader; names not in the sheet.
6. `fail_next` operation names assumed to be method names; `push-rejected` relies on a bare-remote `update` hook.
7. Path 13 needs `doing` → `tests` to count no round: F0005-S0006 must follow v1's rule for a stage without `round_cap`.
8. Six kill-point rows, as in `fault-paths.md`.

## F0009-feature-acceptance (00:33)

Six stories (the skeleton proposed four): S0001 the acceptance report as data and its place in the order (24; ST6.3; `AcceptanceState`, ids `F0001-A0001`); S0002 when a feature acceptance is due (25; ST6.2); S0003 the acceptance stage and the reviewer's facts (25; GH4.4); S0004 the hand-over at the acceptance's approval (19); S0005 a merge accepts, a close refuses (25); S0006 merged before its approval, and repeated acceptances (19; ST2.1, ST2.2, R31; also the dispatcher wiring through ticks). 16 decisions: each acceptance is its own work item `in-progress/F0001-A0001-acceptance.md`, moved to `done/` when booked; status precedence in flight > merged unrecorded > incomplete > recorded result > due; the opening pushes only the report head; the closing text names no merge method; a refusal keeps the report and its cost records and drops the proposed stories.

Open questions:
1. Its numbering differs from the sheet's "created by" column (S0002 to S0005).
2. No signatures in the sheet for the watcher, `factory.application.work_items`, the tick or the dispatcher's construction; F0006 must supply them.
3. The acceptance report's path chosen: `<feature>/in-progress/F0001-A0001-acceptance.md`, `folder="in-progress"`.
4. S0001 grows F0002's reader and writer (they reject extra keys).
5. Wiring: `SplitByWorkItemKind` routes `hand_over`, `merged`, `closed`; the due handler registered in `factory.entry.wiring`, tested only in S0006.
6. Assumes `entry_text` returns the text after `speaker: ` and the journal heading constant.
7. The acceptance's opening commit is not its stage-start commit (contrary to answer 8): the claim comes on the next tick.
8. Write paths allow overwriting an existing backlog story (as in v1, left for v2).
9. Several S0006 criteria walk earlier stories; the tester may see them pass at once.

## F0005-stage-protocol-and-cost (00:35)

Nine stories: S0001 agent definitions, the prompt and the allowed decisions (21); S0002 opening the work item's branch and its draft pull request (17; ST6.1); S0003 the stage starts with the pushed claim, then the agent run (18; GH1.1, R19); S0004 stalls (19; GH2.5, ST1.4's stall note rule); S0005 after the agent: the branch, the undo, the entry, the form again (18; GH2.5); S0006 the decision rules: questions, rework rounds and caps (17); S0007 checks, reports and the stage's result commit (22; R19, `StageRunner`); S0008 cost records at agent run start and end (15; GH4.1, GH4.2, R24); S0009 bills from the cost records (21; SI1.2, SI1.4, GH4.5). 22 decisions, for example: the pull request number is recorded in the stage's next commit; a stall releases the claim in its own commit; the stall note is posted after the push; only a new form finding stalls; a red check stalls with a 15-line tail; entry 1 is dated with the opening day; cost line and table formats, rounded half up.

Gaps worked around:
1. `StallReason` gains `check_red` and `merge_conflict`; `stall_note` gets keyword-only `detail`; `factory.domain.decisions` is created in S0004.
2. The stage entry is `StageRunner.run(work_item, path)`; F0006's `run` handler and F0007 call it. New names: `WorkItemOpening`, `StageLauncher`, `AfterAgent`, `StageFinisher`, `CostRecorder`, `BillService`.
3. `Boundaries.run_record` and the `tests/conftest.py` fixture change in S0003; the tester updates the fixture.
4. F0004's undo reverts the cost sidecar, so S0008 rewrites it from memory after every undo, and changes S0003, S0004, S0005 and S0007 code.
5. `factory-bill` needs a `pyproject.toml` edit (answered: setup commit).
6. After a claim push, a hosting or agent-runtime error leaves the claim, which F0006 reads as a crash: F0008 to decide.
7. `crashes` resets on a forward move: F0008 changes `decide`.
8. `ProjectCommands` has no fake; S0007's tests use a real `Makefile` pushed to `main`.
9. `section_text` and `JOURNAL` unclear on whether the heading carries `## `.
10. A backlog story's `## Journal` must be empty, and `append_entry` must cope.
11. Most Demos in S0002, S0003, S0005, S0007, S0008 are `uv run pytest <module>` runs.

## F0002-work-item-data (00:37)

Eight stories (the skeleton proposed six): S0001 identifiers, paths and order (18); S0002 work item state (14; R15); S0003 reading and writing work items (18; R13, R15); S0004 sections that respect code fences (18; SI1.3); S0005 journal with speaker and kind as data (19; SI1.1); S0006 story form check (18); S0007 cost record sidecar format (18); S0008 the story check command (20). Renumbering against the skeleton: journal S0005 and sections S0004 (swapped); the skeleton's S0002 split into S0002 (state) and S0003 (reader and writer); form check S0006 and command S0008; cost S0007; `journal.py` created by S0002 with data types only. 12 decisions: only `stage` is required in the front matter, unknown keys (v1's `comments_seen` too) refused, notation fixed; a heading is `## ` at column 0 outside fences; v1's form rules kept plus three new findings; `cost_usd` a JSON string, duplicate run refused; the check command exits 0, 1 or 2 and prints `<path>: ok`.

Open questions:
1. Console script `factory-check-story` (answered: setup commit); the Demo uses `python -m factory.entry.check_story`.
2. `Boundaries` does not exist before F0003-S0001; S0008 builds only `build_work_item_reader()` in `entry.wiring`.
3. Added `check_story_place(path, *, feature_file_exists)` (S0008).
4. Added `split_lines`, `code_blocks`/`CodeBlock`, `required_sections` in `factory.domain.sections`.
5. Fixed fault texts in S0003, S0005, S0007.
6. Closing criterion is the literal `make check stays green.`
7. `started_at` golden lines use a placeholder.
Note for the cross-check: the reader refuses v1's `comments_seen`, while R26 detection (answer 11) needs to recognise it: F0006's detection must not go through the strict reader.

## F0006-reading-the-remote (00:39)

Six stories: S0001 work items read from the remote-tracking refs (22; GH5.1, ST6.1, R18, R26 detection); S0002 the watcher's evaluation in four tiers (24; R26 event, claim tier, one lookup); S0003 the dispatcher and the tick status (24; SI2.4, GH5.4, R28); S0004 the tick: fetch first, then the remote's state (21; GH5.2, GH5.3, GH5.5, GH1.5, R26 stop); S0005 the move rule reads the pull request first (23; ST2.3, ST2.4); S0006 the watcher's command line (21; SI3.1, SI3.2, the board). 14 decisions: a branch that is an ancestor of `origin/main` is still read (deviates from the skeleton's "merged branches absent"); a v1 work item is a file in `ongoing/` or an `in-progress/` story with `comments_seen` or `pr`; only the first waiting work item gets the lookup; a question counts as posted when a factory comment is keyed work item, kind = `blocked`, n = the last journal entry's number; the error report at 3 errors, keyed to the first 12 characters of the remote state; the move rule judges the last commit, corrections marked by journal kind `move_back`; an approval to `done` is always legal; `factory-watch` does not fetch.

Gaps worked around: `ErrorCount.last_error` added; the dispatcher gets an optional `log`, a `status` property, `handler_for`, `unhandled_kinds`; an event with no work item or an unreadable work item file goes to a factory-log line and `WorkItemFormatError` propagates; nobody records the pull request number when a report opens a draft pull request; added `V1_STATE_KEYS`, `StoryFile`, `WorkItemsRead`; `RemoteWorkItems(git, reader)`; v1's `busy` mapped to `idle`; no `run` handler registered (F0005 or the wiring must supply it); `factory-watch` takes `boundaries` and `instance` as arguments.

Open questions:
1. F0005, F0007, F0008 must make the asking entry the last journal entry while `blocked` is set, and key the post with n = its number.
2. Tests assume `HumanClone.push_file` creates a missing branch from `main`, and the agent file format of F0003-S0004.
3. S0002, S0003 (24) and S0005 (23) are large.
4. If the hosting service deletes head branches on merge, a merged but unarchived story is read as new: the operator guide must say so.

## F0010-machine (00:41)

Nine stories: S0001 one instance, one project, one checkout (20; ST7.1–7.3, R2, R25); S0002 the pinned image (19; ST5.1, ST5.2, ST5.4, SI3.3, R29, R4); S0003 the health check and the entrypoint's stops (19; ST3.3, ST3.4 entrypoint lines, R27); S0004 the preflight's items (19; ST5.3, ST4.4); S0005 the probe on the main branch and a stamp keyed to the image (19; ST4.1, ST4.2, ST4.3, ST4.5); S0006 agent files with no dead keys (11; SI4.1, SI4.3, R30); S0007 the shipped agents and settings (14; SI4.2, kept 6); S0008 no hosting-service token in an agent run (19; WE3.2, WE3.5, R33, file side of WE3.3, WE3.4); S0009 agent runs as a second unprivileged user (16; WE3.1). 21 decisions, among them: the base-image digest and six Debian package versions in the Dockerfile are placeholders (not looked up offline); Claude Code 2.1.289 and uv 0.9.2; the preflight runs after the fetch and before the pipeline definition loads; machine items skipped while the image build is unchanged; the lint probe repeats only when `main` moves, 10-minute limit; v1's git-identity item not rebuilt; no skills shipped, the shipped agent bodies hold only a boundary sentence and the entry contents (v1's stage texts for the human to add); an agent's environment is an allow list of five names; the token read from a file, git gets it through a credential helper; agents started by `sudo -n -u agent -- env -i …`.

Open questions:
1. `factory-run` and `factory-health` console scripts (answered: setup commit); the stories use `python -m`.
2. Assumed shapes: `build_boundaries(InstanceSettings)`; the tick accepts `preflight=` and turns `AgentDefinitionInvalid` into a stop; `factory.application.task` composes every `AgentRunRequest`; `ClaudeCodeRuntime` builds v1's flags; `AgentDefinitionInvalid` carries `name` and `key`.
3. The sheet's `AgentDefinition` has no `skills` key, which v1's runner applied; `skills` is refused.
4. Added `Boundaries.settings`, `PreflightStampStore`, `MachineChecks(extra=...)`.
5. Whether `AgentRuntimeError` is right for a refused `sudo` (against a stall): check F0001-S0008.
For the audit: placeholders for the digest and package versions against ST5.1 (no floating reference); no shipped skills or stage texts against kept things 5 and 6 (role and stage instructions).

## F0007-human-on-the-pull-request (00:46)

Ten stories: S0001 the human's comments copied by id (22; GH3.1, GH3.2, R22, R34; builds `CannotHandle`, `target_of`, `require_pull_request`, `WorkItemRecorder`, `CommentCopier`); S0002 questions recorded, then posted (17); S0003 a merge archives the story with its bill (18); S0004 a close before the approval discards the story (13; GH4.3); S0005 a close at the approval sends back, recorded first (20; GH3.3); S0006 an illegal stage change moved back (16; GH3.5); S0007 answers unblock, and comment events are capped (17; ST1.1); S0008 stops that cannot be done are counted errors (10; ST3.1, R28); S0009 the hand-over at the approval, retried from state (20; ST1.2, ST1.3); S0010 the pull request read before every agent run (13; `RunGate`, `human_handlers`). 20 decisions, among them: a comment starting `factory:` is copied, a blank one marked read; the branch is deleted only after the archive or move is pushed; record the close, reopen, then record the decision; the round-cap and send-back answers reset no counter; v1's "last story of the feature" line dropped; any merge method accepted.

Open questions:
1. `CannotHandle` created in S0001 (the sheet says S0008).
2. `Event` has no from/to stages for an illegal change; `RejectHandler` derives them from the branch head and its parent.
3. Assumes `entry_text` returns the text without number, date and speaker.
4. Assumes `Git.log(..., since=...)` means commits not reachable from `since`.
5. S0009 adds `DESCRIPTION` to `factory.domain.sections`.
6. S0006 marks corrections with "moved back" in the commit subject; F0006's move rule must exempt it (F0006 uses journal kind `move_back`).
7. S0007 builds the crash-cap answer (`crashes` to 0); F0008 must not rebuild it (F0008-S0002 also claims it).
8. F0009 extends `MergedHandler` and `ClosedHandler` for acceptances.
9. F0006's tick or wiring must call `human_handlers(boundaries, definition, run)`.
10. The S0003 and S0004 demos use real git with local identity and `SimpleNamespace` for `Boundaries`.

## F0001-boundaries (00:50)

Eleven stories (the skeleton proposed eight): S0001 kill points in the wrappers (17; R36); S0002 hosting-service interface and DTOs (17; R10, R6, R7, R34, kept 11); S0003 PyGithub client and its one error type (22; SI2.1, SI2.2, R9); S0004 git wrapper: process, fetch, refs (25; R9, R5); S0005 git wrapper: clone, checkout, commit, push (24; R9, R36); S0006 project commands and the make class (23; R11, R8, kept 8, 17); S0007 agent-runtime interface, DTOs, fake (25; R12, R7, kept 20); S0008 the `claude -p` runtime (25; R12, R24); S0009 git wrapper: history and work tree (22); S0010 git wrapper: branches, merge, reset, revert (26); S0011 the hosting-service fake (20; SI2.3). 16 decisions, among them: S0002 creates the first part of `identifiers`, `git` and `paths` (F0002 must not create them again); `last_line` skips make's own lines; the resume message says `question`; resume budget a quarter, at least 0.50, one `time_limit` across both calls; git calls ignore user and system config and every commit is by `factory <factory@noreply.invalid>`.

Needs the human before S0004: the one `Popen` in `process.py` needs `noqa: S404`, `nosec B404`, `noqa: S603`, `nosec B603`, which `CLAUDE.md` lists under "Not without asking".

Open questions:
1. F0002 must not create `identifiers` and `paths` again.
2. S0004 puts shared fixtures in `tests/conftest.py` (`remote`, `checkout`, later `human`); the feature folder content is minimal.
3. `claude` flags taken from v1's text; `--permission-prompts` and `--tools ""` not checked against the pinned version.
4. PyGithub member names confirmed against 2.10.0.
5. `MakeProjectCommands` stores `kill_points` but never reaches a point.
6. S0010 is at the 26-criteria cap.
7. `run_process` kills the process group with POSIX calls (Linux container only).
8. `HostingService.close` stays.
For the audit: a commit identity fixed in code against R25's environment (the instance's identity).
