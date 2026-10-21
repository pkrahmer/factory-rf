# Re-check of F0038, the documents say what is true today, right before it starts

Checked on 2026-10-21 against `main` at `e5c6c147` (night log: F0039-S0005 merged, S0006 started). Merged since the fresh pre-check (`F0038-fresh.md`, at `ea3b2af2`): F0040-S0001 to S0006, F0027-S0001 to S0007, F0029-S0003, F0030-S0002 and S0003, F0037-S0002 and S0003, F0039-S0001 to S0005 and S0007, and their acceptances. Still open: F0039-S0006 (the boundaries have no optional collaborators) is running, and F0040-S0007 (the tests of the agent's user share their stand-in `sudo` and recording log) is unbuilt. The edits below are applied to the drafts (CRLF kept; S0001 was LF in the tree and is unchanged).

## What I ran

- Every old text the ten stories quote, counted on today's docs (`grep -c -F`). Each occurs once, except " (F0007)" in `git-and-hosting.md` (twice, as S0004 means: both go) and `WE3.3: `, `WE3.4: ` (twice each, as S0006 means).
- `git log ea3b2af2..HEAD` over `docs/` and `README.md`, story by story, and `git show` of the docs commits of F0040-S0006, F0037-S0003 and F0039-S0005.
- The module index loop of S0003 and `[project.scripts]` in `pyproject.toml`.
- `git log 830029c9.. -- claude/agents/`: no change since the fresh pre-check, so S0010's list still holds.
- Form: `factory.entry.check_story` from today's `src`, in a throwaway container of `factory-self-factory` (`--network none --cpus 1`, a `git -c core.autocrlf=false archive HEAD` copy under `C:/Users/pasca/AppData/Local/Temp/pc38r`, the edited drafts and `feature.md` copied in as LF under `factory/features/F0038-.../`): all ten `ok`, after the edits.
- Every smoke block that does not need `git diff`, `make` or `uv run`, in the same container, on today's docs. Output in the story sections below.
- Two small prototypes on the copy: S0009's changes to `docs/decisions.md` (its second smoke block printed `0`, `0` and nine `1`; `check_documents` printed `documents ok`), and S0003's three index changes (the index loop printed only `end`). The copy is deleted.

## The re-check list, item by item

1. **Titles of the entries S0009 cites.** All are headings now: *The project commands run as the agent user, with the git folder sealed* (F0040-S0002), *Every agent run and every project command starts from a fresh agent home* (F0040-S0004), *The factory removes the git-ignored paths after every agent run and at the restore* (F0027-S0003), *The Claude Code hook is removed; the kernel and the undo are the write guard*, *The factory alone writes the checkout's `.git`*, *The agent's own `timeout` kills a run under `sudo` at its time limit*. F0040-S0006, F0037-S0003, F0029-S0003, F0030-S0003, F0040-S0001/S0003 and F0027-S0005/S0006 wrote no new entry; F0037-S0003 changed *A record line that is not UTF-8 is skipped* (decision 4 answered), F0039-S0001 and S0007 added bullets to *What the agent runtimes share lies in one module*, F0039-S0005 a line to the entry on `NOT_YET_HANDLED`. None of these touches a passage F0038 quotes.
2. **How old entries were marked.** F0040-S0002 put "Replaced on 2026-10-20 by *...* (F0040-S0002)." at the start of the `Date:` paragraph of *The project commands run as the factory's user and are left for v2*, and its own entry cites the old title ("It replaces *...*."). F0040-S0004 changed "Left for v2." on the agent's home into "Left for v2 (closed on 2026-10-20 by *Every agent run ...*)." and its own entry quotes "*The agent's home stays writable by the agent (L69) ... Left for v2*". That quote is a third "Left for v2" the draft did not know: S0009's smoke would print `3`, not `0`. S0009 edited (below).
3. **The operator guide's **Left for v2.** paragraph.** Gone (F0040-S0002). The `sudo` refusal of the preflight's `lint` stands only in the six-row table *The stops you will see here* (S0008 edited).
4. **What F0027-S0003, S0005 and S0007 wrote.** S0003: the *Used by* cell is "F0027: after every agent run (`run_sealed`) and at the restore (the tick)", not the wording the draft guessed (S0004 edited); "(left for v2)" is out of `write-guard.md`, as the human decided; the tick table's `checkout_restore_failed` row names "an ignored folder". S0005 added repair advice to that row only (`chmod -R g+w <path>` as root, the crash and the crash cap): S0008's new paragraph would have dropped it (S0008 edited). S0007 added the *Accepted:* bullet to its entry; nothing F0038 quotes.
5. **What F0039-S0005 left of the `NOT_YET_HANDLED` sentence.** Only "every kind of event has a handler. Should a future kind have none, the event leads to this:", and the next paragraph. The clause on `NOT_YET_HANDLED` is gone. S0007's third bullet is now exact (edited).
6. **"morning observation" from F0027-S0002 or F0040-S0004.** None. The four rows F0040-S0006 added to the table start with no planning code, and every "orning observation" in the guide is one S0006 already replaces. The criterion that covered unknown new ones is moot and dropped. But F0040-S0002 wrote "the commands run as the factory's user, as before." in **The project commands run as `agent`.**: S0006's first grep would print `1` (edited).
7. **S0004's quotes in passages F0039 rewrote.** All present once: "(R24: no partial figure; ...)" in `agents.md` survived F0039-S0001. F0039-S0006 is still running and changes `stages.md`, `agents.md`, `watching.md` and `processes-and-checks.md` (clauses on what happens without the settings, the waiter or the records, and `os_user`); none of S0004's quotes is such a clause, but they can only be confirmed once it is merged (see *For the human*).
8. **The module index.** Four modules are missing today: `factory.domain.sessions`, `factory.entry.health` (both known), and F0040-S0004's `factory.application.agent_home` and `factory.adapters.agent_home`. `factory.domain.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home` and `factory.entry.leftovers` are indexed. S0003 now names the two exactly (edited).
9. **The console scripts.** Six in `pyproject.toml` (`factory-check-story`, `factory-confine`, `factory-bill`, `factory-watch`, `factory-run`, `factory-health`); `leftovers` and `fresh_home` are run with `python -I -m` and are no scripts. S0002 as drafted.
10. **Smoke greps and the form check.** Below, and all ten `ok`.

## Per story

### F0038-S0001 (the template and the demo run under the guard)

Ready as drafted. The paragraph is at `docs/operator-guide.md:968`, and the files hold what the new one says. Smoke today: `1`, `0`; the four file lines as expected.

### F0038-S0002 (the README says what the factory is)

Ready as drafted. Six console scripts; the paragraph "Beside the seven console commands" is unchanged. Smoke block 1 today: `2`, `0`, `0`, `0` (line 3's inventory and line 14's "seven console commands").

### F0038-S0003 (the template's pipeline definition as a pointer, and `factory-health`)

Ready with edits, applied. The conditional "if its documenter did not name them" is now a fact: F0040-S0004's documenter named `factory.domain.agent_home`, `factory.adapters.home_files` and `factory.entry.fresh_home` on the `agents.md` line, but not the two `agent_home` modules of the application and the adapters.

- Description: "except two" became "except four", with one sentence on the two `agent_home` modules; the last sentence names them in place of "any other module that a story merged before this one left out".
- Criterion 3, third bullet: the `agents.md` index line's parenthesis "(`factory.domain.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home`)" becomes "(`factory.domain.agent_home`, `factory.application.agent_home`, `factory.adapters.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home`)". The open-ended fourth-bullet sentence on "a module that a story merged before this one" is dropped as moot.

Smoke today: `1`, `0`; `0`, four `missing:` lines, `end`. On the prototype: only `end`.

### F0038-S0004 (no planning code or v1 feature id)

Ready with one edit, applied. Every quote occurs; the grep prints `git-and-hosting.md:10` today (the `remove_ignored` row is the tenth).

- Criterion 3, the `git-and-hosting.md` bullet: the guessed cell became the real one: "F0027: after every agent run (`run_sealed`) and at the restore (the tick)" → "the sealed run and the restore: after every agent run (`run_sealed`) and at the restore (the tick)"; the catch-all sentence stays.

### F0038-S0005 (superseded marks, the removal of `factory/v1/`, the codes)

Ready as drafted. The three places and the three cited headings are unchanged; `CLAUDE.md` still names R3, R5 to R13 and R17. Smoke today: `0`, `0`, `0`, `1`, `1`, `1`.

### F0038-S0006 (an opening, a contents list, the current rule without history)

Ready with edits, applied.

- Criterion 3, the "as before" bullet gains: In **The project commands run as `agent`.**, "the commands run as the factory's user, as before." becomes "the commands run as the factory's user." (F0040-S0002 wrote it; the first grep counts it).
- Criterion 3, the morning-observation bullet: "Any other ... (F0027-S0002 and F0040-S0004 write into that table ...) ..." is dropped as moot; "No row of the table starts with a planning code." stays.

Smoke block 1 today: `25`, `0`. The guide has 1,519 lines ("about 1,500" holds).

### F0038-S0007 (what the operator sees, not the classes)

Ready with edits, applied. All the names still occur (17 matching lines), and `machine_extras` in `factory.entry.wiring` is in the preflight's paragraph.

- Description: "(F0039-S0005 removes the last, `NOT_YET_HANDLED` in `factory.entry.wiring`)" became "(F0039-S0005 already removed `NOT_YET_HANDLED` and its clause)".
- Criterion 3, third bullet: the sentence that follows "every kind of event has a handler." is named exactly ("Should a future kind have none, the event leads to this:"), in place of "and any clause on `NOT_YET_HANDLED` that F0039-S0005 left".

Smoke today: `17`; `2`, `1`.

### F0038-S0008 (each stop in one table)

Ready with edits, applied.

- Criterion 3, second bullet: the `sudo` refusal is now a named fact moved to "The preflight's items" ("with an agent user a missing `sudo` rule ends the probe's `lint` as `the probe on main could not run: project command lint failed: <sudo> refused the command: ...`"); the "F0040-S0002 may write one" sentence is dropped as moot.
- Criterion 3, third bullet: the new tick paragraph also keeps the repair of F0027-S0005's row: when an agent run left the path the stage ends without a result and, once the checkout is repaired, is recorded as a crash and run again; `chmod -R g+w <path>` as root on the path git names, or remove it as root; a second run that leaves the same path reaches `crash_cap`. The parenthesis "(F0027-S0003 adds that cause to the table's row)" is gone.
- Smoke block 2 gains `refused the command` and `chmod -R g+w <path>`: seven lines `found` (a keep-check, true before and after).

Smoke today: `6`, `1`; seven `found`.

### F0038-S0009 (what was left for v2 is named open and not planned)

Ready with edits, applied. The human's answers stay as they are.

- Description: "By the time this story starts, four of the gaps are closed" became "Four of the gaps are closed, each by a story merged before this one"; the story also takes "Left for v2" out of the line of *Every agent run and every project command starts from a fresh agent home* that quotes it.
- Criterion 3, the agent's home: the old text is now exact, "Left for v2 (closed on 2026-10-20 by *Every agent run and every project command starts from a fresh agent home*)." → "Closed by *Every agent run and every project command starts from a fresh agent home*.".
- Criterion 3, the renamed entry: F0040-S0002's inline mark "Replaced on 2026-10-20 by *...* (F0040-S0002). " is named and removed (the paragraph then begins "Date: 2026-10-16"), and the one citation is exact: "It replaces *The project commands run as the factory's user and are left for v2*." → "It replaces *The project commands first ran as the factory's user; replaced*.".
- Criterion 3, a new bullet: in *Every agent run and every project command starts from a fresh agent home*, "It closes the sentence *The agent's home stays writable by the agent (L69) ... Left for v2* of the entry of 2026-10-16." → "It closes the sentence on the agent's writable home (L69) in *The agent is started through `sudo -n -u agent -- env -i`, and a run's files are `0640`*.".
- Criterion 3, last bullet: the part on `README.md`, the operator guide and the project guide is true already (F0040-S0002, F0027-S0003); it is marked so and kept as a guard.
- Smoke block 1: its Expect says it is true before the story too. Block 2: the heading loop gains the newly cited title; Expect eleven lines, `0`, `0`, then nine `1`.

Smoke today: eleven `:0`; then `3`, `1`, `0`, `0`, seven `1`. On the prototype: `0`, `0`, nine `1`, and `documents ok`.

### F0038-S0010 (every passage of v1.1's own in the shipped agents)

Ready as drafted. No commit has touched `claude/agents/` since the fresh pre-check, and the sentences it quotes in `agents.md` (line 303, "Six passages ... (F0034-S0001).", and line 360) are unchanged. Smoke today: `2`; two `named`, seven `missing`.

### feature.md

No edit needed.

## For the human

1. **May F0038 start before F0040-S0007 is built?** `feature.md` says all stories start after F0040 is merged, and F0040-S0007 waits for a leave. Its docs criterion changes only *Shared test helpers* in `docs/project-guide/README.md`, a section no F0038 story touches (S0003 changes three lines of *The files*), and it changes tests only. (a) Yes, start F0038 now (after F0039-S0006); F0040-S0007 follows whenever its leave comes. (b) No, wait for F0040-S0007. Recommended: (a).
2. **F0039-S0006 is still running.** It changes clauses in `stages.md`, `agents.md`, `watching.md`, `processes-and-checks.md` and one entry of `docs/decisions.md`. None of F0038's quotes is such a clause, but none can be confirmed before it is merged. Nothing to decide; before S0004 starts, run S0004's first smoke block and count its quotes once more (expected today: `README.md:1`, `agents.md:4`, `costs.md:2`, `git-and-hosting.md:10`, `stages.md:1`, `watching.md:3`, the rest `:0`).

No story's text depends on F0040-S0007, so every story is ready once F0039-S0006 is merged. Only the order rule of `feature.md` holds them back until the human answers question 1. S0001 and S0002 touch no file that F0039-S0006 changes (the operator guide's one paragraph, `README.md`), so they do not even need the re-count of item 2.

## Verdict

`F0038: all ten stories accepted at intake as they now stand; S0001, S0002, S0005 and S0010 unchanged; edits applied to S0003, S0004, S0006, S0007, S0008 and S0009, none needing the human.`
