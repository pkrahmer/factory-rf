# Traceability

The acceptance conditions, kept things and rules of the v1.1 handover traced to the stories of the overnight run, round 1. Written with `cross-check-1.md`, whose findings are cited by number. Counts: 96 conditions; 87 traced to a building story (of them, 5 are a static test tonight plus a morning observation: ST3.3, ST5.1, WE3.1, WE3.3, WE3.4); 1 observation only (WE6.3); 8 not tonight (WE1.4, WE4.1 to WE4.3, WE5.1 to WE5.4). Criterion numbers are written c<n>.

## Conditions

One row per acceptance condition of handover section 5. "Traced to" gives the story that builds the condition and its criterion numbers (c). Where a condition is split by part, the first story completes it and the others are named with their part; no part is built twice except where cross-check-1 says so. A morning observation row also names the story whose static test covers what v1's container can check.

| Condition | Traced to | Status |
|---|---|---|
| ST1.1 | F0007-S0007 c13, 14, 15 | built |
| ST1.2 | F0007-S0009 c12, 13, 14 | built |
| ST1.3 | F0007-S0009 c18 | built |
| ST1.4 | F0008-S0003 c1, 2, 3, 4, 11, 13 (the expiry note and the stall note at both sides of their caps); F0005-S0004 c3, 4 (the stall note itself) | built |
| ST2.1 | F0009-S0006 c4, 8, 9, 10 | built |
| ST2.2 | F0009-S0006 c12, 13, 14 | built |
| ST2.3 | F0006-S0005 c15, 19, 20 | built |
| ST2.4 | F0006-S0005 c6, 7, 21 | built |
| ST3.1 | F0007-S0008 c4, 5, 6, 7 | built |
| ST3.2 | F0003-S0002 c3, 4, 5, 6, 7 | built |
| ST3.3 | F0010-S0003 c3, 4, 11 (static: compose file and health command); 6, 7, 9 (a repository the entrypoint waits for) | static test tonight; morning observation: a running container with its restart policy and health check (`docker compose ps`) |
| ST3.4 | F0003-S0001 c7, 8, 9, 14 (the factory log); F0010-S0003 c13 (the entrypoint script's lines) | built |
| ST3.5 | F0011-S0003 c1 to 14 | built |
| ST4.1 | F0010-S0005 c1, 2 | built |
| ST4.2 | F0010-S0005 c6, 7 | built |
| ST4.3 | F0010-S0005 c9, 10, 11 | built |
| ST4.4 | F0010-S0004 c8, 9 | built |
| ST4.5 | F0010-S0005 c2, 3 | built |
| ST5.1 | F0010-S0002 c1 to 7 (static check of the build files) | static test tonight; morning observation: a real image build with every pin; the base digest and the package versions are placeholders until the human replaces them |
| ST5.2 | F0010-S0002 c8, 9 | built |
| ST5.3 | F0010-S0004 c11, 12 | built |
| ST5.4 | F0010-S0002 c15, 16 | built |
| ST6.1 | F0005-S0002 c2, 3 (the opening writes the initial state); F0006-S0001 c9, 10 (the reader shows a started story without a branch at the first stage) | built |
| ST6.2 | F0009-S0002 c2, 3, 14 | built |
| ST6.3 | F0009-S0001 c8, 9 (the sort key itself is built by F0002-S0001 c8) | built |
| ST7.1 | F0010-S0001 c6, 9 | built |
| ST7.2 | F0010-S0001 c1, 2, 5, 6 | built |
| ST7.3 | F0010-S0001 c1, 14 | built |
| ST8.1 | F0003-S0004 c3, 4, 5, 6 (the reported stop at load); F0003-S0003 c6, 11 (the schema: defaults taken, missing keys refused); F0006-S0004 c5 (the tick does nothing else) | built |
| ST8.2 | F0003-S0005 c7, 20 | built |
| ST8.3 | F0003-S0005 c9, 20 (a role without write paths); F0003-S0004 c10 (an agent that is not installed) | built |
| ST8.4 | F0003-S0005 c2, 3, 4, 20 | built |
| ST8.5 | F0003-S0005 c13, 14, 15, 16, 17, 20 | built |
| SI1.1 | F0002-S0005 c14 (speaker and kind read from data); F0002-S0002 c7, 8 (the journal records as data) | built |
| SI1.2 | F0005-S0009 c11 | built |
| SI1.3 | F0002-S0004 c5, 7, 9, 13 | built |
| SI1.4 | F0005-S0009 c19 | built |
| SI2.1 | F0001-S0003 c18, 19 | built |
| SI2.2 | F0001-S0003 c16, 17 | built |
| SI2.3 | F0001-S0011 c17, 18 | built |
| SI2.4 | F0006-S0003 c7, 15 (end to end through the tick: F0006-S0004 c19) | built |
| SI3.1 | F0006-S0006 c16, 17 | built |
| SI3.2 | F0006-S0006 c18, 19 | built |
| SI3.3 | F0010-S0002 c17 | built |
| SI4.1 | F0010-S0006 c3, 4, 5 | built |
| SI4.2 | F0010-S0007 c4, 5, 6, 7, 8 | built |
| SI4.3 | F0010-S0006 c7, 8, 9 | built |
| GH1.1 | F0005-S0003 c1, 3, 4, 5 | built |
| GH1.2 | F0004-S0002 c14, 15 (one service, by search tests); F0004-S0001 c1, 5, 6 (name and start time in the stage-start commit) | built |
| GH1.3 | F0008-S0001 c11, 12 (the same name reruns at once); F0008-S0003 c6, 12 (another name waits for the lease, then reruns) | built |
| GH1.4 | F0003-S0005 c14, 16, 20 (refused at load); F0003-S0003 c6 (default of 60 minutes per role) | built |
| GH1.5 | F0006-S0004 c15, 16 | built |
| GH2.1 | F0008-S0001 c1, 2, 11 | built |
| GH2.2 | F0008-S0001 c5 | built |
| GH2.3 | F0008-S0001 c3, 9 | built |
| GH2.4 | F0008-S0002 c2, 3, 4, 7, 15, 18 | built; the reset on a forward move (c18) belongs in F0005 and c15 repeats F0007-S0007 (cross-check-1 findings 2 and 5) |
| GH2.5 | F0005-S0004 c5, 6, 7, 8 (the stall service); F0005-S0005 c3, 6, 7 (the stage protocol applies it) | built |
| GH3.1 | F0007-S0001 c17 | built |
| GH3.2 | F0007-S0001 c18 | built |
| GH3.3 | F0007-S0005 c9, 10 | built |
| GH3.4 | F0003-S0002 c9, 12, 13 | built |
| GH3.5 | F0007-S0006 c9, 11 | built |
| GH4.1 | F0005-S0008 c1, 3, 4, 7, 10 | built |
| GH4.2 | F0005-S0008 c5, 11, 13 (the record); F0005-S0009 c2, 3 (the bill) | built |
| GH4.3 | F0007-S0004 c6 | built |
| GH4.4 | F0009-S0003 c21 (tested again for repeated acceptances in F0009-S0006 c16) | built |
| GH4.5 | F0005-S0009 c13 | built |
| GH5.1 | F0006-S0001 c7 | built |
| GH5.2 | F0006-S0004 c9, 10 | built |
| GH5.3 | F0006-S0004 c2, 3, 4 | built |
| GH5.4 | F0006-S0003 c14 (through the tick: F0006-S0004 c11) | built |
| GH5.5 | F0006-S0004 c12 | built |
| WE1.1 | F0011-S0001 c1, 5 to 13, 16 to 20 | built |
| WE1.2 | F0011-S0002 c1 to 18 | built |
| WE1.3 | F0011-S0002 c10, 11 | built |
| WE1.4 | — | not tonight: the baseline run on the shipped code needs the finished v1.1, run on `factory-demo-todo` (plan section 5) |
| WE2.1 | F0004-S0005 c13 (the undo); F0004-S0004 c14 (the guard); F0004-S0003 c14, 15 (the source at the stage-start commit) | built |
| WE2.2 | F0004-S0005 c14 | built |
| WE2.3 | F0004-S0005 c15 | built |
| WE3.1 | F0010-S0009 c4, 13 (static: the sudo call, the uids); F0010-S0008 c16 (the secret's owner and mode) | static test tonight; morning observation: a second OS user in a real container |
| WE3.2 | F0010-S0008 c2, 3, 4, 5, 6 | built |
| WE3.3 | F0010-S0008 c9, 10, 11, 13 (static: token file mode and owner; the helper refuses a reader without access) | static test tonight; morning observation: a real agent run tries to read the token file and the token |
| WE3.4 | F0010-S0008 c13, 15 (static: the helper, no stored credential); F0010-S0009 c4, 5 (the agent starts through `sudo -n -u agent -- env -i`) | static test tonight; morning observation: a push (`git -C . push origin main`) and an API call from inside a real agent run against the real remote |
| WE3.5 | F0010-S0008 c17 (see cross-check-1 finding 3: the local bare remote needs no credential) | built |
| WE4.1 | — | not tonight: a change in `factory-demo-todo`, another repository; WE4.3 is recorded with the run's records (WE5) |
| WE4.2 | — | not tonight: a change in `factory-demo-todo`, another repository; WE4.3 is recorded with the run's records (WE5) |
| WE4.3 | — | not tonight: a change in `factory-demo-todo`, another repository; WE4.3 is recorded with the run's records (WE5) |
| WE5.1 | — | not tonight: the run's summary, root-cause table and tag need the finished v1.1 and its end-to-end run (R37) |
| WE5.2 | — | not tonight: the run's summary, root-cause table and tag need the finished v1.1 and its end-to-end run (R37) |
| WE5.3 | — | not tonight: the run's summary, root-cause table and tag need the finished v1.1 and its end-to-end run (R37) |
| WE5.4 | — | not tonight: the run's summary, root-cause table and tag need the finished v1.1 and its end-to-end run (R37) |
| WE6.1 | F0011-S0004 c2, 14, 15, 19 | built |
| WE6.2 | F0011-S0004 c1, 4, 6, 7 (its rows come from F0011-S0003's STOP_TABLE) | built |
| WE6.3 | — | observation only: checked across the stories by the cross-feature check (skeleton-answers, answer 9); cross-check-1 found that all 76 stories end with a `docs:` criterion naming the documents it touches; F0011-S0004 builds no test for it |
| WE6.4 | F0011-S0004 c10, 12 | built |
| WE6.5 | F0011-S0004 c11 | built |

## Kept things and rules

One row per kept thing of handover section 3 and per rule of section 4: the stories that keep or obey it, taken from each story's Assignment and checked against its criteria, or "configuration in the seed" where `factory-rf`'s seed (its `CLAUDE.md`, `pyproject.toml`, `Makefile` and v1's `factory/stages.yml`) carries it rather than a story.

### Kept things (handover section 3)

| # | Kept thing | Kept by |
|---|---|---|
| 1 | Sort every step: human, model or code | F0005-S0001 (allowed decisions computed by code), F0005-S0005 (speaker and kind written by code), F0005-S0006 (code decides what a decision means), F0007-S0001 (comments copied, never interpreted), F0007-S0005 (the reason taken from data), F0009-S0005 (the refusal reason copied unchanged) |
| 2 | Nothing starts and nothing lands without the human | F0005-S0002 (a branch and a pull request per work item), F0006-S0001 (a story starts only by the human's move to `in-progress/`), F0007-S0003 (merge accepts), F0007-S0004 (discard returns the human's text), F0009-S0003 (proposed stories only as backlog files), F0009-S0005, F0009-S0006 (the human's merge decides) |
| 3 | Versioned files are the only truth (v1.1: the remote) | F0001-S0004, F0001-S0009 (remote-tracking refs), F0005-S0002, F0005-S0009 (bills read from the remote), F0006-S0001, F0006-S0004, F0007-S0001, F0007-S0005 (the human's act recorded first), F0009-S0002 |
| 4 | The work item is the memory | F0002-S0001, F0002-S0002, F0002-S0003, F0002-S0005, F0004-S0005 (state and journal restored), F0005-S0002, F0005-S0003, F0005-S0005, F0009-S0001 |
| 5 | Code enforces, instructions explain | F0001-S0010 (the undo's revert), F0002-S0006 (form validated), F0004-S0004 (the guard hook), F0004-S0005 (the undo), F0005-S0001, F0005-S0003, F0005-S0005 (form before and after), F0005-S0007 (same steps in the same order), F0006-S0005 (the pipeline definition decides legal moves), F0010-S0008 (agents do not push or call the hosting service). The instructions half is thin: F0010-S0007 ships no stage texts (cross-check-1 finding 20) |
| 6 | Whoever makes something does not judge it | F0010-S0007 (each role's boundary in its shipped agent file; the template pipeline definition), F0004-S0003 (write paths per role keep the coder out of the tests), F0005-S0001 (an approved test change recognised from data); the role order is configuration in the seed (`factory/stages.yml`) |
| 7 | The pipeline definition | F0003-S0003, F0003-S0004, F0003-S0005, F0006-S0005 (legal moves from the definition), F0010-S0007 (the template) |
| 8 | Believe what you observe | F0001-S0006 (exit status only), F0005-S0005, F0005-S0007 (green means the factory ran the check), F0010-S0004 (a missing tool is reported, never worked around) |
| 9 | Specify first, down to the edge cases | F0002-S0004, F0002-S0006 (the form check), F0002-S0008 (the command for the human), F0005-S0001 (the first stage gets the form's findings), F0005-S0005 (the form again after the run) |
| 10 | Ask, don't guess | F0001-S0007 (`question` always allowed), F0005-S0001, F0005-S0006 (a question always blocks), F0007-S0002 (recorded, then posted), F0007-S0005 (the send-back question), F0008-S0002 (the crash-cap question) |
| 11 | The human acts where they already are | F0001-S0002, F0001-S0003, F0001-S0011 (the marker), F0003-S0002 (one post per stop), F0005-S0004 (the stall note), F0006-S0003 (the error report), F0007-S0002, F0007-S0005, F0007-S0009 (draft and ready), F0009-S0004 |
| 12 | Loud over lucky | F0003-S0001, F0003-S0004, F0003-S0005, F0005-S0004, F0006-S0002 (a state without a handler becomes an event), F0006-S0003 (an unknown event raises; errors capped and reported), F0007-S0008, F0011-S0003 |
| 13 | Recover by construction (v1.1: discard and rerun) | F0001-S0001 (the seam), F0001-S0005, F0001-S0010, F0004-S0001, F0004-S0002, F0008-S0001, F0011-S0001, F0011-S0002 |
| 14 | When a story does not move forward (four ways, plus the crash) | F0005-S0004 (stall), F0005-S0006, F0005-S0007 (rework and question), F0006-S0003 (error), F0007-S0007, F0008-S0001, F0008-S0002, F0008-S0003 (crash) |
| 15 | Bounded work in flight, in the human's order | F0002-S0001 (plain id order), F0006-S0001, F0006-S0002 (waiting outranks new work; one agent run), F0010-S0001 (one instance, one project) |
| 16 | Spend on events, not on time | F0006-S0002 (at most one lookup), F0006-S0004 (an idle tick costs a fetch), F0010-S0001 (the pause follows activity), F0010-S0005 (no command on an idle tick) |
| 17 | The project owns how it is built | F0001-S0006 (project commands only), F0004-S0003, F0004-S0004, F0004-S0005 (protected paths outside every write path) |
| 18 | The machine | F0010-S0001, F0010-S0002, F0010-S0003, F0010-S0004, F0010-S0005 |
| 19 | The feature acceptance | F0009-S0001 to F0009-S0006 |
| 20 | Measure every agent run | F0001-S0007, F0001-S0008 (the result's measures), F0002-S0007 (the sidecar), F0005-S0008 (a record per run), F0005-S0009 (the bill), F0007-S0003 (written at the archive), F0007-S0009 (posted at the approval), F0009-S0003, F0009-S0004, F0009-S0005 (each acceptance costed) |
| 21 | Change by evidence, and write down why | F0011-S0002 (every run a fault-injection run), F0011-S0004 (the decision log); every story's docs criterion names `docs/decisions.md` where it decides something |

### Rules (handover section 4)

| Rule | Subject | Kept or obeyed by |
|---|---|---|
| R1 | One repository, built by v1 | configuration in the seed (`factory-rf`, v1's `factory/stages.yml`); the build itself |
| R2 | One instance, one project | F0010-S0001 (no list of repositories, ST7) |
| R3 | English, and the glossary's names | F0002-S0001 (folders and branch names); every story through the interface sheet's names; F0010-S0007 (agent bodies in the glossary's words); F0011-S0004 (the documents' word check, WE6.5) |
| R4 | Language and code standard | configuration in the seed (`pyproject.toml`, ruff, `mypy --strict`, `make check`); F0010-S0002 (pinned versions in the image) |
| R5 | Every command-line tool behind a wrapper class | F0001-S0004 (one module starts processes), F0001-S0003 (one module imports `github`), F0001-S0006 (one module names `make`), F0001-S0008 |
| R6 | Interfaces where stacks will differ | F0001-S0002, F0001-S0006, F0001-S0007 |
| R7 | DTOs shaped by the factory, Pydantic, no `dict[str, Any]` | F0001-S0002 (the search test), F0001-S0004, F0001-S0007, F0001-S0008, F0001-S0009; every story's DTOs |
| R8 | Layers belong to the project | F0001-S0006 (a generic check result); `factory-rf`'s own layers are configuration in the seed (import-linter in `make layers`) |
| R9 | Git and the hosting service | F0001-S0003, F0001-S0004, F0001-S0005, F0001-S0009, F0001-S0010 |
| R10 | The hosting service client | F0001-S0002, F0001-S0003, F0001-S0011; labels written, never read: F0005-S0007 |
| R11 | Project commands | F0001-S0006 |
| R12 | Agent runtime | F0001-S0007, F0001-S0008, F0004-S0004 (the hook), F0010-S0009 |
| R13 | File formats | F0002-S0003, F0002-S0007, F0003-S0003 (reader only; no story writes the pipeline definition), F0003-S0004 (agent files), F0009-S0001 |
| R14 | The interfaces are yours to draft | the interface sheet (`interfaces.md`) with F0001-S0002, F0001-S0004, F0001-S0006, F0001-S0007 |
| R15 | A work item's data | F0002-S0002, F0002-S0003, F0002-S0005, F0002-S0007 |
| R16 | The seed | configuration in the seed |
| R17 | Documents | F0011-S0004; every story's docs criterion |
| R18 | The remote is the only truth, and it is read | F0005-S0002, F0005-S0009, F0006-S0001, F0006-S0002, F0006-S0004, F0009-S0002 |
| R19 | Every stage boundary is a pushed commit | F0004-S0001, F0005-S0003, F0005-S0007 |
| R20 | The claim | F0004-S0001, F0004-S0002, F0006-S0002 (recognition through the claim service), F0008-S0001, F0008-S0003 |
| R21 | The lease | F0003-S0003 (default 60), F0003-S0005 (validated at load), F0004-S0001, F0004-S0002 |
| R22 | The human's acts are recorded before any effect | F0003-S0002, F0007-S0001, F0007-S0002, F0007-S0005, F0007-S0006, F0007-S0010, F0009-S0004, F0009-S0005 |
| R23 | Crash, stall, error | F0003-S0003 (crash cap default 2), F0005-S0004 (a stall), F0008-S0001, F0008-S0002, F0008-S0003 (the crash); see cross-check-1 findings 2 and 6 |
| R24 | Cost records | F0001-S0008, F0002-S0007, F0005-S0008, F0005-S0009 (unknown never summed as zero), F0008-S0001 (discarded with the stage) |
| R25 | Project and checkout | F0010-S0001, F0010-S0003 (the compose variables) |
| R26 | Start only on idle repositories | Dropped for v1.1 by decision 008 (factory-v2) and questionnaire 1, Q15: v1.1 starts fresh and recognises no v1 work item; F0002-S0003 still lists the keys it drops |
| R27 | Where stops go | F0003-S0001, F0003-S0002, F0010-S0003, F0011-S0003 |
| R28 | A handler that cannot do its work is a counted error | F0006-S0003, F0007-S0001, F0007-S0007, F0007-S0008 |
| R29 | A pinned machine | F0010-S0002, F0010-S0004 |
| R30 | The pipeline definition is validated at load | F0003-S0003, F0003-S0004, F0003-S0005, F0010-S0006, F0010-S0007 |
| R31 | A feature acceptance merged before its approval | F0009-S0006 (on F0009-S0005) |
| R32 | Write paths come from the stage-start commit | F0004-S0003, F0004-S0004, F0004-S0005 |
| R33 | No hosting service token in an agent run | F0010-S0008, F0010-S0009 |
| R34 | Comments counted by author is not in v1.1 | F0001-S0002 (the marker, not the author), F0007-S0001 |
| R35 | The end-to-end run uses `factory-demo-todo` | not tonight: the baseline run and the hand rewrite of run 4's stories need the finished v1.1 |
| R36 | Kill tests are injection only | F0001-S0001, F0001-S0005 (the push points), F0001-S0003, F0001-S0011 (`after-post`), F0001-S0007, F0001-S0008 (`agent-run`), F0011-S0001, F0011-S0002 |
| R37 | The run's records are committed in `factory-rf` | not tonight: WE5, after the end-to-end run |
| R38 | Small | obeyed by every story: each lies inside its feature's Scope and handover section 5; cross-check-1 found no story that builds an item of handover section 8 |

## Reverse index

Story → the conditions it covers, as traced above. "none" means the story builds no acceptance condition; what it keeps or obeys is in the section above.

| Story | Title | Conditions |
|---|---|---|
| F0001-S0001 | Kill points in the wrappers | none |
| F0001-S0002 | The hosting-service interface and its DTOs | none |
| F0001-S0003 | The PyGithub hosting client and its one error type | SI2.1, SI2.2 |
| F0001-S0004 | The git wrapper: process, fetch and refs | none |
| F0001-S0005 | The git wrapper: clone, checkout, commit and push | none |
| F0001-S0006 | The project-commands interface and the make class | none |
| F0001-S0007 | The agent-runtime interface, its DTOs and the fake | none |
| F0001-S0008 | The claude agent runtime | none |
| F0001-S0009 | The git wrapper: history and work tree | none |
| F0001-S0010 | The git wrapper: branches, merge, reset and revert | none |
| F0001-S0011 | The hosting-service fake | SI2.3 |
| F0002-S0001 | Identifiers, paths and order | none |
| F0002-S0002 | Work item state | SI1.1 |
| F0002-S0003 | Reading and writing work items | none |
| F0002-S0004 | Sections that respect code fences | SI1.3 |
| F0002-S0005 | Journal with speaker and kind as data | SI1.1 |
| F0002-S0006 | Story form check | none |
| F0002-S0007 | Cost record sidecar format | none |
| F0002-S0008 | The story check command | none |
| F0003-S0001 | Repository and machine stops: health status and time-stamped lines | ST3.4 |
| F0003-S0002 | Work item stops on the pull request, posted once | ST3.2, GH3.4 |
| F0003-S0003 | The pipeline definition schema and its defaults | ST8.1, GH1.4 |
| F0003-S0004 | Loading the pipeline definition: installed agents and a reported stop | ST8.1, ST8.3 |
| F0003-S0005 | Load-time rules of the pipeline definition | ST8.2, ST8.3, ST8.4, ST8.5, GH1.4 |
| F0004-S0001 | The stage-start commit is the claim | GH1.2 |
| F0004-S0002 | One service for claim, expiry and recognition | GH1.2 |
| F0004-S0003 | Write paths and protected paths read at the stage-start commit | WE2.1 |
| F0004-S0004 | The write-path guard hook | WE2.1 |
| F0004-S0005 | Undo and restore after an agent run | WE2.1, WE2.2, WE2.3 |
| F0005-S0001 | Agent definitions, the prompt and the allowed decisions | none |
| F0005-S0002 | Opening the work item's branch and its draft pull request | ST6.1 |
| F0005-S0003 | The stage starts with the pushed claim, then the agent run | GH1.1 |
| F0005-S0004 | Stalls | ST1.4, GH2.5 |
| F0005-S0005 | After the agent: the branch, the undo, the entry, the form again | GH2.5 |
| F0005-S0006 | The decision rules: questions, rework rounds and caps | none |
| F0005-S0007 | Checks, reports and the stage's result commit | none |
| F0005-S0008 | Cost records at agent run start and end | GH4.1, GH4.2 |
| F0005-S0009 | Bills from the cost records | SI1.2, SI1.4, GH4.2, GH4.5 |
| F0006-S0001 | Work items read from the remote-tracking refs | ST6.1, GH5.1 |
| F0006-S0002 | The watcher's evaluation in four tiers | none |
| F0006-S0003 | The dispatcher and the tick status | SI2.4, GH5.4 |
| F0006-S0004 | The tick: fetch first, then the remote's state | ST8.1, GH1.5, GH5.2, GH5.3, GH5.5 |
| F0006-S0005 | The move rule reads the pull request first | ST2.3, ST2.4 |
| F0006-S0006 | The watcher's command line | SI3.1, SI3.2 |
| F0007-S0001 | The human's comments copied by id | GH3.1, GH3.2 |
| F0007-S0002 | Questions recorded, then posted | none |
| F0007-S0003 | A merge archives the story with its bill | none |
| F0007-S0004 | A close before the approval discards the story | GH4.3 |
| F0007-S0005 | A close at the approval sends back, recorded first | GH3.3 |
| F0007-S0006 | An illegal stage change moved back | GH3.5 |
| F0007-S0007 | Answers unblock, and comment events are capped | ST1.1 |
| F0007-S0008 | Stops that cannot be done are counted errors | ST3.1 |
| F0007-S0009 | The hand-over at the approval, retried from state | ST1.2, ST1.3 |
| F0007-S0010 | The pull request read before every agent run | none |
| F0008-S0001 | A crash discards the stage and reruns it free | GH1.3, GH2.1, GH2.2, GH2.3 |
| F0008-S0002 | The crash cap asks the human | GH2.4 |
| F0008-S0003 | An expired lease, and notes that say retrying only when true | ST1.4, GH1.3 |
| F0009-S0001 | The acceptance report as data, and its place in the order | ST6.3 |
| F0009-S0002 | When a feature acceptance is due | ST6.2 |
| F0009-S0003 | The acceptance stage and the acceptance reviewer's facts | GH4.4 |
| F0009-S0004 | The hand-over at the acceptance's approval | none |
| F0009-S0005 | A merge accepts, a close refuses | none |
| F0009-S0006 | Merged before its approval, and repeated acceptances | ST2.1, ST2.2 |
| F0010-S0001 | One instance, one project, one checkout | ST7.1, ST7.2, ST7.3 |
| F0010-S0002 | The pinned image | ST5.1 (static part, morning observation), ST5.2, ST5.4, SI3.3 |
| F0010-S0003 | The health check and the entrypoint's stops | ST3.3 (static part, morning observation), ST3.4 |
| F0010-S0004 | The preflight's items | ST4.4, ST5.3 |
| F0010-S0005 | The probe on the main branch and a stamp keyed to the image | ST4.1, ST4.2, ST4.3, ST4.5 |
| F0010-S0006 | Agent files with no dead keys | SI4.1, SI4.3 |
| F0010-S0007 | The shipped agents and settings | SI4.2 |
| F0010-S0008 | No hosting-service token in an agent run | WE3.1 (static part, morning observation), WE3.2, WE3.3 (static part, morning observation), WE3.4 (static part, morning observation), WE3.5 |
| F0010-S0009 | Agent runs as a second unprivileged user | WE3.1 (static part, morning observation), WE3.4 (static part, morning observation) |
| F0011-S0001 | Kill-point tests | WE1.1 |
| F0011-S0002 | The thirteen fault-injection paths, and reject walked | WE1.2, WE1.3 |
| F0011-S0003 | The stop table | ST3.5 |
| F0011-S0004 | The four documents | WE6.1, WE6.2, WE6.4, WE6.5 |

## Sources

- The stories under `factory-rf/planning/overnight/stories/` (their Assignments and numbered criteria).
- `factory-v2/planning/v1.1/handover.md`, sections 3, 4 and 5, 8.
- `factory-v2/planning/v1.1/overnight-run-plan.md`, section 5, "Traceability" and "What v1 cannot build tonight".
- `factory-rf/planning/overnight/skeleton.md` ("Not tonight"), `skeleton-answers.md` (answers 9, 10 and 16).
