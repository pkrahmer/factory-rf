# Questionnaire 1: the working answers and the interface sheet

## How to use

During and after the overnight run of 2026-10-12/13, the main session answered the skeleton's open questions, the interface sheet's open questions, the drafters' questions, F0001's rounds 1 and 2 and the blockers of cross-check round 1, all on the human's behalf (`planning/overnight/skeleton-answers.md`). F0001's acceptances also left open points for the human (`factory/features/F0001-boundaries/ACCEPTANCE.md`, sections 4 to 6). This questionnaire lets the human confirm or change each of them that is a real choice and still shapes F0002 to F0011. Decisions 001 to 007, F0001's decisions 20 to 23, `CLAUDE.md` and checked facts are not asked again; they are listed under "Settled, not asked".

1. The session asks round 1 in its batches, in order, with AskUserQuestion: up to four questions per batch, using each question's header, question and options as given. In every question the first option is the recommendation, and "other" is always open. Round 1's answers do not depend on one another.
2. It records each answer under "Answers" with the date, and names the stories to edit from the question's "If changed" line when the answer is not the working answer.
3. It then asks round 2. Each question there names the round-1 question it waits for and says what to ask for each possible earlier answer.

Two recommendations differ from the working answer: Q3 (drop the run record) and Q18 (no preflight item for the git identity). Each gives its reason in the explanation. Q22, Q23, Q27 and Q29 had no working answer; their recommendation is this file's.

## Round 1: independent questions

Twenty-seven questions in seven batches, grouped by theme: lease and crashes (Q1 to Q5), posts and the hosting service (Q6 to Q10), files and names (Q11 to Q16), git and agents (Q17 to Q24), F0001 leftovers (Q25 to Q27).

### Batch 1: lease and crashes

#### Q1: Another instance's expired lease, and which crashes post a note

- Header: `Expiry`
- Source: skeleton answer 1.

When a claim's lease runs out and the claim names another instance, the next tick must decide what that costs and what it tells the human. The working answer treats it as a crash: the stage reruns from its stage-start commit, no attempt is charged and `crashes` rises by one. It also posts a note on the pull request that says "retrying" only when the rerun will happen, and that asks the human instead at the crash cap (ST1.4). A crash of the instance's own name posts no note and only adds a journal entry naming the rerun's stage-start commit. Under R2 another name appears only when an instance is renamed, so the case is rare, but GH1.3 tests it.

**Question.** How is another instance's expired lease charged, and which crashes post a note?

**Options**
- **A. Crash; note on expiry only (Recommended).** A free rerun, as R23 makes a dead holder a crash; the human hears of a foreign expiry, not of every own restart. Con: an own crash shows only in the journal.
- **B. Crash; every crash posts.** The same charge, and an own crash also posts a note. Pro: every restart is visible on the pull request. Con: one more post per restart, with nothing for the human to do.
- **C. Stall; costs an attempt.** Con: charges the work item for a death it did not cause (v1's L5), and counts it against the attempts cap instead of the crash cap.

**If changed:** F0008-S0001, F0008-S0003, F0006-S0002 (the `expired` event), F0002-S0005 (journal kinds `crash` and `expiry`), the post texts of F0003-S0002, F0011-S0001, F0011-S0002.

#### Q2: Where the stage-start commit sits

- Header: `Start commit`
- Source: skeleton answer 8; cross-check round 1, note 22.

The undo and the restore take the stage-start commit as their baseline. The working answer therefore makes it the last commit before the agent run, after opening the branch and merging the main branch, and for a first stage the commit that opens the branch is also its stage-start commit (F0005-S0002 drafts it so). F0009-S0003 departs for the feature acceptance: its opening commit pushes only the report's head, and the claim comes on the next tick, when the acceptance is an ordinary work item at its first stage. That costs one more commit and one tick per acceptance and keeps the opening outside the stage protocol.

**Question.** Is the stage-start commit the last commit before the agent run, with a first stage's opening commit as its claim?

**Options**
- **A. Yes; acceptance opens apart (Recommended).** The working answer, with F0009's separate opening kept: the acceptance then runs as an ordinary work item. Con: two rules for a work item's first commit.
- **B. Yes; acceptance aligned too.** F0009's opening commit becomes its claim, as for a story. Pro: one rule. Con: F0009-S0003 merges the opening into the stage protocol, a larger story.
- **C. Separate opening commit always.** Every first stage opens its branch in one commit and claims it in the next. Pro: one rule and a simple opening. Con: one more commit per story.

**If changed:** F0004-S0001, F0005-S0002, F0005-S0003, F0009-S0003, F0011-S0002 (fault-injection path 12).

#### Q3: Does v1.1 keep a local run record?

- Header: `Run record`
- Source: skeleton answer 2.

R20 and decision 001 make the local run record a cache that nothing depends on. The working answer keeps it only for the board's "running since" and keeps no tick lock: F0005-S0003 writes and clears a `RunRecord` file around every agent run, which adds a `RunRecordStore` interface, a JSON adapter and a `Boundaries` field, and F0006-S0004 tests GH1.5 against it. This file recommends dropping it, against the working answer. The claim in the work item's front matter already carries `started_at` on the remote and the board already shows the claim (F0006-S0006); a time read from the remote is right on any machine, while the file is right only on the machine that runs the stage. GH1.5 then tests that the tick reads and writes no run record and no lock, v1's leftover files included.

**Question.** Does v1.1 keep a local run record at all?

**Options**
- **A. Drop it; board reads claim (Recommended).** One interface, one adapter, one field and about six criteria less, and one truth. Con: the board shows the claim's start, seconds before the agent run starts, and keeps showing it during the checks.
- **B. Keep it as a cache.** The working answer: the board shows exactly while an agent runs. Con: a second, local source for a fact the remote already holds.
- **C. Keep record and lock.** v1's shape, both as caches. Con: with one process per instance (R2) the lock protects nothing.

**If changed:** the working answer is B. For A: F0005-S0003 (its Interface, c4, c13 to c16 and the docs criterion), F0006-S0004 (c15, c16), F0006-S0006 (`running_since`), the `boundaries` fixture as F0003-S0001, F0004-S0001, S0003, S0005, F0006-S0003, F0008-S0001 to S0003 and F0011-S0001 use it, and the sheet's run-record rows. For C: F0005-S0003, F0006-S0004.

#### Q4: A dirty checkout at the start of a tick

- Header: `Dirty main`
- Source: skeleton answer 3.

ST3.3 lists "a dirty main branch" as a repository stop, but R18 makes machine state disposable and GH2 discards a crashed stage's leftovers. The working answer restores the checkout to the remote-tracking refs at the start of every tick, discards uncommitted changes and writes one time-stamped line naming what it discarded. ST3.3's stop is then the case where that restore fails (`checkout_restore_failed`), which fails the health check. F0006-S0004 builds the restore and F0010-S0003 the health check.

**Question.** Does the tick discard leftovers in its checkout and stop only when the restore fails?

**Options**
- **A. Discard, stop on failure (Recommended).** Follows R18 and GH2: nothing local is worth keeping, and the line says what went. Con: a hand edit in the container's checkout is lost.
- **B. Stop on any leftovers.** ST3.3 read literally; the human cleans up. Con: every crash's leftovers stop the repository until someone acts, against GH1.3's rerun at the first look.
- **C. Keep on a local branch.** Leftovers committed to a local rescue branch, then the restore. Con: a branch kind of its own, on a disk R18 calls disposable.

**If changed:** F0006-S0004, F0010-S0003, F0011-S0003, F0003-S0001 (the stop kinds).

### Batch 2: lease and crashes; posts and the hosting service

#### Q5: The four kill points

- Header: `Kill points`
- Source: interface sheet answer 11.

The handover's section 7.2 has six rows over five kill points: during an agent run (once as a crash, once as a stall), between a commit and its push, between a post and its record, the tick at any other point, and the container. F0001-S0001 built four named points, `agent-run`, `before-push`, `after-post` and `after-push`, as the sheet proposed. "The tick at any other point" is `after-push` armed with a count, and the container is a restart on an empty disk with the same instance name, which needs no point. The fault-path table's open question 3 (does a crash between two stages raise `crashes`, and on which stage) stays with F0008-S0001.

**Question.** Do the four built kill points stand for all of section 7.2's rows?

**Options**
- **A. Four points (Recommended).** Built and accepted; F0011-S0001 maps each row onto them. Con: "any other point" means any point where a push happens, not any line of code.
- **B. Add tick and container.** A named point for every row. Pro: one name per row of 7.2. Con: a new F0001 story and seam code for cases the two existing mechanisms already reach.

**If changed:** a new F0001 story; F0008-S0001, F0011-S0001, F0011-S0002, `planning/overnight/fault-paths.md`.

#### Q6: Posts made idempotent by a key

- Header: `Keyed posts`
- Source: skeleton answer 4.

GH3 allows two ways to keep a post from repeating after a kill: write it into state first, or give it a key that makes a repeat a no-op. The working answer keys every post with `<!-- factory key=<work item id>:<kind>:<n> -->` after the marker, derived from state on the remote; before posting, the hosting client lists the pull request's comments and posts nothing when that key is there. F0001 built `PostKey` and the `already_posted` outcome, and F0003-S0002's stop service and the handlers of F0007 and F0008 rest on it, as do the tests of GH3.4 and ST1.1. Reading comments is the human's channel, not state read back as truth (R22).

**Question.** Is every post made idempotent by a key in the post, checked before posting?

**Options**
- **A. Key in the post (Recommended).** Built; state and post may then be written in either order. Con: one comment listing per post.
- **B. State first, then post.** Each post recorded in the front matter before it is made. Con: a kill between the post and its record still double-posts unless a key is added; one more commit and push per post.
- **C. Both.** Recorded and keyed. Con: B's cost, for no case that A misses.

**If changed:** F0003-S0002, F0005-S0004, F0006-S0003, F0007-S0002, S0006, S0008, S0009, F0008-S0002, S0003, F0009-S0004, F0011-S0003; round 2's Q28 changes.

#### Q7: The state the hand-over is retried from

- Header: `Hand-over`
- Source: skeleton answer 15.

The hand-over at the approval (the description, ready for review, the cost table) must be retried from the work item's state until it completes (ST1.2, ST1.3), so the watcher needs a fact that says whether it completed. R15's list of state fields has none for it. The working answer adds the front matter field `handed_over`, the stage whose hand-over completed: the watcher raises a `hand_over` event while `stage` differs from it, and the hand-over writes it when it is done.

**Question.** Is the hand-over's completion kept in a new front matter field, `handed_over`?

**Options**
- **A. A handed_over field (Recommended).** One field, read as data with one comparison; thirteen drafts already use it. Con: a field beyond R15's list.
- **B. A journal kind.** The completion as a journal record of kind `hand_over`, data and not text. Pro: no new field. Con: the watcher must search the journal list for such a record after the last stage change.
- **C. The cost-table post's key.** Done when the keyed cost-table post exists. Con: completion read from the hosting service, which R22 keeps out of the truth; the post can land before the description is set.

**If changed:** F0002-S0002, F0006-S0002, F0007-S0009, F0009-S0004, and the drafts that copy the field: F0002-S0003, F0005-S0004, S0007, F0007-S0005, S0007, F0008-S0001, S0003, F0009-S0005, F0011-S0002.

#### Q8: The error cap

- Header: `Error cap`
- Source: interface sheet answer 10.

A handler that raises is counted per event and remote state, retried on later ticks and reported once at the error cap; kept thing 12 says it is tried three times. The working answer makes `ERROR_CAP` the constant 3 in `factory.domain.tick_status`, not a pipeline definition key, because R30 lists the attempts cap and the crash cap but not this one.

**Question.** Is the error cap a fixed constant of 3?

**Options**
- **A. Constant 3 (Recommended).** v1's figure, as kept thing 12 states it; nothing for a project to get wrong. Con: a project cannot tune it.
- **B. Pipeline key, default 3.** Like `attempts_cap` and `crash_cap`. Pro: uniform with the other caps. Con: one more key and rule, and a project could set it high enough to let a failing handler loop for long.

**If changed:** F0003-S0003, F0003-S0005, F0006-S0003, F0007-S0007, S0008, F0011-S0002.

### Batch 3: posts and the hosting service; files and names

#### Q9: The hosting interface's operations beyond R10's list

- Header: `Host ops`
- Source: interface sheet answer 12; F0001's acceptance, section 6.

R10 lists the hosting client's operations: create as draft or ready, read state and merge state, list comments, post with the marker, close and reopen, and labels. F0001 built ten operations; three go beyond the list (`find_open_pull_request`, `set_draft`, `set_description`), and `close` is in the list but no draft calls it, since the human closes (the sheet kept it because R10 is exact). Every acceptance of F0001 noted the extra three. Later stories use them: the open draft pull request reused (F0003-S0002, F0005-S0002), ready for review at the hand-over (F0007-S0009), and the description as decision 001's one projection.

**Question.** Does the hosting interface keep all ten operations, R10's list and the three beyond it?

**Options**
- **A. Keep all ten (Recommended).** Each extra serves a kept thing (draft or ready says whose turn it is; the description is the one projection); a decision entry records R10 as the floor. Con: R10's wording stays narrower than the code.
- **B. Drop close until needed.** Nine operations, none unused. Con: a change to an accepted interface and its tests, for one method R10 names.
- **C. Amend R10 instead.** The v2 planning widens R10's wording to the ten. Con: a change to the handover, which binds v1.1, for what A records anyway.

**If changed:** B is a new F0001 story (the tests of S0002, S0003 and S0014). Dropping an extra would change its users: F0003-S0002, F0005-S0002, F0007-S0005, S0009, F0009-S0004, F0010-S0004, F0011-S0003.

#### Q10: `set_labels` reads the label names

- Header: `Label read`
- Source: F0001's FEATURE.md, decision 5; F0001's acceptance, section 6.

Labels are a projection of the stage, written and never read back (R10, R22). F0001-S0003's `set_labels` reads the pull request's label names, so that it keeps the labels that do not start with `stage:` and replaces only the factory's own; the read stays inside the client and is never returned. Every acceptance of F0001 left this to the human. F0005-S0007 is its first caller.

**Question.** May `set_labels` read the label names inside the client to keep the human's own labels?

**Options**
- **A. Keep the internal read (Recommended).** Built; the human's labels survive, and nothing read reaches a decision. Con: a read of a hosting object, which a strict reading of R10 forbids.
- **B. Add and remove, no read.** Remove `stage:<s>` for every stage of the pipeline definition, then add the current one. Con: a call per stage per change, a failing call for each absent label, and a change to an accepted story.
- **C. Replace all labels.** Write only the stage label. Con: deletes the labels the human set.

**If changed:** a new F0001 story (S0003's `set_labels`); F0005-S0007.

#### Q11: The spellings in v1.1's files

- Header: `Spellings`
- Source: skeleton answer 5; interface sheet answer 2.

The glossary gives words, not spellings, so the interface sheet fixed them: folders `backlog/`, `in-progress/` and `done/`; branches `work-item/<id>`; headings `## Description`, `## Interface`, `## Acceptance criteria`, `## Smoke test` and `## Journal`; the files `factory/pipeline.yml`, `feature.md`, `factory/story-form.md` and `factory/feature-form.md`; the marker `<!-- factory -->` and the label prefix `stage:`. Where the glossary renames nothing, v1's spelling was not in the inputs and the sheet chose; v1 writes `FEATURE.md`, for example. F0001 already built the marker, `stage:` and `main`.

**Question.** Do the interface sheet's spellings stand?

**Options**
- **A. The sheet's spellings (Recommended).** Lower case and hyphens throughout, the glossary's word wherever there is one; every draft uses them. Con: a few differ from v1 where no rename asked for it (`feature.md`).
- **B. v1's where not renamed.** v1's template spelling wherever the glossary keeps the word (`FEATURE.md`, v1's form files). Con: mixed case; F0002-S0001 and every draft that names those files change.
- **C. Name changes in the answer.** The sheet's set, with the changes the human names.

**If changed:** F0002-S0001 (`paths`), F0002-S0006, S0008, F0003-S0003, F0005-S0002, F0006-S0001, F0009-S0001 to S0003, F0010-S0007 (the template), F0011-S0004; a change to the marker or to `stage:` is a new F0001 story.

#### Q12: Six small answers of the interface sheet

- Header: `Sheet bits`
- Source: interface sheet answers 1, 4, 5, 6, 8 and 13.

Six of the sheet's open questions are small, and each was answered with the sheet's own proposal. They are asked as one set, each with the alternative it beat:

- (a) Acceptance ids are `F0001-A0001`, sorted after their feature's stories by an explicit key, `work_item_order`. Alternative: a letter after `S`, so plain string order suffices.
- (b) `blocked` has five values (`question`, `attempts_cap`, `round_cap`, `crash_cap`, `send_back`), so an answer resets the right counter. Alternative: one value for the round cap and the send-back.
- (c) Only the human's journal entries carry a date, as in v1. Alternative: every entry dated.
- (d) The claim copies the role's `lease_duration`, so a later change of the pipeline definition never shortens a running claim (a key beyond R20's instance and start time). Alternative: read the definition at the stage-start commit.
- (e) The pipeline definition has a reader and no writer, since no story writes it. Alternative: a writer for R13's "one reader and writer", with a round-trip test.
- (f) `Boundaries` is a frozen dataclass that holds interfaces, not a Pydantic DTO. Alternative: a Pydantic model with arbitrary types allowed.

**Question.** Do the six answers (a) to (f) stand as taken?

**Options**
- **A. Confirm all six (Recommended).** Each follows v1 or the simplest reading of R13, R15 and R20, and the drafts use them. Con: six choices in one answer.
- **B. Change named ones.** The answer names the letters; each named one takes its alternative above.
- **C. Reopen all six.** Asked one by one at the end of this sitting, from the alternatives above.

**If changed:** (a) F0002-S0001, F0009-S0001 to S0006, F0011-S0002. (b) F0002-S0002, F0007-S0002, S0005, S0007, F0008-S0002. (c) F0002-S0005. (d) F0002-S0002, F0004-S0001, S0002, F0008-S0003. (e) F0003-S0003. (f) F0003-S0001 and every draft that builds `Boundaries(...)`.

### Batch 4: files and names

#### Q13: Write-path placeholders

- Header: `Placeholder`
- Source: interface sheet answer 7.

v1 let each agent write its own story file besides its lane. The sheet writes that into a role's write paths as placeholders: `{work_item}`, the work item's own file, and `{feature}`, its feature's directory, as in the acceptance reviewer's `{feature}/backlog/*`. Every role then lists at least one write path, which ST8.3 checks, and the guard and the undo expand them at the stage-start commit.

**Question.** Are write paths written with the placeholders `{work_item}` and `{feature}`?

**Options**
- **A. Placeholders (Recommended).** Explicit per role; a role that must not write its work item can say so. Con: every pipeline definition repeats `{work_item}`.
- **B. Own file always writable.** The work item's file is writable by every role implicitly; `{feature}` stays for the acceptance reviewer. Con: a rule hidden in code, and ST8.3's "a role without write paths" changes meaning.

**If changed:** F0003-S0003, S0005, F0004-S0003, S0005, F0009-S0006, F0010-S0007 (the template's pipeline definition).

#### Q14: Default `time_limit`s

- Header: `Time limits`
- Source: interface sheet answer 3.

v1 gave every `claude` and `make` call the full lease. R21 requires a role's agent run `time_limit` plus its stage's check and report `time_limit`s to fit inside its `lease_duration` (60 minutes by default), checked at load (ST8.5). The working answer defaults to 40 minutes for an agent run and 10 for a project command, both settable by the project. A stage with one check and one report then fits exactly (40 + 10 + 10), and a stage with two checks and a report at the defaults is refused at load, naming the role and the minutes.

**Question.** Do the defaults stay at 40 minutes per agent run and 10 per project command?

**Options**
- **A. 40 and 10 (Recommended).** The fixture's heaviest stage fits; a heavier one is told so at load. Con: a project with more checks must set its own figures.
- **B. Agent limit from the rest.** The agent run gets the lease minus its stage's checks and reports. Con: a default computed per stage, harder to read and to state in the docs.
- **C. No defaults.** Every `time_limit` is required. Con: fewer keys take a default under ST8.1, and every project writes figures.

**If changed:** F0003-S0003, S0005, F0010-S0007 (the template), F0011-S0002.

#### Q15: How a v1 work item is recognised

- Header: `v1 items`
- Source: skeleton answer 11.

v1.1 refuses to work beside a v1 work item in progress: a repository stop that names it, and nothing else, until it is archived or discarded (R26; decision 006, point 4). The working answer recognises a v1 work item by either of two signs: a file in v1's lifecycle folder `ongoing/` under the features root, or a work item whose front matter carries the v1-only key `comments_seen`. F0006-S0001 detects it through the lenient reader, since the strict one refuses `comments_seen`.

**Question.** Is a v1 work item recognised by either the `ongoing/` folder or the `comments_seen` key?

**Options**
- **A. Either sign (Recommended).** Catches v1's files where v1 put them and a v1 file moved by hand into `in-progress/`. Con: two rules to test.
- **B. The folder only.** Simpler. Con: a v1 file moved into `in-progress/` fails the strict reader as a counted error instead of a stop that names it.
- **C. The key only.** Con: a v1 work item in `ongoing/` is never seen, so never refused, though R26 is about exactly that case.

**If changed:** F0006-S0001, S0002, S0004, F0002-S0003 (`ignored_keys`).

#### Q16: WE6.3 as an observation

- Header: `WE6.3`
- Source: skeleton answer 9.

WE6.3 asks that every story's criteria include the docs criterion naming the documents it touches. The working answer checks it in the cross-feature check over the stories (round 1 found the `docs:` criterion last in all 76 drafts) and traces it as an observation, so F0011-S0004 has no code test for it. A code test would read the stories under `factory/features/`, which in `factory-rf` are v1's files in v1's format.

**Question.** Is WE6.3 an observation of the cross-feature check rather than a code test?

**Options**
- **A. An observation (Recommended).** Already done for every draft; no v1.1 code reads v1's story format. Con: stories added later, by acceptances, are checked only by v1's form check and the reviewer.
- **B. A code test.** F0011-S0004 adds a test over the stories under `factory/features/`. Con: v1.1's tests then depend on v1's file format.

**If changed:** F0011-S0004; `planning/overnight/traceability.md`.

### Batch 5: git and agents

#### Q17: How the factory's git gets the token

- Header: `Git token`
- Source: answers for F0001's round 1 (git credentials); cross-check round 1, blocker 3 and its answer.

The factory's own pushes need the hosting-service token, and no agent run may get it (R33, WE3.5). F0001's `GitCli` ignores the system and global git configuration on every call and takes credentials only through its `GitOptions.environment`, for example a credential helper given as `GIT_CONFIG_COUNT` entries or `GIT_ASKPASS` (FEATURE.md, decision 7). The working answer keeps that and asks F0010 to pass the token that way, never through a system or global `credential.helper`. The F0010 drafts predate the answer: F0010-S0008 sets `git config --system credential.helper`, F0010-S0003 the global identity and F0010-S0009 the global `core.sharedRepository`, none of which reaches `GitCli`.

**Question.** Does the factory's git get the token only through `GitCli`'s own environment, with no system or global git setting?

**Options**
- **A. Through GitOptions only (Recommended).** Matches the accepted wrapper; git behaves the same on every machine. Con: three F0010 drafts are redrafted.
- **B. Let git read system config.** `GitCli` stops ignoring the system file, so F0010-S0008 works as drafted. Con: a change to an accepted story; the agent's own git sees the same helper, safe only while the token file stays unreadable to it.

**If changed:** B is a new F0001 story (S0005's configuration rule and its tests), and the F0010 drafts stay. Under A the answer still has to be applied to F0010-S0001 (wiring `GitOptions`), S0003 (c16), S0008 (c15) and S0009.

#### Q18: The commit identity

- Header: `Identity`
- Source: answers for F0001's rounds 1 and 2 (commit identity, default identity).

`GitCli` commits as `factory <factory@noreply.invalid>`, v1's compose default, unless it is given an identity, which the wiring takes from `GIT_USER_NAME` and `GIT_USER_EMAIL` (R25). The round answers also said that F0010's preflight reports an unset identity, since kept thing 18 lists "identity set". F0010-S0004 departs: it builds no identity item, because with the default the identity cannot be missing. This file recommends the draft over the working answer: a preflight that stops on an unset variable would stop a machine that can commit, and the kept thing's point, that every commit has an identity, holds through the default.

**Question.** Is the commit identity a default that the settings override, with no preflight item for it?

**Options**
- **A. Default, no preflight item (Recommended).** As F0010-S0004 drafts it; nothing stops on it. Con: an operator who forgets the settings commits as `factory`.
- **B. Default; preflight stops if unset.** The working answer read as a stop: the default serves tests and Demos, production must set both. Con: a stop for a value that has a working default.
- **C. Default; a line if unset.** A time-stamped line at start, no stop. Con: a line that nobody may read.

**If changed:** the working answer is B. For B or C: F0010-S0004 (an identity item), F0010-S0001 (the settings). Either way F0010-S0003's global `git config` lines go with Q17's answer.

#### Q19: Who writes the shipped agent files

- Header: `Agent files`
- Source: skeleton answer 7.

The factory ships its agents and their settings under `claude/`, and its image and template under `image/` and `template/`; none of the three exists in `factory-rf` yet. The seed's `factory/stages.yml` already puts all three in the coder's write paths. The working answer has F0010's stories write the shipped agent, skill and settings files new, in the glossary's names (role `acceptance-reviewer`, stage `smoke-test` and so on), rather than copy v1's through the seed. F0010-S0007 drafts seven agents and the settings.

**Question.** Are the shipped agent and settings files written new by F0010's stories, in the glossary's names?

**Options**
- **A. Written by F0010 (Recommended).** The names match the pipeline definition, and SI4.2 tests every key. Con: v1's instructions must be carried over by a story (round 2's Q29).
- **B. Copied by a seed commit.** v1's files copied and renamed by the human before F0010. Con: a large commit outside the pipeline, and v1's dead keys come along until F0010-S0006 refuses them.

**If changed:** F0010-S0002, S0003, S0006, S0007; Q29 is then not asked.

#### Q20: The production wiring grows with each feature

- Header: `Wiring`
- Source: cross-check round 1, blocker 1 and its answer.

Cross-check round 1 found that no story built the production wiring, so `factory-run` would dispatch every `run` event to `UnhandledEvent`. The working answer grows `factory.entry.wiring` with each feature: `build_boundaries(settings)` and `build_dispatcher(boundaries, definition)`. F0006 creates `build_dispatcher` and registers `StageRunner` as the `run` handler, every later story that adds a handler registers it there with a criterion, one test checks that every event kind built so far has a handler, and F0010-S0001 completes `build_boundaries`. The drafts of F0006 to F0011 do not carry this yet.

**Question.** Does the production wiring grow with each feature, with a test that every event kind built so far has a handler?

**Options**
- **A. Grows per feature (Recommended).** Each feature's handlers run in a real tick when it is accepted, and a missing handler fails a test early. Con: a wiring criterion in several stories.
- **B. One wiring story, last.** F0010-S0001 wires everything. Con: F0006 to F0009 are accepted with handlers that no production path calls, and their acceptances cannot run a real tick.

**If changed:** the answer is still to be applied either way: F0006-S0004, F0007-S0010, F0008-S0001, S0003, F0009-S0006, F0010-S0001, F0011-S0001.

### Batch 6: git and agents (F0001's open points)

#### Q21: The pinned Claude Code version

- Header: `Claude pin`
- Source: F0001's acceptance, sections 4 and 6.

R29 pins every tool, and the preflight compares the agent runtime's version with the pinned one (ST5.3). F0010-S0002 drafts `CLAUDE_CODE_VERSION=2.1.289`, the version of v1's last build, and F0001's `claude -p` runtime was built from v1's book, whose flags ran on that version. The operator guide does not name the version yet; F0001's acceptances asked for it.

**Question.** Which Claude Code version does v1.1 pin?

**Options**
- **A. 2.1.289, v1's last (Recommended).** The flags F0001 uses last ran there; the operator guide names it when F0010-S0002 is built. Con: an older release.
- **B. The current release.** Taken at the morning build. Con: a flag F0001 uses may have changed; only Q22's probe would show it.
- **C. The human names one.** In the answer.

**If changed:** F0010-S0002 (the `ARG` default), F0010-S0004's Demo, `docs/operator-guide.md`.

#### Q22: A preflight probe of the agent run's flags, `PATH` and `HOME`

- Header: `Flag probe`
- Source: F0001's FEATURE.md, decisions 17 and 18; F0001's acceptance, section 6.

No stand-in can show whether the pinned `claude` accepts F0001's flags or how it exits on a budget stop. Decision 18 therefore asks F0010's preflight to run S0009's exact argument list once against the pinned `claude`, because a rejected flag would end every real run `died` with no text that says why. Decision 17 adds that a request's environment must hold a `PATH` with `factory-guard` and a `HOME`, or the guard hook fails open and the login is not found. The F0010 drafts keep `PATH` (S0008) and set `HOME` for the agent user (S0009), but no preflight item runs the argument list or checks the two.

**Question.** Does F0010's preflight run one real `claude -p` call with the factory's exact arguments and check `PATH` and `HOME`?

**Options**
- **A. Probe call and checks (Recommended).** One preflight item, run once per image build under ST4.3's stamp: a rejected flag or a missing guard becomes a named machine stop. Con: one short model call per build.
- **B. Check PATH and HOME only.** No model call. Con: a rejected flag still shows only as every run ending `died`.
- **C. Morning observation only.** Decision 18's fallback. Con: nothing checks it again after the image changes.

**If changed:** no draft has the item yet: under A or B, F0010-S0004 or S0005 gains it, and F0005-S0001 (the request's environment) is checked against it.

#### Q23: Where `claude --version` runs

- Header: `Version dir`
- Source: F0001's acceptance, sections 4 and 6.

The runtime's `version()` runs `claude --version` in the factory process's current directory (F0001-S0010), and the preflight calls it (F0010-S0004). The acceptances left open whether that directory should be fixed: the process may start anywhere, the checkout included, and a reclone removes the checkout.

**Question.** How is the directory of `claude --version` fixed?

**Options**
- **A. Entrypoint fixes the directory (Recommended).** F0010-S0003's entrypoint starts the factory in a fixed directory; no F0001 change. Con: the rule lives in the image, not in the code.
- **B. version() takes a directory.** The interface gains a parameter. Con: a new F0001 story that changes an accepted interface and its tests.
- **C. Leave as built.** Con: the result may depend on where the process started.

**If changed:** A: F0010-S0003. B: a new F0001 story and F0010-S0004.

#### Q24: F0001's three unsourced defaults

- Header: `F0001 limits`
- Source: F0001's FEATURE.md, decision 19; F0001's acceptance, section 6.

Three figures in F0001 have no source in the handover or in v1's facts: a `time_limit` of 5 minutes on every git call, 30 seconds for `version()`, and a minimum of 0.50 dollars for the budget resume (v1's facts give only "a quarter more"). They are built and accepted. Every later git user depends on the first, so a clone or fetch of a large repository must finish within 5 minutes.

**Question.** Do the three defaults stand: 5 minutes per git call, 30 seconds for `version()`, a resume of at least 0.50 dollars?

**Options**
- **A. Keep all three (Recommended).** Generous for the todo demo and `factory-rf`; no change. Con: a large clone on a slow network becomes a counted error.
- **B. Make them settings.** Instance settings with these defaults (F0010-S0001). Con: three more settings and a wiring change for figures nobody has needed to change.
- **C. Change named figures.** In the answer, built by a small F0001 story.

**If changed:** B: F0010-S0001. C: a new F0001 story (S0005, S0010).

### Batch 7: F0001 leftovers

#### Q25: The hand-ported branch-name rules

- Header: `Branch rules`
- Source: F0001's acceptance, section 6 ("Taken in S0021 without asking").

S0021 refuses, before `push` and `delete_remote_branch` run, any name that git would not take as a branch. Its coder ported git's branch-name rules into the domain by hand instead of calling `git check-ref-format --branch`, because the domain runs no tool and the call would cost a process per push; the port matches git 2.39.5 over 3,061 names. A later git that tightens its rules would not be followed until a story changes the port, and the image pins git (F0010-S0002), so that happens only on a deliberate upgrade.

**Question.** Does the hand port of git's branch-name rules stand?

**Options**
- **A. Keep the port (Recommended).** Built and compared with git; the pinned image keeps git still. Con: an upgrade of git needs the comparison run again.
- **B. Call git instead.** `GitCli` asks `git check-ref-format`. Con: a story, a process per push, and the check leaves the domain.

**If changed:** a new F0001 story; F0010-S0002 (a note on upgrading git).

#### Q26: A path removed only from the index

- Header: `rm --cached`
- Source: F0001's acceptance, section 6; F0001-S0011's journal.

`changed_paths` reports a path removed from the index with `git rm --cached`, but still on disk, as "modified", even when its content is unchanged. The human decided the twin case in decision 21: an unmerged path stays "modified" in `status()`, and a kind of its own would be a story of its own. The undo (F0004-S0005) reverts a "modified" path outside the write paths from the stage-start commit, so its result does not depend on the kind.

**Question.** Does a path removed only from the index stay "modified"?

**Options**
- **A. Stays modified (Recommended).** As decision 21 for unmerged paths; the undo's result is right. Con: the kind is imprecise.
- **B. A kind of its own.** A story adds an exact kind. Con: a new `ChangeKind` value that every user of `changed_paths` must handle.

**If changed:** a new F0001 story; F0004-S0005.

#### Q27: Seven small tidy-ups

- Header: `Tidy-ups`
- Source: F0001's acceptance, sections 3 to 6.

F0001's fourth acceptance carried seven small items, none of them a broken promise:

1. `RemoteBranch` is the only result model that is not frozen (`src/factory/domain/git.py`).
2. `tests/application/test_git_protocol.py` and `test_hosting_protocol.py` still say "protocol" after the switch to abstract base classes.
3. `merge` checks its ref twice, directly and again through `is_ancestor`.
4. No test row has a control character between 0x10 and 0x1f for `check_branch_name` (the one surviving mutant).
5. FEATURE.md decision 16 still says the feature has "fourteen" stories; it has twenty-one.
6. Three one-line remnants in the documents: the WE6.3 planning tag in the operator guide, the project guide's "until then `CLAUDE.md` holds the rules", and the README's "(partly written)".
7. The decision entry that holds decisions 22 and 23 is one dense paragraph.

Items 2 and 4 change tests another stage wrote, which needs the human's word (`CLAUDE.md`), and no stage's write paths cover FEATURE.md (item 5). The document remnants have now been carried through four acceptances while waiting for "the next documenter that touches the file", which is why this file recommends a story of their own.

**Question.** How are the seven tidy-ups handled?

**Options**
- **A. One housekeeping story now (Recommended).** Items 1 to 4, 6 and 7 through the pipeline for about $1.50, with this answer as the word for items 2 and 4; item 5 stays as a historic statement. Con: a full run for one-liners.
- **B. Fold into next stories.** Each goes into the next story that touches its file. Con: folding has not happened in four acceptances; some items wait until F0011-S0004.
- **C. A commit by the human.** Fast and free. Con: outside the pipeline, with no review.
- **D. Leave them.** Con: the document remnants mislead a newcomer.

**If changed:** A is a new F0001 story, proposed with the answer. B: the next drafts that touch `src/factory/domain/git.py`, `src/factory/adapters/git_cli.py`, the two test files, `docs/` and `README.md`.

## Round 2: questions that depend on a round-1 answer

### Batch 8

#### Q28: The tick status across a restart

- Header: `Tick status`
- Source: skeleton answer 14.
- Depends on: Q6 (keyed posts).

v1 deleted its tick memo at every start. The working answer keeps the tick status, the error counts per event and remote state, as a local cache that a restart may reset. Because the error-cap report is keyed, a restart cannot post it twice, but it may reset an error's count, so a failing handler gets up to three more tries after each restart; the morning report notes this. ST1.1's "further ticks on the same state post nothing" holds through the key.

**If Q6 is A or C (posts are keyed), ask:**

**Question.** Does the tick status stay a local cache that a restart may reset?

**Options**
- **A. Local cache, may reset (Recommended).** Disposable as R18 wants; the key stops a second report. Con: each restart grants a failing handler up to three more tries.
- **B. Kept in the repository.** The error counts committed, for example in the front matter. Con: a commit per counted error, and the factory's own faults written into work items.
- **C. Kept on a volume.** A file that survives restarts. Con: state the remote does not hold, which R18 and decision 001 avoid.

**If Q6 is B (state first, no key), ask instead:** "Is the error-cap report recorded in the work item before it is posted?", with the options **A. Recorded, then posted (Recommended):** the report survives a restart as state, and a restart cannot repeat it; con: a commit per report. **B. Tick status on disk:** the counts and the reported flag kept on a volume; con: state the remote does not hold.

**If changed:** F0006-S0003, F0007-S0007, F0011-S0001.

#### Q29: How much instruction the shipped agents carry

- Header: `Agent text`
- Source: cross-check round 1, note 20 (a drafter's choice that follows from skeleton answer 7).
- Depends on: Q19 (who writes the shipped agent files).

F0010-S0007 ships seven agents whose bodies hold one boundary sentence and one entry sentence each, and leaves v1's long stage and role texts to the human. Kept things 5 and 6 lean on those instructions, and the baseline run compares cost and time with run 4 (R35, within +25 %), which ran on v1's instructions. There is no working answer: the F0010 drafter chose the short bodies.

**If Q19 is A (written by F0010), ask:**

**Question.** Do the shipped agent files carry v1's instructions, renamed?

**Options**
- **A. v1's texts, renamed (Recommended).** F0010-S0007, or a story after it, carries v1's role and stage texts over in the glossary's names. Pro: the baseline run compares with run 4 on the same instructions. Con: a long story, and text no test can check.
- **B. Short bodies; human adds.** As drafted; the human writes the texts before the baseline run. Con: the baseline run waits on a task outside the pipeline.
- **C. Short bodies only.** The two sentences are all the instruction. Con: the agents run without v1's guidance, and the comparison with run 4 says little.

**If Q19 is B (copied by a seed commit):** not asked; the copied files carry v1's texts.

**If changed:** F0010-S0007 (A splits it or adds a story after it); `docs/project-guide.md`.

## Settled, not asked

- Skeleton answer 6, the lease clock: decided by decision 007, question 4.
- Skeleton answer 10, the PyGithub client tested with stand-ins: built by F0001-S0003 and accepted; no later story depends on it, and the real API is the baseline run's observation.
- Skeleton answer 12, dependencies read per condition: the plan reads its own table that way (SI1 split, ST8 before ST3), and no other reading gives an order that holds (skeleton, open question 12).
- Skeleton answer 13, the size of F0001: built, with twenty-one stories, and accepted.
- Skeleton answer 16, Docker, root and a second OS user in v1's container: a fact checked on the PC (none is available).
- Header of the answers, interfaces as abstract base classes: decided by the human (`CLAUDE.md`; F0001's decision 20).
- Interface sheet answer 9, the keys of `AgentDefinition`: a fact of the pinned runtime that F0010-S0006 finds (SI4); nothing to choose before it.
- Interface sheet answer 14, the event kinds checked against v1: an instruction to F0006's drafter, carried out in drafting.
- Answers during drafting, the console scripts: done (`pyproject.toml` holds the six scripts as `factory.entry.<module>:main`); `pyproject.toml` is in no write path, so no story could add them.
- F0001 round 1, `claude -p` flags only from v1's book: built (decision 13) and accepted; what remains is Q22's probe.
- F0001 round 1, the budget stop decided from `subtype`: built (decision 13) and accepted; no later story depends on it.
- F0001 round 1, splitting stories above 22 criteria: superseded by round 2's limit of 26, which is the plan's own.
- Cross-check blocker 2, `crashes` reset on a forward move, built in F0005: the reset is decision 006, point 5 (R23); building it in F0005 follows `CLAUDE.md`'s rule that a coder may not change a test it did not write.
- F0001 round 2, `GitOptions` as one constructor argument: built (decision 10) and accepted; it follows ruff's limit of five arguments (R4).
- F0001 round 2, 26 criteria at most: the plan's limit.
- F0001 round 2, S0004's demo flushes after each write: built and accepted; nothing later depends on it.
- F0001 round 2, nested make: built (decision 11) and accepted; nothing later depends on it.
- F0001 round 2, a resumed call that reaches its `time_limit` has no cost, turns or tokens: follows R24 (nothing partial or estimated); built.
- F0001 round 2, S0002's garbled lines: an editorial fix, built.

## Answers
