# Skeleton: the features of v1.1 in build order

## Summary

- v1.1 is built in eleven features, F0001 to F0011, with 66 proposed stories; ids are a topological order, so v1 can build them in plain id order.
- The plan's ten features are kept with one split added: crash recovery becomes its own feature, F0008, because its conditions need the stage protocol (F0005), the watcher's first look (F0006) and a question to the human at the crash cap (F0007). The plan's features 7 to 10 become F0007, F0009, F0010 and F0011.
- Other changes to the plan's split, each for a named gap (section Dependencies and Sources): the guard, undo and restore move from feature 5 to F0004, where WE2 tests them; GH1.1 and GH2.5 go to F0005, GH1.4 to F0003, GH1.5 to F0006; GH3.4 goes to F0003, so the stop service posts once from the start; the dispatcher, the tick status and SI2.4 go to F0006, where GH5.4 needs them; GH4.3 goes to F0007 (the discard); ST1.4 goes to F0008 (the expiry).
- 88 of the 96 acceptance conditions are in the build order; 8 are not tonight (WE1.4, WE4.1 to WE4.3, WE5.1 to WE5.4). Five conditions become a static test plus a morning observation: ST3.3, ST5.1, WE3.1, WE3.3 and WE3.4.
- Every dependency of the plan's table holds. Seven rows hold at the level of conditions, which is how the plan itself splits SI1, ST3/ST8 and ST2/SI2.
- F0001 (boundaries) is useful alone: every later feature reaches git, the hosting service, the project commands and the agent runtime only through it. It has eight stories, and Open question 13 asks whether that is small enough.
- Open questions that the interface sheet or the operator must settle before drafting: the expiry of another instance's lease, the run record and lock, a dirty main branch, keyed posts, the v1.1 spellings, the write paths for `image/`, `template/` and `claude/`.

## Build order

| Feature | Title | Goal | Items and conditions |
|---|---|---|---|
| F0001-boundaries | Boundaries | The factory reaches git, the hosting service, the project commands and the agent runtime only through wrappers and interfaces with factory-shaped DTOs, each with a fake or a real local stand-in for tests. Done when every one of the four is callable through its interface, a fake exists for the hosting service and the agent runtime, and a search finds no other call to an outside tool. | SI2.1, SI2.2, SI2.3; R5, R6, R7, R8, R9, R10, R11, R12, R34, R36 |
| F0002-work-item-data | Work item data | A work item's identity, state, journal, sections and cost records are read and written as validated data by one reader and one writer per format. Done when a story can be read, checked against the form and written back, its journal entries carry speaker and kind as data, and cost records round-trip through the sidecar file. | SI1.1, SI1.3; R13, R15 |
| F0003-stops-and-pipeline-definition | Stops and the pipeline definition | Every stop has one destination, and the pipeline definition is validated when it loads. Done when a work item's stop is posted once on its pull request (opened first if missing), a repository or machine stop fails the health status with a time-stamped line, and an invalid pipeline definition is a reported stop that names the fault. | ST3.2, ST3.4, ST8.1–ST8.5, GH1.4, GH3.4; R21, R27, R30 |
| F0004-claim-and-write-paths | Claim and write paths | The pushed stage-start commit is the claim, and an agent's write paths come from it. Done when one service creates, reads, recognises and expires claims, and the guard and the undo both read the write paths from the stage-start commit, so a rewrite in the work tree widens nothing. | GH1.2, WE2.1–WE2.3; R19, R20, R21, R32 |
| F0005-stage-protocol-and-cost | Stage protocol and cost | One stage runs the same steps in the same order around one agent run, and every agent run's cost is recorded in the work item. Done when a stage starts only after its claim is pushed, its result is decided and committed by code, a stall costs an attempt with undo and restore applied, and the bill of a stage and a story is computed from the cost records alone. | GH1.1, GH2.5, GH4.1, GH4.2, GH4.5, SI1.2, SI1.4; R19, R24 |
| F0006-reading-the-remote | Reading the remote | Each tick fetches, reads every work item from the remote-tracking refs and dispatches one event, with errors counted per event and remote state. Done when a hand push to a remote branch is seen past a stale local branch, a failed fetch or rejected push stops the tick and is reported once, every event kind has a handler or raises, and no merge method is misread as an illegal stage change. | GH5.1–GH5.5, GH1.5, ST6.1, ST2.3, ST2.4, SI2.4, SI3.1, SI3.2; R18, R26, R28 |
| F0007-human-on-the-pull-request | The human on the pull request | Every act of the human on the pull request is recorded in the work item before any effect, and every handler of those acts either completes, retries or is reported. Done when comments are copied by id, questions are recorded then posted, merge, close and send-back each keep the human's act, the hand-over is retried from state, and every comment event is bounded by the error cap. | GH3.1, GH3.2, GH3.3, GH3.5, GH4.3, ST1.1, ST1.2, ST1.3, ST3.1; R22, R28, R34 |
| F0008-crash-recovery | Crash recovery | A crash discards the stage in flight and reruns it free, and an expired lease is recognised. Done when a restart with the same instance name reruns the interrupted stage at its first look with no writes of the dead stage in history, the `crashes` counter asks the human at its cap, and no note says "retrying" unless the next tick retries. | GH2.1–GH2.4, GH1.3, ST1.4; R23, R24 |
| F0009-feature-acceptance | Feature acceptance | A complete feature is judged as a whole by the acceptance reviewer, and the human's merge or close decides the result. Done when an acceptance becomes due by counting story files only, sorts after its stories whatever the slug, is costed alone, and a merge before its approval or a repeated acceptance neither loops nor stays due. | ST2.1, ST2.2, ST6.2, ST6.3, GH4.4; R31 |
| F0010-machine | The machine | One pinned container runs one project, checks itself before work, reports its own stops through its health check, and keeps the hosting-service token out of every agent run. Done when the image has no floating reference, the preflight probes the main branch with a stamp keyed to the image, agent files hold only applied keys, and an agent run holds no credential. | ST3.3, ST4.1–ST4.5, ST5.1–ST5.4, ST7.1–ST7.3, SI3.3, SI4.1–SI4.3, WE3.1–WE3.5; R2, R4, R25, R27, R29, R30, R33 |
| F0011-proof-and-documents | Proof and documents | Recovery is proven by named injection tests, every stop is listed with its destination, and the four documents describe what v1.1 does. Done when each kill point and each of the thirteen fault-injection paths has its test or its removing item, the stop table has a test per row, and the four documents exist in the glossary's names with nothing an item replaced. | WE1.1, WE1.2, WE1.3, ST3.5, WE6.1–WE6.5; R17, R36 |

## Features

### F0001-boundaries: Boundaries

**Goal.** Every outside party is reached through one boundary: the git command-line tool through a wrapper class, the hosting service through an interface with a PyGithub implementation and one fake, the project commands through an interface with a make-based class, and the agent runtime through an interface with a `claude -p` implementation and a fake. Inputs and outputs are Pydantic DTOs shaped by the factory, and named kill points in the wrappers let later tests inject a crash. The feature is useful on its own: everything after it calls only these interfaces. Done when each interface has its first implementation and the tests run against the fakes and a real local bare git remote, and a search finds no call to an outside tool outside the wrappers.

**Scope.**
- Named kill points: an injection seam in the wrappers, inert unless a test arms it (R36).
- Hosting-service interface (R10): create a pull request as draft or ready, find the open pull request of a branch, read state and merge state, list comments with id and author, post with the marker, close, reopen, mark draft and ready, replace the description, write labels; one error type for every failing call (SI2.2); one fake implementing it (SI2.3).
- The PyGithub implementation, and a search test that no other code reaches the hosting service (SI2.1).
- Git wrapper with DTOs (R9): fetch with prune, remote-tracking refs, a file at a commit, ancestry, log, paths changed since a commit, status, branch and check out, commit, push with its outcome (pushed, rejected, unreachable), fast-forward, merge of the main branch with abort on conflict, reset and clean, delete a branch, clone.
- Project-commands interface and the make class (R11): run a named command under a `time_limit`, judged by exit status, with the last line and the tail of the output; a generic check result with no layer names (R8).
- Agent-runtime interface, DTOs and fake (R12): request (agent definition, prompt, allowed decisions, `time_limit`, budget, working directory, environment, hook settings), result (end reason, decision and entry, duration, turns, tokens, cost, permission denials, cost and tokens marked unknown when not reported).
- The `claude -p` implementation: v1's flags, the budget resume once, the `time_limit`, the version query used later by the preflight.

**Out of scope.**
- The write-path guard hook and what it refuses: F0004.
- Reading agent files from disk and composing the prompt: F0005; the keys an agent file may hold: F0010.
- Scrubbing the agent's environment and the second OS user: F0010.
- When to post, what to post, and idempotent posting: F0003 and F0007.
- Kill-point tests themselves: F0011 (F0008 uses the seam too).

**Kept things.** 8 (a check is its exit status), 11 (posts carry the factory's marker), 17 (the project is reached through its project commands only), 20 (every agent run's duration, turns, tokens and cost are reported).

**Rules.** Implements R5, R6, R7, R8, R9, R10, R11, R12, R36 (the seam); obeys R3, R4, R34 (the marker tells the factory's posts apart; no author counting).

**Base behaviour rebuilt.**
- `v1-04-08.md`, Chapter 7 "Shared helpers" (`github.py` operations, the marker, `repo.py`'s failing steps) and Chapter 6 "Reading the pull requests".
- `v1-04-08.md`, Chapter 8 "Starting the agent" (flags, result fields, budget resume, end reasons, `AGENT_ENV`).
- `v1-12-15.md`, Chapter 12 "The control surface"; Chapter 13 "Staying in step" and "Branches" (`repo.delete`).

**Proposed stories.**
- S0001 — Kill points in the wrappers. Builds R36's seam: named points, inert by default, raise when armed. New in v1.1. 8 criteria.
- S0002 — The hosting-service interface, its DTOs and the fake. Builds SI2.3, R10, the marker (kept 11). 16 criteria.
- S0003 — The PyGithub hosting client and its one error type. Builds SI2.1 (a search test), SI2.2, R9; tested against stand-ins of PyGithub's objects, no network. 14 criteria.
- S0004 — The git wrapper: reading. Builds R9, R7 for fetch, refs, files at a commit, ancestry, log, changed paths, status; tests against a real bare remote in `tmp_path`. 16 criteria.
- S0005 — The git wrapper: writing. Builds R9 for branch, check out, commit, push with its outcome, fast-forward, merge of the main branch with abort, reset and clean, delete, clone; the kill point between a commit and its push. 18 criteria.
- S0006 — The project-commands interface and the make class. Builds R11, R8; keeps 8 and 17 (exit status, tail of the output). 12 criteria.
- S0007 — The agent-runtime interface, its DTOs and the fake. Builds R12, R7; keeps 20 (the result's measures). 14 criteria.
- S0008 — The `claude -p` agent runtime. Builds R12's first implementation: flags, `--json-schema`, the budget resume, the `time_limit`, end reasons with cost and tokens marked unknown, the version query; tested with a stand-in executable. 20 criteria.

### F0002-work-item-data: Work item data

**Goal.** A work item's parts are data with one reader and one writer each: identifiers and paths that sort, state in the YAML front matter, a journal in the body whose entries keep speaker and kind as data, sections found without regard to headings inside code fences, the story form check, and the cost-record sidecar file. Done when a story can be read, validated against the project's form, edited and written back with its key order, its journal read back by speaker and kind without parsing the text, and cost records round-trip through the sidecar file.

**Scope.**
- Identifier patterns, story and feature ids, branch names, paths of the lifecycle folders, plain string order.
- The state DTO in the front matter (R15): stage, blocked, round, attempts, crashes, ids of comments read, pull request number; fixed key order; initial values.
- The journal (SI1.1): numbered, append-only entries with speaker and kind kept as data; continuation indent; only the human's entries dated; putting one version's journal into another (for the restore).
- Sections (SI1.3): the title, the `## ` sections, the required sections taken from the project's story form, inserting a paragraph under a heading; code fences respected.
- The story form check and its command for the human (v1's `factory-check-story`).
- The cost-record sidecar format (R15): one JSON line per record, a reader and a writer, unknown cost and tokens.

**Out of scope.**
- Which state a stage writes and when: F0005, F0007.
- The acceptance report's extra fields (`stories`, `outcome`) and the feature form's reader: F0009.
- When a cost record is written and how bills are summed: F0005.
- The order of an acceptance against its stories: F0009 (ST6.3).

**Kept things.** 4 (the work item is the memory: specification, state, journal), 9 (the form is checked by code).

**Rules.** Implements R13 (readers and writers), R15 (state, journal, sidecar); obeys R3 (names in file formats), R7.

**Base behaviour rebuilt.** `v1-04-08.md`, Chapter 4: "Where work items live", "Identifiers", "The story form", "The state fields", "The log", "Form validation"; `v1-12-15.md`, Chapter 14 "Cost records" (the record's fields).

**Proposed stories.**
- S0001 — Identifiers, paths and order. Builds the id patterns, branch names, folder paths and plain string order (kept 15's order; R3 spellings from the interface sheet). 12 criteria.
- S0002 — Work item state in the front matter. Builds R15's state fields, key order, initial values, R13's reader and writer. 14 criteria.
- S0003 — The journal with speaker and kind as data. Builds SI1.1; keeps 4 (append-only, numbered, attributed); the restore of a journal from another version. 16 criteria.
- S0004 — Sections that respect code fences. Builds SI1.3; the title rule, required sections from the project's form, insert under a heading. 10 criteria.
- S0005 — The story form check and its command. Keeps 9: v1's form rules (criteria numbered, the two closing criteria, every smoke-test block followed by `Expect:`, journal numbered, place of the file). 14 criteria.
- S0006 — The cost-record sidecar format. Builds R15's sidecar and R13's reader and writer; cost and tokens marked unknown, never zero. 10 criteria.

### F0003-stops-and-pipeline-definition: Stops and the pipeline definition

**Goal.** One stop service sends every stop to its destination: a work item's stop to its pull request, opening the draft pull request first when there is none, and posted only once; a stop of the repository or the machine to the health status and a time-stamped line of the container's output. The pipeline definition is a Pydantic schema with defaults, read with ruamel.yaml and validated at load, and an invalid one is a reported stop, not a crash on every tick. Done when each stop reaches its destination once and every validation of ST8 refuses its case with a stop that names it.

**Scope.**
- Repository and machine stops (R27): the health status the health check will read, set and cleared; every line about a stop time-stamped (ST3.4); the factory log.
- Work item stops (ST3.2, R27): posted on the pull request; without one, the draft pull request opened first; a repeat after a kill posts nothing (GH3.4).
- The pipeline definition schema (R30): stages with their agent, approval, `next`, checks, reports, round cap; per role `lease_duration` (default 60 minutes) and `time_limit`s; the attempts cap (default 2) and the crash cap (default 2); write paths per agent; the contract version.
- Load-time validation (ST8, GH1.4): missing keys without default, `next` naming no stage, an agent without write paths or not installed, an unknown major contract version, `time_limit`s that do not fit inside `lease_duration`.

**Out of scope.**
- The handlers that post questions, answers and send-backs: F0007.
- The health check command, the container's restart policy and the entrypoint's own stops: F0010 (ST3.3).
- The keys an agent file may hold: F0010 (SI4).
- The table of all stops: F0011 (ST3.5).

**Kept things.** 7 (the pipeline definition is the project's configuration), 11 (every stop is one post on the pull request), 12 (a stop is reported, never carried past).

**Rules.** Implements R21 (validation of the lease), R27, R30; obeys R13, R22 (state before effect, for the keyed post), R23 (the crash cap's default).

**Base behaviour rebuilt.**
- `v1-04-08.md`, Chapter 5 "The stage table, key by key" and "Names in the code" (the schema's limits).
- `v1-04-08.md`, Chapter 7 "The tick's memo" (the give-up post, which F0006 reuses through this service).
- `v1-09-11.md`, Chapter 10 "What the factory posts".
- `v1-12-15.md`, Chapter 14 "What the human sees of the machine" (time-stamped lines, the factory log).

**Proposed stories.**
- S0001 — Repository and machine stops: health status and time-stamped lines. Builds ST3.4, R27 (repository side); keeps 12. 10 criteria.
- S0002 — Work item stops on the pull request, posted once. Builds ST3.2, GH3.4, R27 (work item side); keeps 11. 14 criteria.
- S0003 — The pipeline definition schema and its defaults. Builds R30's schema, R13's reader; keeps 7. 16 criteria.
- S0004 — Load-time validation of the pipeline definition. Builds ST8.1–ST8.5, GH1.4, R21; each refusal a reported stop through S0001. 18 criteria.

### F0004-claim-and-write-paths: Claim and write paths

**Goal.** A stage is claimed by pushing a stage-start commit whose "started" journal entry names the instance and the start time; one service creates, reads, recognises and expires claims on the remote-tracking refs. The write paths an agent may write, and the protected paths no one may write, are read from the pipeline definition at that stage-start commit, both by the guard hook during the agent run and by the undo and restore after it. Done when a rewrite of the pipeline definition in the work tree widens nothing and breaks nothing, and the claim service is the only module that knows claims.

**Scope.**
- The stage-start commit with its "started" entry, pushed; a rejected or unreachable push is no claim (R19, R20).
- The claim service (GH1.2): own claim, a claim held by another name within its lease, an expired claim; `lease_duration` per role; the clock from the interface sheet.
- Write paths and protected paths (R32): the matching rule, the protected paths outside every write path, read at the stage-start commit.
- The guard hook command for the agent runtime (refuses Edit and Write outside the write paths).
- Undo and restore (WE2): paths changed since the stage-start commit outside the write paths reverted or deleted, other work items in progress undone, the work item's state and journal restored, a deleted work item restored.

**Out of scope.**
- Starting the agent run after the claim: F0005 (GH1.1).
- When the undo runs (after an agent run, after a stall): F0005.
- Recognising a claim at the tick's first look and the events for it: F0006; rerunning after a crash: F0008.
- Writes to ignored paths or outside the checkout (left for v2, handover section 8).

**Kept things.** 5 (write paths refused by a hook and reverted by the undo; state and journal restored), 13 (recovery from what is on the remote), 17 (protected paths outside every write path).

**Rules.** Implements R19, R20, R21 (the lease runs from the stage-start commit), R32; obeys R12 (hook scripts), R18.

**Base behaviour rebuilt.**
- `v1-04-08.md`, Chapter 6 "The run record" (what the claim replaces).
- `v1-04-08.md`, Chapter 8 "After the agent" (the lane undo, the restore of state and log, v1's lanes) and the limits under "The hand-over" (the lane read from the work tree).
- `v1-12-15.md`, Chapter 12 "Protected paths".

**Proposed stories.**
- S0001 — The stage-start commit is the claim. Builds R19, R20: the "started" entry with instance name and start time, pushed; no claim without the push. 12 criteria.
- S0002 — One service for claim, expiry and recognition. Builds GH1.2 (with its search test), R21's lease per role. 12 criteria.
- S0003 — Write paths and protected paths read at the stage-start commit. Builds R32; keeps 17. 12 criteria.
- S0004 — The write-path guard hook. Builds the hook command and its settings for the agent runtime; keeps 5. 10 criteria.
- S0005 — Undo and restore after an agent run. Builds WE2.1, WE2.2, WE2.3; keeps 5 (other work items undone, state and journal restored). 16 criteria.

### F0005-stage-protocol-and-cost: Stage protocol and cost

**Goal.** Every stage runs the same steps in the same order: compose the task from the pipeline definition, open or prepare the work item's branch and its draft pull request, push the claim, run the agent, apply the undo and restore, write the entry, check the form again, decide by v1's rules, run the checks and reports, and commit the result. Any result the factory cannot keep is a stall that costs an attempt. Every agent run has a cost record from its start, and bills are computed from the records alone. Done when a stage moves, stalls or asks exactly as v1's decision rules say, with the claim pushed before the agent run and the cost records in the stage's next commit.

**Scope.**
- Agent definitions read from the agent home, the task's lines, the allowed decisions and the outcome schema from one source, the pipeline definition.
- Opening the branch with initial state (the backlog file's own state fields dropped), preparing a later stage (fast-forward, merge of the main branch, conflict aborted), the draft pull request (only an open one reused).
- The stage start: claim pushed first, no agent run without it (GH1.1); the guard settings; `time_limit` and budget.
- Stalls (GH2.5): attempts + 1, the stall entry, partial work inside the write paths committed, undo and restore applied whatever ended the run, the stall note with attempt and reason.
- After the agent: the branch test, undo and restore, the entry written by code with speaker and kind, the form checked again.
- The decision rules 1 to 7: questions, rework rounds and their caps, the round-cap question, checks in order with the red tail, reports after green, the forward move; the result commit and push; labels written as a projection of the stage.
- Cost records (GH4.1, GH4.2, R24): created at agent run start, completed at its end, committed with the stage's next commit; `ok: false` counted; unknown cost and tokens.
- Bills (SI1.2, GH4.5): per stage and per story from the records; the cost table and cost line; the command that prints them; a search that no code reads data from journal text (SI1.4).

**Out of scope.**
- The hand-over at the approval and the cost table posted there: F0007.
- Reading the pull request's state before the agent run: F0007.
- The "retrying" wording of notes: F0008 (ST1.4).
- Crash discard and rerun: F0008.
- The image recorded in each cost record: F0010 (ST5.4).
- The acceptance reviewer's facts and an acceptance's cost: F0009.

**Kept things.** 1 (the agent judges, code applies), 4 (each stage starts from the committed work item), 5 (same steps in the same order; form checked before and after), 8 (green means the factory ran the check), 9 (intake gets the form's findings), 10 (`question` always allowed), 14 (rework and stall counted apart), 20 (a cost record per agent run).

**Rules.** Implements R19 (the stage's result is a pushed commit), R24; obeys R7, R11, R12, R15, R21, R23 (a stall, not a crash), R32.

**Base behaviour rebuilt.**
- `v1-04-08.md`, Chapter 8: "Before the agent", "The task", "The outcome schema", "Starting the agent", "After the agent".
- `v1-04-08.md`, Chapter 5 "Transitions" (rules 1 to 7, the factory's observation) and "The counters".
- `v1-04-08.md`, Chapter 7 "`run`: a stage is due" and "Shared helpers" (`ops.stall`).
- `v1-09-11.md`, Chapter 10 "What the factory posts" (stall causes, the cost table's columns).
- `v1-12-15.md`, Chapter 14 "Cost records" and the limits under "Changes made on measured grounds" (the bill).

**Proposed stories.**
- S0001 — Agent definitions, the task and the outcome schema. Keeps 1, 5, 9 (the Format check line), the approved test change recognised from data. 16 criteria.
- S0002 — Opening the work item's branch and its draft pull request. Keeps 2 (a branch per work item); initial state with the backlog file's own state fields dropped; only an open pull request reused. 16 criteria.
- S0003 — The stage starts with the pushed claim, then the agent run. Builds GH1.1; R19. 12 criteria.
- S0004 — Stalls. Builds GH2.5; keeps 14 (a stall costs an attempt), 12 (the stall note). 14 criteria.
- S0005 — After the agent: the branch, the undo, the entry, the form again. Keeps 5, 4; the entry's speaker and kind written by code. 14 criteria.
- S0006 — The decision rules: questions, rework rounds and caps. Keeps 10, 14 (rules 1 to 4 and 7). 14 criteria.
- S0007 — Checks, reports and the stage's result commit. Keeps 8 (rules 5 and 6: checks in order, the red tail, reports after green); the pushed result commit; labels as a projection. 14 criteria.
- S0008 — Cost records at agent run start and end. Builds GH4.1, GH4.2, R24; keeps 20. 12 criteria.
- S0009 — Bills from the cost records. Builds SI1.2, GH4.5, SI1.4 (a search test); keeps 20 (the cost table and the cost line). 14 criteria.

### F0006-reading-the-remote: Reading the remote

**Goal.** Every tick fetches first, reads every work item from the remote-tracking refs only, evaluates the four tiers into one event, and hands it to its handler through a dispatcher that counts errors per event and remote state and reports at the cap. The local checkout follows the remote and is disposable. Done when a hand push, a rejected push, a failed fetch, a fresh clone and every merge method are handled as the remote says, and the watcher's command line has no `--follow`.

**Scope.**
- Reading work items (R18): in-progress stories listed from the main branch on the remote, state from the work item's remote branch, never a local branch (GH5.1); merged branches absent; plain id order; a started story without a branch is at the first stage with initial counters, whatever its file says (ST6.1).
- The evaluation: the four tiers, waiting work items holding back new work, at most one pull request lookup, the claim tier through F0004's service (own claim, held, expired), the attempts-cap question, `run`, idle; two work items with one id; a work item of v1's format found is a repository stop naming it (R26).
- The dispatcher and the tick status (R28): every event kind has a handler or raises as a counted error (SI2.4); errors counted per event and the work item's remote state; the cap reported once; a push to the work item's remote branch retries (GH5.4).
- The tick: fetch first, a failed fetch (an expired token included) a repository stop (GH5.3); load and validate the pipeline definition; the local checkout reset to the remote; after a rejected push the remote's state evaluated, with at most one report (GH5.2); a fresh clone continues every work item (GH5.5); the local run record and lock change nothing (GH1.5).
- The move rule: an illegal stage change judged after the pull request's state is read, so no merge method is misread (ST2.3); the factory's own stage changes legal under the pipeline definition (ST2.4).
- The command line: evaluate once, the board of features and work items; no `--follow` (SI3.1) and no `factory-last-line` file (SI3.2).

**Out of scope.**
- The handlers of the human's acts (comments, questions, merge, close, `reject`, hand-over): F0007.
- The crash and expiry handlers: F0008.
- The acceptance's derivation and its column on the board: F0009.
- The preflight and its place after the fetch: F0010 (ST4.2).
- The scheduler loop and its pauses: F0010.

**Kept things.** 2 (a story starts only by the human's move to in progress), 3 (the remote is the truth), 5 (the move rule), 12 (an unknown event raises; errors capped and reported), 14 (errors counted per event and state), 15 (id order; waiting outranks new work; one agent run), 16 (an idle tick costs a fetch and at most one lookup).

**Rules.** Implements R18, R26, R28; obeys R20 (recognition through the claim service), R2.

**Base behaviour rebuilt.**
- `v1-04-08.md`, Chapter 6: "The concept", "The rules, in order", "Reading the work items", "Reading the last change", "Reading the pull requests", "The command line".
- `v1-04-08.md`, Chapter 7 "The tick's memo" (what the tick status replaces and keeps).
- `v1-12-15.md`, Chapter 13 "Staying in step" and "Merges"; Chapter 14 "The tick".

**Proposed stories.**
- S0001 — Work items read from the remote-tracking refs. Builds GH5.1, ST6.1, R18; keeps 2, 3, 15 (order). 16 criteria.
- S0002 — The watcher's evaluation in four tiers. Builds R26; keeps 15, 16 (waiting outranks new work; at most one lookup), the claim tier through F0004. 18 criteria.
- S0003 — The dispatcher and the tick status. Builds SI2.4, GH5.4, R28; keeps 12, 14. 14 criteria.
- S0004 — The tick: fetch first, then the remote's state. Builds GH5.2, GH5.3, GH5.5, GH1.5; keeps 3. 18 criteria.
- S0005 — The move rule reads the pull request first. Builds ST2.3, ST2.4; keeps 5. 12 criteria.
- S0006 — The watcher's command line. Builds SI3.1, SI3.2; the board's rows for features and work items. 10 criteria.

### F0007-human-on-the-pull-request: The human on the pull request

**Goal.** The pull request is the work item's face. The human's comments are copied into the journal by their ids, and the human's comment or close is committed and pushed into the work item before the factory posts, reopens or checks out. Questions are recorded, then posted; an answer unblocks; a merge archives with the bill; a close discards before the approval and sends back at it; an illegal stage change is moved back; the hand-over at the approval is assembled by code and retried from state. Every comment event is bounded by the error cap. Done when each handler keeps the human's act through a kill or a failure, and none repeats a post.

**Scope.**
- Comments by id (GH3.1, GH3.2, R22, R34): new comments without the marker become dated human entries; the ids read kept in the front matter; recorded and pushed before any effect.
- Questions in two steps: a recorded question posted, the attempts-cap question, the round-cap question.
- Merge: the story archived to the done folder at whatever stage, its done entry with the bill, its branch deleted.
- Discard: a close before the approval returns the story to the backlog with the human's text unchanged, its branch deleted; started again, its bill is empty (GH4.3).
- Send-back at the approval (GH3.3): the close recorded first; the pull request reopened as a draft; the reason taken as data; round + 1 within the smoke test's cap; else the send-back question with its three options.
- `reject` (GH3.5): the stage moved back, the correction note, the commit marked; a kill leaves the main branch clean.
- Answers and comment events (ST1.1): an answer unblocks, at the attempts cap resets attempts; a comment at the approval only recorded; comment events go through the error cap.
- Stops that cannot be done (ST3.1): `duplicate`, `error pr-lookup` and an `ask` without a pull request are counted errors.
- The hand-over (ST1.2, ST1.3): the description from fixed sections and the last entries of the tester, reviewer, documenter and smoke test, read by speaker as data; ready for review; the cost table posted; retried from the work item's state, reported at the error cap.
- The pull request's state read before every agent run: a close or a merge handled first.

**Out of scope.**
- The acceptance's merge, refusal and hand-over text: F0009.
- The crash-cap question and its answer: F0008.
- Counting comments by author (WE7, out of v1.1).
- A comment written while the stages work gets no new meaning (left for v2).

**Kept things.** 1 (code never interprets the human's free text), 2 (merge accepts; a discard returns the human's text), 3 (the human's acts recorded before the factory acts), 10 (recorded and committed, then posted), 11 (draft and ready say whose turn it is; one post per stop), 12 (handlers that cannot work are counted errors), 14 (question, error), 20 (the bill posted at the approval, written at the archive).

**Rules.** Implements R22, R28; obeys R10 (labels never read back), R15 (comment ids in the front matter), R34.

**Base behaviour rebuilt.**
- `v1-04-08.md`, Chapter 7: "`merged`", "`closed`", "`ask`", "`pr`", "`reject`", "`run`" (step 3) and the limits under "Shared helpers".
- `v1-04-08.md`, Chapter 8 "The hand-over".
- `v1-09-11.md`, Chapter 10: "The pull request's life", "What the factory posts", "A question and its answer".
- `v1-12-15.md`, Chapter 13 "Who commits where".

**Proposed stories.**
- S0001 — The human's comments copied by id. Builds GH3.1, GH3.2, R22, R34; keeps 3. 12 criteria.
- S0002 — Questions recorded, then posted. Keeps 10, 11 (the attempts-cap and round-cap questions). 12 criteria.
- S0003 — A merge archives the story with its bill. Keeps 2, 20. 12 criteria.
- S0004 — A close before the approval discards the story. Builds GH4.3; keeps 2 (the human's text unchanged). 10 criteria.
- S0005 — A close at the approval sends back, recorded first. Builds GH3.3; keeps 1 (the reason as data), 11 (three options that are existing paths). 16 criteria.
- S0006 — An illegal stage change moved back. Builds GH3.5. 10 criteria.
- S0007 — Answers unblock, and comment events are capped. Builds ST1.1; keeps 14. 12 criteria.
- S0008 — Stops that cannot be done are counted errors. Builds ST3.1, R28; keeps 12. 10 criteria.
- S0009 — The hand-over at the approval, retried from state. Builds ST1.2, ST1.3; keeps 11, 20 (the cost table). 16 criteria.
- S0010 — The pull request read before every agent run. Keeps the planner's "read before every agent run" (`v1-04-08.md`, Chapter 7). 8 criteria.

### F0008-crash-recovery: Crash recovery

**Goal.** A crash, the death of the tick or the container, discards the stage in flight and reruns it from its stage-start commit with no attempt charged, counting `crashes` against the crash cap, at which the human is asked. A restart with the same instance name reruns at its first look; another name waits until the lease has expired. Notes say "retrying" only when the next tick retries. Done when a kill during an agent run leaves no write of that run on any branch, the stage-start commit stays, the discarded cost records are gone, and the cap asks the human.

**Scope.**
- Crash discard and rerun (GH2.1, GH2.2, GH2.3, R23, R24): uncommitted work and unpushed commits of the stage thrown away; the stage rerun from its stage-start commit; attempts unchanged, `crashes` + 1; the started entry kept, the discarded cost records gone.
- First look (GH1.3): same name reruns without waiting out the lease or a pause; another name waits until expiry.
- The crash cap (GH2.4): the human asked on the pull request; no rerun until answered; the counter reset when the stage moves forward.
- An expired lease of another instance, and the notes (ST1.4): the stall note and the expiry note say "retrying" only where the next tick retries.

**Out of scope.**
- The kill-point tests across all five kill points: F0011 (WE1.1).
- A stall, which costs an attempt: F0005 (GH2.5).
- A second-instance test (dropped, R2).

**Kept things.** 13 (recover by construction), 14 (the crash, a fifth way not to move forward).

**Rules.** Implements R23, R24 (discarded records); obeys R18, R20, R21.

**Base behaviour rebuilt.**
- `v1-04-08.md`, Chapter 7 "`expired`: an agent run died" (what the crash and the expiry replace) and Chapter 6 "The run record".
- `v1-12-15.md`, Chapter 14 "The entrypoint" (start time, `docker stop`), "The tick" (step 4, the recovery of a dirty tree, which v1.1 replaces), "Machine state".
- `v1-09-11.md`, Chapter 10 "A question and its answer" (the "Retrying" limit).

**Proposed stories.**
- S0001 — A crash discards the stage and reruns it free. Builds GH2.1, GH2.2, GH2.3, GH1.3, R23, R24; keeps 13. 18 criteria.
- S0002 — The crash cap asks the human. Builds GH2.4; keeps 14. 10 criteria.
- S0003 — An expired lease, and notes that say "retrying" only when true. Builds ST1.4. 10 criteria.

### F0009-feature-acceptance: Feature acceptance

**Goal.** When a feature is complete, its acceptance becomes due and runs as a work item with one agent stage, the acceptance reviewer's, and one approval; the human's merge or close decides the result. Done when due counts story files only, the acceptance sorts after its stories for any slug, its cost line counts only its own records, and a merge before the approval or a repeated acceptance is decided without a loop.

**Scope.**
- Due (ST6.2, ST6.3): complete when there is an archived story and no story file in the backlog or in progress; due when no report at done covers exactly the archived stories; the derived states (in flight, merged and not yet recorded); the order after the feature's stories; the board's acceptance column.
- The acceptance stage: the acceptance branch with the report's head (state, `stories`, the title from the feature file); the acceptance reviewer's facts (archived stories, next free story number, the stories' cost from records); its write paths (its report and new backlog stories of its feature); its own cost line (GH4.4).
- At the approval: the description (recommendation, findings, proposed stories, closing text); a merge books `accepted` and brings the proposed stories; a close books `refused` with the human's reason first under the recommendation and drops the proposed stories.
- Merged before its approval (ST2.1, R31) and repeated acceptances (ST2.2).

**Out of scope.**
- Validating the report and the proposed stories (left for v2, L12, L47).
- A stopping rule for follow-up stories, parked backlog stories (left for v2, L44, L46).
- The acceptance reviewer's instructions: F0010 (shipped agents).

**Kept things.** 2 (proposed stories only as backlog; only the human starts them), 19 (the feature acceptance), 20 (each acceptance costed).

**Rules.** Implements R31; obeys R15, R22, R24.

**Base behaviour rebuilt.**
- `v1-09-11.md`, Chapter 11: "The concept", "Due, and the acceptor's task", "The eight items", "The report", "In the demonstration runs".
- `v1-04-08.md`, Chapter 6 "Reading the work items" (the acceptance's derivation); Chapter 4 "Where work items live" (the `.gitkeep`) and "Identifiers" (the sort limit); Chapter 5 "Names in the code" (the acceptance loop); Chapter 8 "The hand-over" (`ACCEPTANCE_CLOSING`).

**Proposed stories.**
- S0001 — When a feature acceptance is due. Builds ST6.2, ST6.3; keeps 19 (due rule), the board's column. 16 criteria.
- S0002 — The acceptance stage and the acceptance reviewer's facts. Builds GH4.4; keeps 19, 20. 16 criteria.
- S0003 — The acceptance at its approval: a merge accepts, a close refuses. Keeps 2, 19 (the result is the human's act). 14 criteria.
- S0004 — Merged before its approval, and repeated. Builds ST2.1, ST2.2, R31. 12 criteria.

### F0010-machine: The machine

**Goal.** One container runs one project: its repository URL and instance name come from environment variables, its checkout is one fixed path on a volume, recloned if missing. The image pins every tool. A preflight after the fetch checks the machine and probes the main branch, with a stamp keyed to the image build. The machine's own stops make the health check fail. Agent files hold only keys the runtime applies. No agent run holds a credential for the hosting service. Done when each of these is shown by a test, and the parts that need Docker, root or a second OS user by a static test of the files plus a morning observation.

**Scope.**
- One instance, one project (ST7, R2, R25): settings from the environment, the fixed checkout path, the reclone, the loop with its pauses (15 seconds after activity, doubling to 120 while idle).
- The pinned image (ST5.1, ST5.2, R29, R4): base by digest, Claude Code and tool packages by exact version, the factory installed from the lock file; the image's identity in each cost record (ST5.4); no `tasks/.gitkeep` in the template (SI3.3).
- The health check (ST3.3): failing after a failed preflight, a dirty main branch, an invalid pipeline definition, a repository the entrypoint waits for; compose with a restart policy and a health check.
- The preflight's items: tools, identity, the hosting service reachable, the agents where `FACTORY_CLAUDE_HOME` points (ST4.4), the agent runtime's version against the pinned one (ST5.3); every item reported at once.
- The probe and stamp (ST4.1, ST4.2, ST4.3, ST4.5): lint probed on the main branch or a clean worktree of it, after the fetch, stamp keyed to the image build, a failing main branch a reported stop.
- Agent files (SI4, R30): a key the runner does not apply refused at load, naming it, as a reported stop; the shipped agents, skills and settings in the glossary's names, each key with an effect.
- Credentials (WE3, R33): agent runs as a second unprivileged OS user, the token file readable only by the factory's user, the agent's environment scrubbed, the factory's own pushes and posts unaffected.

**Out of scope.**
- A watchdog for a dead container (stays in v1's backlog; R27).
- Preflight checks of the project's setup, the hosting settings and the token's expiry (WE10, out).
- A sandbox for agent runs (left for v2).
- The stop table: F0011 (ST3.5).

**Kept things.** 6 (each role's boundary in its shipped agent file), 8 (a missing tool is reported, never worked around), 15 (one instance, one project), 16 (the pause follows activity), 18 (the machine and its preflight).

**Rules.** Implements R2, R25, R27 (the container side), R29, R30 (agent files), R33; obeys R4, R12.

**Base behaviour rebuilt.**
- `v1-12-15.md`, Chapter 14: "The image and the container", "The entrypoint", "The tick", "The preflight", "Machine state", and the limits under "Changes made on measured grounds".
- `v1-12-15.md`, Chapter 15 "What an agent run can reach".
- `v1-09-11.md`, Chapter 9: "The seven agents", "The rules, R1 to R15", "The roles and their stages", "Permissions", "Installation".
- `v1-04-08.md`, Chapter 8, the limits under "The hand-over" (agent file keys with no effect).

**Proposed stories.**
- S0001 — One instance, one project, one checkout. Builds ST7.1, ST7.2, ST7.3, R2, R25; keeps 15, 16 (the pauses). 16 criteria.
- S0002 — The pinned image. Builds ST5.1 (a static test of the build files plus a morning observation of a real build), ST5.2, ST5.4, SI3.3, R29. 16 criteria.
- S0003 — The health check and the entrypoint's stops. Builds ST3.3 (a static test of the compose file and the health check command plus a morning observation of a running container), R27. 12 criteria.
- S0004 — The preflight's items. Builds ST5.3, ST4.4; keeps 8, 18. 16 criteria.
- S0005 — The probe on the main branch and a stamp keyed to the image. Builds ST4.1, ST4.2, ST4.3, ST4.5. 14 criteria.
- S0006 — Agent files with no dead keys, and the shipped agents. Builds SI4.1, SI4.2, SI4.3, R30; keeps 6. 16 criteria.
- S0007 — No hosting-service token in an agent run. Builds WE3.2, WE3.5, R33, and WE3.1, WE3.3, WE3.4 as a static test of the files and settings plus a morning observation (a second OS user, the token, a push and an API call from inside a real agent run). 18 criteria.

### F0011-proof-and-documents: Proof and documents

**Goal.** Recovery is proven by injection tests at each named kill point against a real local bare remote and the fake hosting client; each of v1's thirteen fault-injection paths is walked or mapped to the item that removed it; every stop is listed with its destination; and the four documents state what v1.1 does in the glossary's names. Done when every row of the three tables has its test, and the documents pass their checks.

**Scope.**
- Kill-point tests (WE1.1, R36): during an agent run (the tick dies; the agent run dies and the tick lives), between a commit and its push, between a post and its record, the tick, the container (a restart on an empty disk with the same instance name); each shows the crash or stall result of handover section 7.2.
- The thirteen fault-injection paths (WE1.2) from `planning/overnight/fault-paths.md`, each walked by a named test or mapped in a table to its removing item; `reject` walked by an injection test (WE1.3).
- The stop table (ST3.5): every stop of L11, L19, L26, L33, L55, L58, L64, L65 with its destination, each row a test.
- The four documents (WE6, R17): README, operator guide (install, configuration, the stops and what to do, from the stop table), project guide, decision log; none describes a replaced behaviour; glossary names; every story's docs criterion names the documents it touches (WE6.3).

**Out of scope.**
- The baseline run and its records: not tonight (WE1.4, WE5).
- Document errors not made wrong by v1.1 (L16, L36; handover section 8).

**Kept things.** 13 (recovery proven), 21 (the decision log; every run a fault-injection run, root causes recorded).

**Rules.** Implements R17, R36; obeys R3.

**Base behaviour rebuilt.**
- `v1-04-08.md`, Chapter 6, the limits under "The command line" (stops reaching only the factory log), and Chapter 7, the limits under "Shared helpers".
- `v1-12-15.md`, Chapter 14, the limits under "Changes made on measured grounds" (the machine's stops) and Chapter 12 "Reader documentation".
- The handover's section 7.2 (the kill-point table and its pass conditions).

**Proposed stories.**
- S0001 — Kill-point tests. Builds WE1.1, R36; keeps 13. 18 criteria.
- S0002 — The thirteen fault-injection paths, and `reject` walked. Builds WE1.2, WE1.3. 16 criteria.
- S0003 — The stop table. Builds ST3.5; keeps 12. 12 criteria.
- S0004 — The four documents. Builds WE6.1, WE6.2, WE6.3, WE6.4, WE6.5, R17; keeps 21. 12 criteria.

## Dependencies

How to read the rows: an item's need is met when the conditions of the needed item that its own conditions use are built in a lower feature, or earlier in the same feature. Where a later condition of the needed item is not used, the row says so. The plan reads its table the same way when it splits SI1 before GH4, settles ST3 and ST8, and puts ST2.3 before SI2.4.

| Item | Needs | Where the needs are built | Verdict |
|---|---|---|---|
| ST1 | GH3, GH5 | GH3.4 F0003-S0002; GH3.1, GH3.2 F0007-S0001; GH3.3 F0007-S0005; GH3.5 F0007-S0006; GH5 F0006 | Holds: ST1.1 is F0007-S0007, ST1.2 and ST1.3 are F0007-S0009, ST1.4 is F0008-S0003, all after every GH3 and GH5 condition. |
| ST2 | SI2 | SI2.1–SI2.3 F0001; SI2.4 F0006-S0003 | Holds: ST2.3 and ST2.4 are F0006-S0005; ST2.1 and ST2.2 are F0009-S0004. |
| ST3 | ST8 (they name each other) | ST8 F0003-S0004 | Holds, settled as the plan settles it. The stop service (ST3.2, ST3.4) comes first in F0003-S0001 and S0002 because ST8 needs it. ST3's own need of ST8 is ST3.3 (an invalid pipeline definition fails the health check), which is in F0010-S0003. ST3.1 (F0007) and ST3.5 (F0011) also come after ST8. |
| ST4 | ST5, ST3 | ST5.1, ST5.2, ST5.4 F0010-S0002; ST5.3 F0010-S0004; ST3.2, ST3.4 F0003; ST3.1 F0007; ST3.3 F0010-S0003 | Holds at condition level. ST4.4 is in F0010-S0004 with ST5.3, and ST4.1–ST4.3 and ST4.5 are in F0010-S0005, after both. ST3.5 (F0011) is the table of all stops, ST4.5's included, so it must come later; ST4 does not use it. |
| ST5 | GH4 | GH4.1, GH4.2 F0005-S0008; GH4.5 F0005-S0009; GH4.3 F0007; GH4.4 F0009 | Holds: F0010 is after all of them. |
| ST6 | nothing | — | Holds (ST6.1 F0006, ST6.2 and ST6.3 F0009). |
| ST7 | nothing | — | Holds (F0010). |
| ST8 | ST3 | ST3.2, ST3.4 F0003-S0001, S0002 | Holds: ST8 is F0003-S0004 and reports through the stop service. |
| SI1 | GH4 | GH4.1, GH4.2 F0005-S0008 | Holds as the plan splits it. SI1.1 and SI1.3 (F0002) need no cost record. SI1.2 and SI1.4 are F0005-S0009, after GH4.1 and GH4.2. |
| SI2 | nothing | — | Holds (F0001; SI2.4 F0006). |
| SI3 | nothing | — | Holds (SI3.1, SI3.2 F0006; SI3.3 F0010). |
| SI4 | ST5, ST8, ST3 | ST5 F0010-S0002, S0004; ST8 F0003-S0004; ST3.3 F0010-S0003 | Holds: SI4 is F0010-S0006. ST3.5 (F0011) lists SI4.3's stop and so comes after it. |
| GH1 | SI2 | SI2.1–SI2.3 F0001; SI2.4 F0006-S0003 | Holds at condition level. GH1.4 (F0003), GH1.2 (F0004) and GH1.1 (F0005) come after the one client and use no event dispatch. GH1.5 (F0006-S0004) and GH1.3 (F0008) come after SI2.4. |
| GH2 | GH1, WE2 | GH1.4 F0003; GH1.2 F0004-S0002; GH1.1 F0005-S0003; GH1.5 F0006-S0004; GH1.3 F0008-S0001; WE2 F0004-S0005 | Holds. GH2.5 (F0005-S0004) comes after GH1.1, GH1.2, GH1.4 and WE2, and uses neither restart rule. GH2.1–GH2.3 are built in F0008-S0001 together with GH1.3, and GH2.4 is in S0002. |
| GH3 | SI2 | SI2.1–SI2.3 F0001; SI2.4 F0006-S0003 | Holds at condition level. GH3.4 (F0003) uses only the client. GH3.1–GH3.3 and GH3.5 (F0007) come after all of SI2. |
| GH4 | GH1 | GH1.4 F0003; GH1.2 F0004; GH1.1 F0005-S0003; GH1.5 F0006; GH1.3 F0008 | Holds at condition level. GH4.1, GH4.2 and GH4.5 (F0005-S0008, S0009) use the stage-start commit and the stage's next commit (GH1.1, GH1.2). GH1.5 and GH1.3 concern the restart, which cost records do not use. GH4.3 (F0007) and GH4.4 (F0009) come after GH1.5. |
| GH5 | ST3, SI2 | ST3.2, ST3.4 F0003; ST3.1 F0007; ST3.3 F0010; ST3.5 F0011; SI2.1–SI2.3 F0001; SI2.4 F0006-S0003 | Holds at condition level, as the plan's own split (GH5 in feature 6, ST3.1, ST3.3 and ST3.5 later). GH5 reports through the stop service (ST3.2, ST3.4). GH5.1 (F0006-S0001) reads refs and uses no dispatch. GH5.4 is built with SI2.4 in F0006-S0003. GH5.2, GH5.3 and GH5.5 are in F0006-S0004. |
| WE1 | all GH items, ST2 | GH F0003–F0009; ST2 F0006, F0009 | Holds: F0011 is last. |
| WE2 | GH1 | Claim F0004-S0001; GH1.2 F0004-S0002 | Holds at condition level: WE2 (F0004-S0005) uses the stage-start commit. GH1.1, GH1.3 and GH1.5 come later and WE2 does not use them. |
| WE3 | nothing | — | Holds (F0010). |
| WE4 | R35 | Not tonight | Cannot hold tonight: it is a change in `factory-demo-todo` and needs R35's rewrite. |
| WE5 | GH4, WE1 | Not tonight | Cannot hold tonight: it needs the finished v1.1 and its end-to-end run. |
| WE6 | the items its documents describe | Every item before F0011-S0004 | Holds: WE6 is the last story. |

## Not tonight

- WE1.4: the baseline run is made on the shipped code. It needs the finished v1.1, run on `factory-demo-todo`.
- WE4.1, WE4.2, WE4.3: the `layers` check of the todo demo. These are changes in `factory-demo-todo`, another repository, and WE4.3 is recorded with the run's records (WE5).
- WE5.1, WE5.2, WE5.3, WE5.4, with R37: the run's summary, root-cause table and tag, committed at the end of the end-to-end run. They need the finished v1.1 and the run itself.
- R35's hand rewrite of run 4's eight stories, three feature acceptances and the todo demo's files into v1.1's formats. The formats exist only once v1.1's code does.
- Built tonight as a static test, observed only in the morning (they need Docker, root, a second OS user, a real image build or the real hosting service):
  - ST3.3: a running container's health check and restart policy.
  - ST5.1: a real image build with every pin.
  - WE3.1: a second OS user.
  - WE3.3: a real agent run trying to read the token file and the token.
  - WE3.4: a push and an API call from inside a real agent run against the real remote. The local bare remote of the tests needs no credential, so a push there would succeed. This one is added to the plan's list.
- Also observable only outside the container: the PyGithub client against the real API (SI2.2's real side) and a real restart (R36). The baseline run is the first to see them.

## Open questions

1. **Expiry of another instance's lease.** What does it cost when another instance's lease expires: is it a crash (free rerun, `crashes` + 1) or a stall (an attempt)? And what note does it post, if any? The handover says only that another name "waits for the lease to expire" (R20), and ST1.4 speaks of "a note of an expiry". The proposal is a crash, because its holder is gone (R23), with a note under ST1.4's rule. Related: does a crash of one's own post a note at all? Section 7.2 lists none. F0008-S0003 depends on the answer.
2. **The run record and the lock.** Does v1.1 keep a local run record and a tick lock at all? R20 calls them a cache that nothing depends on. GH1.5 (F0006-S0004) needs to know whether to test real files or v1's leftovers. With one process per instance (R2), a lock seems unneeded.
3. **A dirty main branch.** ST3.3 lists "a dirty main branch" as a repository stop. R18 and GH2, however, make local state disposable, and leftovers of a crash are discarded. Does the tick discard leftovers on the main branch (then the stop never arises), or stop on them?
4. **Keyed posts or state first.** GH3 allows both: every post is written into state first, or it carries a key that makes a repeat a no-op. F0003-S0002 builds the stop service on one of them. The interface sheet should fix which, and where the key lives (marker text, or comment ids in the front matter).
5. **Spellings.** What are the exact v1.1 spellings of the lifecycle folders (backlog, in progress, done), the branch prefixes, the story headings (description, smoke test, journal), the journal entry's prefix (section 6, question 2), the state keys and the stage keys? The glossary gives the words, not the spellings. The interface sheet should fix them before F0002 is drafted.
6. **The lease clock** (section 6, question 4): F0004-S0002 needs it from the interface sheet.
7. **Write paths for the factory's other product paths.** Which role's write paths in `factory-rf/factory/stages.yml` cover `image/`, `template/` and `claude/`? F0010-S0002, S0003, S0006 and S0007 write there. Are the shipped agents, stage skills and settings rewritten into the glossary's names by F0010-S0006, or copied by the seed?
8. **Order of the stage-start commit.** Does the stage-start commit come before or after the preparation (opening the branch, merging the main branch)? The undo's baseline must come after every preparation step (`v1-04-08.md`, Chapter 8 "The concept"). If the stage-start commit is the baseline, it must be the last commit before the agent run. Is the opening commit of the first stage the same commit as its stage-start commit?
9. **WE6.3.** Is WE6.3 a test that reads every story under `factory/features/` (v1's format, in this repository), or a traceability observation of the cross-feature check? It is placed in F0011-S0004 for now.
10. **The PyGithub client's tests.** Can it be tested against stand-ins of PyGithub's objects (no network)? The rule "never mock the code under test" allows it, but no real API call is seen before the baseline run.
11. **R26's detection.** What marks a v1 work item that v1.1 refuses (F0006-S0002)? A file in v1's `ongoing/` folder, v1's state keys such as `comments_seen`, or both?
12. **Reading the dependency table by condition.** Please confirm the condition-level reading of seven rows (ST4, GH1, GH3, GH4, GH5, WE2, and SI1 as the plan's own). Without it, ST3.5 and SI2.4 would have to move before items that they document or that do not use them, which the order cannot satisfy for ST3.5.
13. **The size of F0001.** It has eight stories. If "small enough to be built first tonight" means fewer, the `claude -p` implementation (F0001-S0008) can move to F0010 without breaking a dependency, since F0005 to F0009 test against the fake.
14. **Tick status across a restart.** v1 deleted the memo at every start. ST1.1 ("further ticks on the same state post nothing") holds across a restart only if the report at the cap is keyed (question 4). Should the tick status itself also be kept?
15. **The hand-over's event.** The hand-over is retried from state (F0007-S0009), which adds an event to F0006's evaluation. Is a field in the front matter (for example, the hand-over done) the state it is keyed to? R15 lists no such field.
16. **Docker, root and a second user inside v1's container** (the plan: "check on the PC"). If they are available, ST3.3, WE3.1, WE3.3 and WE3.4 can be real tests instead of morning observations.

## Sources

- Feature list, starting order and splits: `factory-v2/planning/v1.1/overnight-run-plan.md`, section 5, "Serial work", item 1 (both tables and the SI1 paragraph).
- Ids, slugs starting with a letter, and topological numbering: plan section 5, item 1, and item 3 "Identifier allocation"; the brief's rules.
- Condition-level reading of dependencies: plan section 5, the paragraph after the starting order (SI1 split; ST8 ahead of ST3; SI4 after ST5); the plan's own placement of ST2.3, ST2.4 (feature 6) before SI2.4 (feature 7).
- New feature F0008 (crash recovery), and GH1.1 and GH2.5 to F0005: handover section 5, GH2.1–GH2.5 (an agent run killed, the cap asking the human), GH1.1 (no agent run before the push), GH1.3 (rerun at its first look); section 7.2 (crash and stall tests).
- Guard, undo and restore in F0004: handover WE2.1–WE2.3 (the guard and the undo read the stage-start commit), and the plan's feature 4 carrying WE2.
- GH1.4 in F0003: handover GH1.4 refers to ST8.5; R21.
- GH1.5 in F0006: handover GH1.5 ("what the next tick does").
- GH3.4 in F0003: the brief's rule that a replaced mechanism is built the v1.1 way from the start; handover GH3 v1.1 behaviour ("every post is written into state first or carries a key").
- Dispatcher, tick status and SI2.4 in F0006: handover GH5.4 (the retry keyed to the remote branch), SI2.4, R28; `v1-04-08.md`, Chapter 7 "The tick's memo".
- GH4.3 in F0007: handover GH4.3 (a story discarded and started again); the discard is `v1-04-08.md`, Chapter 7 "`closed`" (`_discard`).
- ST1.4 in F0008: handover ST1.4 ("a note of a stall or an expiry"); the plan's dependency row ST1 | GH3, GH5.
- ST6.1 in F0006, R26 in F0006: handover ST6 v1.1 behaviour ("on start the factory sets the story's stage and counters itself"); R26.
- The machine's conditions as static tests plus morning observations: plan section 5, "From the 23 changes to criteria", third bullet; handover WE3.4 for the added case.
- Not tonight: plan section 5, "What v1 cannot build tonight"; handover R35, R37, WE4, WE5.
- Kept things per feature: handover section 3; `factory-v2/planning/01-discovery/kept-from-v1.md`, each kept thing's "What v2 must preserve".
- Rules per feature: handover section 4; `factory-rf/CLAUDE.md`, "Architecture" (layers, wrappers, interfaces, DTOs, file formats).
- v1's base behaviour per feature: `factory-v2/planning/01-discovery/v1-04-08.md`, `v1-09-11.md`, `v1-12-15.md`, the sections named in each feature.
- Out-of-scope items left for v2 or excluded: handover section 8.
- Names: handover section 2 "Names" and the appendix.
- Story sizes and the 26-criteria ceiling: plan section 5, "From the 23 changes to criteria", last bullet; the brief.
