# Fresh pre-check of F0038, the documents say what is true today

Checked on 2026-10-20 against `main` at `ea3b2af2` (F0030-S0001, F0037-S0001, F0041-S0001 to S0004, F0027-S0001 and F0032 merged; F0027-S0002 in progress), and against the stories queued before F0038: F0027-S0002 and S0003, F0029-S0003, F0030-S0002 and S0003, F0037-S0002 (in `factory/features/*/backlog/` and `in-progress/`), F0039-S0001 to S0006 and F0040-S0001 to S0004 (in `planning/overnight/stories/`). The earlier round-1 edits (`F0038-S000*-1.md`) are all in the drafts; the human's answers are in `feature.md`.

## What I ran

- Every old text each story quotes, counted on today's docs: each occurs exactly once, except the ones named under the stories below. S0001's paragraph is now at `docs/operator-guide.md:929`.
- Every grep block of the smoke tests, on today's docs (host checkout, CRLF; the counts do not depend on it). Each block tells today's text from the changed one, except the keep-checks of S0007 (block 2) and S0008 (block 2), which are meant to pass before and after.
- Form: `factory-check-story` (`factory.entry.check_story` from today's `src`) in a throwaway container of `factory-self-factory` (`--network none`, LF copies under `C:/Users/pasca/AppData/Local/Temp/pc38`): all nine drafts `ok`, and all ten stories with the edits below applied (S0010 new) `ok`.
- A small prototype on the same copy: S0002's README as edited below and S0006's opening and contents list. `python -m factory.entry.check_documents` printed `documents ok`; S0002's first block printed `0`, `6`, `2`, `1` (the new first paragraph has 529 characters), and S0006's Python block printed `True True`.
- `git log 830029c9.. -- claude/agents/` for the folded F0034-S0003 (see S0010).

## Verdicts in short

- S0001: still true, as drafted.
- S0002: required edits: `factory-guard` is gone since F0041-S0002, so there are six console commands, and the README's contract paragraph still says "seven".
- S0003: required edits: `factory.domain.sessions` (F0030-S0001) is also missing from the index; F0040-S0004 may add two more modules without an index line.
- S0004: required edit: F0027-S0003 adds a row `F0027: ...` to the table S0004 rewrites.
- S0005: required edit: `CLAUDE.md` names R3 and R17 too, not only R5 to R13.
- S0006: required edit: F0027-S0002 and F0040-S0004 write into the "morning observations" table; one optional.
- S0007: required edit: F0039-S0005 removes the clause the third bullet starts from; two optional.
- S0008: required edits: F0040-S0002 may add a detail to the six-row table, and F0027-S0003 adds a cause to the `checkout_restore_failed` row.
- S0009: rewritten to the human's answers: four gaps are closed by queued and merged stories, one stays open; the operator guide's part is F0040-S0002's.
- S0010 (new): the folded F0034-S0003 as a story of its own, with the passages `git log` shows today.
- `feature.md`: required edits for the scope, the stories list and the folded section.

Edits that depend on a queued story say so in their heading; the list at the end names what to re-check right before F0038 starts.

## The human's answers

Given on 2026-10-20 to the questions at the end; the edits below already follow them, and they are applied to the drafts.

1. F0034-S0003 becomes S0010, a story of its own, last in the order (as recommended).
2. The new entry is titled *v2 is retired; nothing is left for v2* (as proposed). Not as recommended in question 5: the replaced entry *The project commands run as the factory's user and are left for v2* is renamed too. Its new title is *The project commands first ran as the factory's user; replaced*, and a paragraph directly under it says "Replaced by *The project commands run as the agent user, with the git folder sealed*." S0009's criterion 3 and its smoke test say so, and every citation of the old title in the log follows.
3. F0027-S0003 removes "(left for v2)" from `write-guard.md`, *Limits* (as recommended): its docs criterion gains the sentence: The passage loses "(left for v2)", and its smoke test one grep block (`0`). S0009 changes only `docs/decisions.md`.
4. S0007 removes the made-up handler case (as recommended); F0039-S0005 stays as it is.

### F0038-S0001

Verdict: accepted as drafted. The old paragraph occurs once (`docs/operator-guide.md:929`), and the files hold what the new paragraph says (`template/Makefile:3`, `demo/todo-service/project/Makefile:3`, both `pipeline.yml`s `:1`). No queued story touches the paragraph (F0027-S0003 writes into *The project's make targets*, another section). Smoke blocks today: `1`, `0`; the four file lines as expected. No edits.

### F0038-S0002

Verdict: accepted with edits 1 to 7, all required. F0041-S0002 removed `factory-guard`: `pyproject.toml` has six console scripts (`factory-check-story`, `factory-confine`, `factory-bill`, `factory-watch`, `factory-run`, `factory-health`). Today's *Getting started* says "Six commands exist" (about 1,200 characters), but the paragraph after it still begins "Beside the seven console commands", and the draft's table asks for seven rows with a `factory-guard` row. The first paragraph has changed its opening words since the draft ("The factory, reimplemented by v1 of itself."), but it still holds "under construction", "groundwork" and "probe of 2026-10-17", so the criterion and the first grep still fit. No queued story touches `README.md`. Smoke block 1 today: `1`, `0`, `0`, `0`; on the prototype `0`, `6`, `2`, `1`.

Edit 1 (required, Description (F0041 removed `factory-guard`; six console commands)). Replace

```markdown
Its *Getting started* paragraph lists the seven commands with their exit statuses in one sentence of about 1,300 characters
```

with

```markdown
Its *Getting started* paragraph lists the six console commands with their exit statuses in one sentence of about 1,200 characters
```

Edit 2 (required, Description). Replace

```markdown
The paragraph on `python -m factory.entry.contract` and `check_documents`, *How it is built* and *Replaced from v1* stay as they are.
```

with

```markdown
The paragraph on `python -m factory.entry.contract` and `check_documents` keeps its text but its first words, which still count seven console commands from before F0041 removed `factory-guard`; *How it is built* and *Replaced from v1* stay as they are.
```

Edit 3 (required, Acceptance criteria, criterion 3, second bullet). Replace

```markdown
and exactly seven rows, in this order,
```

with

```markdown
and exactly six rows, in this order,
```

Edit 4 (required, Acceptance criteria, criterion 3, second bullet (the command is gone since F0041-S0002)). Replace

```markdown
`factory-health` (prints `healthy`, or one line per stop in force), `factory-guard` (run by the agent runtime: refuses an edit outside a role's write paths), `factory-confine`
```

with

```markdown
`factory-health` (prints `healthy`, or one line per stop in force), `factory-confine`
```

Edit 5 (required, Acceptance criteria, criterion 3, a bullet before *Where to look next*). Replace

```markdown
   - *Where to look next* gains one bullet
```

with

```markdown
   - The paragraph that begins "Beside the seven console commands" begins "Beside the six console commands"; the rest of it stays.
   - *Where to look next* gains one bullet
```

Edit 6 (required, Smoke test, first block). Replace

```markdown
grep -c -F -e 'under construction' -e 'groundwork' -e 'probe of 2026-10-17' README.md || true
```

with

```markdown
grep -c -F -e 'under construction' -e 'groundwork' -e 'probe of 2026-10-17' -e 'seven console commands' -e 'factory-guard' README.md || true
```

Edit 7 (required, Smoke test, first block). Replace

```markdown
Expect: four lines, `0`, `7`, `2` and `1` (no inventory, seven command rows,
```

with

```markdown
Expect: four lines, `0`, `6`, `2` and `1` (no inventory, no count of seven and no `factory-guard`, six command rows,
```

### F0038-S0003

Verdict: accepted with edits 1 to 3, all required. The YAML block in *The template* is still stale (no `tool_paths`), and `factory.entry.health` is still undescribed and unindexed. But the index check in the smoke test prints two lines today, `missing: factory.domain.sessions` and `missing: factory.entry.health`: F0030-S0001 added `factory.domain.sessions`, which `processes-and-checks.md` describes (*Starting a process*, **Killing a session.**) but its index line does not name. As drafted, the story's last bullet and its smoke test would fail on that module. F0040-S0003 asks its documenter to index its new modules, but F0040-S0004's docs criterion does not, so `factory.application.agent_home` and `factory.adapters.agent_home` may be missing too (edit 3, depends on F0040-S0004). Smoke blocks today: `1`, `0`; `0`, the two missing lines, `end`.

Edit 1 (required, Description (`factory.domain.sessions`, F0030-S0001, is not in the index either)). Replace

```markdown
except `factory.entry.health` (the console command `factory-health`, the container's health check), and no guide file describes it. The five other modules the review found missing were added since by F0025-S0004 and F0025-S0005. This story adds one paragraph on `factory-health` to `watching.md` and names it on that file's index line.
```

with

```markdown
except two. No guide file describes `factory.entry.health` (the console command `factory-health`, the container's health check). `factory.domain.sessions` (F0030-S0001: one line of the kernel's process table, and what of a session is left to kill) is described in `processes-and-checks.md`, under *Starting a process* (**Killing a session.**), but its index line does not name it. The five other modules the review found missing were added since by F0025-S0004 and F0025-S0005. This story adds one paragraph on `factory-health` to `watching.md`, names it on that file's index line, names `factory.domain.sessions` on the index line of `processes-and-checks.md`, and names any other module that a story merged before this one left out of the index.
```

Edit 2 (required, Acceptance criteria, criterion 3, third bullet). Replace

```markdown
gains `factory.entry.health` before `factory.entry.run`, each in backticks. No other line of the index changes.
```

with

```markdown
gains `factory.entry.health` before `factory.entry.run`, each in backticks. The `processes-and-checks.md` line: "It also names ..." gains `factory.domain.sessions` after `factory.domain.known_results`. No other line of the index changes, but for the modules the next bullet asks for.
```

Edit 3 (required, Acceptance criteria, criterion 3, last bullet (depends on F0040-S0004)). Replace

```markdown
is named in backticks in the index. `make documents` ends with `documents ok`.
```

with

```markdown
is named in backticks in the index. A module that a story merged before this one added without naming it in the index (F0040-S0004's `factory.application.agent_home` and `factory.adapters.agent_home`, if its documenter did not name them) is named on the index line of the guide file that describes it, after the module before it in alphabetical order. `make documents` ends with `documents ok`.
```

### F0038-S0004

Verdict: accepted with edits 1 and 2, both required (they depend on F0027-S0003). Every old text occurs once today, and the first grep prints today `README.md:1`, `agents.md:4`, `costs.md:2`, `git-and-hosting.md:9`, `stages.md:1`, `watching.md:3` and `:0` for the other three. F0027-S0003's docs criterion adds a row to *Which feature uses which operation*: `` `remove_ignored` | F0027: after every agent run and at the restore ``. S0004 renames that table to name parts, not features, and its grep would not see `F0027: `, so the new row would keep a feature id. Two passages that S0004 changes lie in paragraphs that queued stories rewrite: "(R24: no partial figure; ...)" in `agents.md`, *The shared launch module* (F0039-S0001), and `stages.md`'s *Status* sits beside the clauses F0039-S0006 removes. Re-check both quotes before the start.

Edit 1 (required, Acceptance criteria, criterion 3, the `git-and-hosting.md` bullet (depends on F0027-S0003)). Replace

```markdown
"F0023: the key of a known project-command result (S0002) is the tree" → "the known results: the key of a known project-command result is the tree".
```

with

```markdown
"F0023: the key of a known project-command result (S0002) is the tree" → "the known results: the key of a known project-command result is the tree". Every other *Used by* cell that starts with a feature id names the part in its place: F0027-S0003 adds the row of `remove_ignored` with "F0027: after every agent run and at the restore", which becomes "the sealed run and the restore: after every agent run and at the restore".
```

Edit 2 (required, Smoke test, first block (catches a cell such as F0027-S0003's)). Replace

```markdown
|Which feature uses|F0023: ' docs/project-guide/*.md
```

with

```markdown
|Which feature uses|F0023: |\| F00[0-9]{2}: ' docs/project-guide/*.md
```

### F0038-S0005

Verdict: accepted with edit 1, required. The four places exist as drafted (*No `mutants` target, no mutmut* at line 13, *The four documents are checked by a command ...* at 339, the handover entry at 550 with its bullet "- Decision: v1's"), and the three cited titles are headings. The header sentence the story writes says "`CLAUDE.md` names R5 to R13", but `CLAUDE.md` names R3 (the glossary) and R17 (the project guide) as well. The mark form "Superseded by *Title*." matches F0032-S0001's marks. No queued story touches these passages (F0030-S0003 and F0040 add lines to other entries). Smoke block 1 today: `0`, `0`, `0`, `1`, `1`, `1`.

Edit 1 (required, Acceptance criteria, criterion 3, first bullet (`CLAUDE.md` also names R3 and R17)). Replace

```markdown
(`CLAUDE.md` names R5 to R13;
```

with

```markdown
(`CLAUDE.md` names R3, R5 to R13 and R17;
```

### F0038-S0006

Verdict: accepted with edit 2 required (it depends on F0027-S0002 and F0040-S0004) and edit 1 optional. Every quoted old text occurs once; `WE3.3: ` and `WE3.4: ` occur twice each, as the bullet's "its table's cells lose the prefixes" means. The new login-shell sentence matches `login_argv` in `src/factory/adapters/agent_launch.py` (shell, `-c`, script, `factory-login`, token file). F0027-S0002 and F0040-S0004 both write into the table of morning observations and the paragraphs around it; whatever they write with the words "morning observation" is not in S0006's list of replacements, and S0006's first grep would then fail. The guide has 1,480 lines now, not 1,468. S0009 (the second bullet of its edited criterion 3) changes the one citation of "the operator guide's morning observation" in the decision log; the other mentions in the log (lines 312 and 509) are history and stay. Smoke block 1 today: `24`, `0`; the prototype's contents check printed `True True`, and `documents ok`.

Edit 1 (optional, Description (the guide has grown)). Replace

```markdown
and it has 1,468 lines and no contents list.
```

with

```markdown
and it has about 1,500 lines and no contents list.
```

Edit 2 (required, Acceptance criteria, criterion 3, after the bullet on **Morning observations.** (depends on F0027-S0002 and F0040-S0004)). Replace

```markdown
"**Morning observation.**" (under *The hosting-service token*) becomes "**Checks on a running instance.**".
```

with

```markdown
"**Morning observation.**" (under *The hosting-service token*) becomes "**Checks on a running instance.**". Any other "morning observation" or "morning observations" in the guide (F0027-S0002 and F0040-S0004 write into that table and the paragraphs around it) becomes "check on a running instance" or "checks on a running instance", and no row of the table starts with a planning code.
```

### F0038-S0007

Verdict: accepted with edit 3 required (it depends on F0039-S0005) and edits 1 and 2 optional. All twenty names and the five quoted sentences occur today. F0039-S0005's docs criterion removes, in the operator guide, "the clause on `NOT_YET_HANDLED`" and keeps "every kind of event has a handler". The draft's third bullet starts its removal at ", and `NOT_YET_HANDLED`", which will then be gone; the hypothetical "Should a future kind have none, the event leads to this:" and the paragraph after it stay S0007's (F0039-S0005 does not name them). Smoke today: `17`; `2`, `1`.

Edit 1 (optional, Description (F0039-S0005 removes the clause on `NOT_YET_HANDLED` first)). Replace

```markdown
`PullRequestLookupHandler` and `factory.application.handlers.lookups`, and `NOT_YET_HANDLED` in `factory.entry.wiring`. They make the guide longer
```

with

```markdown
`PullRequestLookupHandler` and `factory.application.handlers.lookups` (F0039-S0005 removes the last, `NOT_YET_HANDLED` in `factory.entry.wiring`). They make the guide longer
```

Edit 2 (optional, Description). Replace

```markdown
Beside the last of them stands a hypothetical case written into the current rule:
```

with

```markdown
In *An event that keeps failing* stands a hypothetical case written into the current rule:
```

Edit 3 (required, Acceptance criteria, criterion 3, third bullet (depends on F0039-S0005, which removes the clause the old text starts from)). Replace

```markdown
   - In *An event that keeps failing*, the paragraph on the registered handlers ends "... are registered: every kind of event has a handler.": the text from ", and `NOT_YET_HANDLED`" to the end of the next paragraph ("... A push to the branch makes the factory try again.") is removed.
```

with

```markdown
   - In *An event that keeps failing*, the paragraph on the registered handlers ends "... are registered: every kind of event has a handler.". What follows those words in that paragraph (the hypothetical "Should a future kind have none, the event leads to this:", and any clause on `NOT_YET_HANDLED` that F0039-S0005 left) and the whole next paragraph ("It ends in the one report ... A push to the branch makes the factory try again.") are removed.
```

### F0038-S0008

Verdict: accepted with edits 1 and 2, both required (they depend on F0040-S0002 and F0027-S0003). The three tables are as described (six, fifteen and four rows), and *The stops of the tick* is cited by *The stops* and by lines 29 and 72, so it keeps its heading as drafted. F0040-S0002's docs criterion writes a new `preflight_failed` detail "in *The stops you will see here* or the preflight's section"; if it lands in the six-row table, S0008's list of moved details does not name it. F0027-S0003's docs criterion adds to "the row `checkout_restore_failed`" the cause "an ignored folder the factory cannot empty", and S0008's new tick paragraph keeps only the untracked file or directory. Smoke today: `6`, `1`; five lines `found`.

Edit 1 (required, Acceptance criteria, criterion 3, second bullet (depends on F0040-S0002)). Replace

```markdown
in "The wait for a repository that is not ready". A detail already written there is not written twice.
```

with

```markdown
in "The wait for a repository that is not ready". Any other detail form that a row of the table holds and no other passage holds is kept the same way, in the section *The stops* points to for that stop: F0040-S0002 may write one for `preflight_failed`, `the probe on main could not run: project command lint failed: <sudo> refused the command: ...`, which then goes to "The preflight's items". A detail already written there is not written twice.
```

Edit 2 (required, Acceptance criteria, criterion 3, third bullet (depends on F0027-S0003)). Replace

```markdown
`checkout_restore_failed` comes, for example, from an untracked file or directory the factory cannot remove, and its detail is git's message.
```

with

```markdown
`checkout_restore_failed` comes, for example, from an untracked file or directory the factory cannot remove, or from an ignored folder it cannot empty (F0027-S0003 adds that cause to the table's row), and its detail is git's message.
```

### F0038-S0009

Verdict: rewrite needed; edits 1 to 4 are required and depend on F0040-S0002, F0040-S0004 and F0027-S0003. Today five passages say "left for v2": the operator guide's **Left for v2.** (line 398), `write-guard.md`'s "(left for v2)" (83), and in `docs/decisions.md` the title *The project commands run as the factory's user and are left for v2* (288), "Left for v2." on the agent's home (298) and "Left for v2:" in *The factory alone writes the checkout's `.git`* (444). Line 145 ("a stricter reading for v2") belongs to an entry that F0041 already marked superseded. By the human's answers and the queued stories:

- F0040-S0002 replaces the operator guide's **Left for v2.** paragraph and marks the old entry replaced; S0009's operator-guide bullet goes. Its old title is renamed *The project commands first ran as the factory's user; replaced*, with a line that points to the new entry, and the citations follow (the human's answer 2).
- F0040-S0004 marks "Left for v2." on the agent's home closed; S0009 still points the stale "Open: the kill ... under `sudo`" in the same paragraph to *The agent's own `timeout` kills a run under `sudo` at its time limit* (line 392).
- F0027-S0003 rewrites the undo's *Limits* bullet and, by the human's answer 3, takes out "(left for v2)" (one sentence and one grep added to its docs criterion and smoke test); S0009 does not touch `write-guard.md`.
- Gap 3, the clone's working folder and the process environment, stays: "Left for v2:" at line 444 becomes "Open, not planned".
- The new entry points each closed gap to the entry that closed it (titles from the queued docs criteria) and names the one open gap. Its drafted title, *v2 is retired; what was left for v2 is open*, would now be wrong for four of the five; I propose *v2 is retired; nothing is left for v2* (question 2).

The night-log criterion is dropped, as the human decided. Smoke blocks today (rewritten form): `README.md:0`, `docs/operator-guide.md:1`, `docs/project-guide/write-guard.md:1`, the other guide files `:0`; then `2`, `0`, `1`, `0`, `0`, `0`, `1`, `1`. After the queued stories and S0009 the Expect lines hold. The story's title can stay ("named open and not planned" is still what it does for the one open gap).

Edit 1 (required, Description (the human's answers: four gaps closed by F0040, F0027 and F0041, one open)). Replace

```markdown
Four passages say that a known gap is "left for v2": the operator guide's **Left for v2.** over a security gap (the project commands run agent-written code as the factory's user, who can read the token file), `docs/project-guide/write-guard.md`'s "(left for v2)" on what the undo cannot see, and in `docs/decisions.md` the title *The project commands run as the factory's user and are left for v2* and "Left for v2." on the agent's writable home. On 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009: v1.1 evolves), and the decision log does not record that. The operator reads a known way to leak the token as work already planned, and nothing plans it now. The paragraph on the agent's writable home also still says "Open: the kill of a timed-out agent under `sudo` ... the human has not chosen", which *The agent's own `timeout` kills a run under `sudo` at its time limit* settled on 2026-10-17. This story names each gap open and not planned, records the retirement in one new decision entry, and points the settled question to its entry (finding H6 of the documentation review of 2026-10-20). Whether a gap becomes v1.1 backlog is the human's decision; this story plans none of them.
```

with

```markdown
The documents say of five known gaps that they are "left for v2". On 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009: v1.1 evolves), and the decision log does not record that. By the time this story starts, four of the gaps are closed, each by a story merged before it: the project commands run as the agent user (F0040-S0002, which also replaced the operator guide's **Left for v2.** paragraph and marked the entry *The project commands run as the factory's user and are left for v2* replaced), the agent's home starts fresh before every run (F0040-S0004, which marked the decision log's "Left for v2." on the agent's writable home closed), the git-ignored paths are removed after every agent run (F0027-S0003, which rewrote the undo's *Limits* in `docs/project-guide/write-guard.md` and took out its "(left for v2)"), and the hook and its reading of a payload are gone (F0041). One gap is open and nothing plans it: the checkout's seal does not cover the clone's working folder (the checkout's parent) or the process environment `GitCli` passes on first, which the entry *The factory alone writes the checkout's `.git`* calls "Left for v2:". The paragraph on the agent's writable home also still says "Open: the kill of a timed-out agent under `sudo` ... the human has not chosen", which *The agent's own `timeout` kills a run under `sudo` at its time limit* settled on 2026-10-17. This story records the retirement in one new decision entry, which points each closed gap to the entry that closed it and names the open one "open, not planned"; it takes the words "Left for v2" out of the two paragraphs that still carry them, and points the settled question to its entry (finding H6 of the documentation review of 2026-10-20; the human's answers of 2026-10-20). The entry *The project commands run as the factory's user and are left for v2* gets a plain title that says what it now is, *The project commands first ran as the factory's user; replaced*, and a line that points to *The project commands run as the agent user, with the git folder sealed* (the human, 2026-10-20). The night logs under `docs/runs/` are the human's and stay as they are. Whether the open gap becomes v1.1 backlog is the human's decision; this story plans nothing.
```

Edit 2 (required, Interface). Replace

```markdown
None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes `docs/operator-guide.md`, `docs/project-guide/write-guard.md` and `docs/decisions.md`.
```

with

```markdown
None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/decisions.md`.
```

Edit 3 (required, Acceptance criteria, criterion 3 (depends on F0040-S0002, F0040-S0004 and F0027-S0003)). Replace

```markdown
3. docs:
   - `docs/operator-guide.md`, *The hosting-service token*: "**Left for v2.**" becomes "**Open, not planned.**". The paragraph's last sentence ends with "see *The project commands run as the factory's user; open, not planned* and *v2 is retired; what was left for v2 is open* in `docs/decisions.md`." in place of "see `docs/decisions.md`.". The rest of the paragraph stays.
   - `docs/project-guide/write-guard.md`, *Limits*: "(left for v2)" becomes "(open, not planned)".
   - `docs/decisions.md`: the heading *The project commands run as the factory's user and are left for v2* becomes *The project commands run as the factory's user; open, not planned*. In its text, "is work for v2. Until then the operator guide says so" becomes "is open and not planned since v2 was retired (see *v2 is retired; what was left for v2 is open*). The operator guide says so".
   - `docs/decisions.md`, the paragraph that begins "The agent's home stays writable by the agent": "Left for v2." becomes "Open, not planned.", and the text from "Open: the kill of a timed-out agent under `sudo`." to the end of the paragraph becomes "The kill of a timed-out agent under `sudo` was settled later: see *The agent's own `timeout` kills a run under `sudo` at its time limit*."
   - `docs/decisions.md`, a new last entry `## v2 is retired; what was left for v2 is open`, dated with the story, in the bullet form: Decision: on 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009): v1.1 evolves, and nothing is left for a v2. What the log and the guides left for v2 is open and not planned: the project commands run as the factory's user, who can read the token file; the agent's home stays writable by the agent; the undo does not see ignored paths or anything outside the checkout. Why: a gap named "left for v2" reads as planned work. Open: whether any of the three becomes v1.1 backlog is the human's decision. Rejected: keeping "left for v2" in the documents.
   - No document under `docs/` and no `README.md` says "left for v2" outside the new entry and the citations of its title, and every title the changed passages cite is a heading of the log. `make documents` ends with `documents ok`.
```

with

```markdown
3. docs:
   - `docs/decisions.md`, a new last entry `## v2 is retired; nothing is left for v2`, dated with the story, in the bullet form. Decision: on 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009): v1.1 evolves, and nothing is left for a v2. Of the gaps the log and the guides left for v2, four are closed: the project commands run as the factory's user (*The project commands run as the agent user, with the git folder sealed*), the agent's writable home (*Every agent run and every project command starts from a fresh agent home*), the git-ignored paths the undo did not see (*The factory removes the git-ignored paths after every agent run and at the restore*), and the guard's reading of a hook payload it cannot read, which went with the hook (*The Claude Code hook is removed; the kernel and the undo are the write guard*). One is open and not planned: the checkout's seal does not cover the clone's working folder (the checkout's parent) or the process environment `GitCli` passes on first (*The factory alone writes the checkout's `.git`*). Why: a gap named "left for v2" reads as planned work, and no v2 will come. Open: whether the open gap becomes v1.1 backlog is the human's decision. Rejected: keeping "left for v2" in the documents.
   - `docs/decisions.md`, *The factory alone writes the checkout's `.git`*, the paragraph that begins "Rejected: a sticky bit on the checkout's root": "Left for v2: the clone's working folder" becomes "Open, not planned (see *v2 is retired; nothing is left for v2*): the clone's working folder", and "is the operator guide's morning observation" becomes "is one of the operator guide's checks on a running instance".
   - `docs/decisions.md`, the paragraph that begins "The agent's home stays writable by the agent": "Left for v2.", with any mark F0040-S0004 put beside it, becomes "Closed by *Every agent run and every project command starts from a fresh agent home*.", and the text from "Open: the kill of a timed-out agent under `sudo`." to the end of the paragraph becomes "The kill of a timed-out agent under `sudo` was settled later: see *The agent's own `timeout` kills a run under `sudo` at its time limit*."
   - `docs/decisions.md`, *The project commands run as the factory's user and are left for v2*: the heading becomes `## The project commands first ran as the factory's user; replaced`, and directly under it a paragraph of its own says "Replaced by *The project commands run as the agent user, with the git folder sealed*.", in place of any mark F0040-S0002 wrote in the entry. The rest of its text stays. Every citation of the old title in `docs/decisions.md` (F0040-S0002's entry cites it) cites the new title.
   - No `README.md`, no `docs/operator-guide.md` and no file under `docs/project-guide/` says "left for v2", in any case. `docs/decisions.md` says "Left for v2" nowhere, and "left for v2" only in the new entry's title and text and where a line cites its title. No document cites the old title. Every title that the new and the changed lines cite is a heading of the log. `make documents` ends with `documents ok`.
```

Edit 4 (required, Smoke test, the first three blocks). Replace

````markdown
```bash
grep -c -F -e '**Left for v2.**' -e '(left for v2)' -e 'are left for v2' -e 'Left for v2.' -e 'the human has not chosen' docs/operator-guide.md docs/project-guide/write-guard.md docs/decisions.md README.md || true
```
Expect: four lines, `docs/operator-guide.md:0`, `docs/project-guide/write-guard.md:0`, `docs/decisions.md:0`, `README.md:0`

```bash
f=docs/decisions.md
for t in "The project commands run as the factory's user; open, not planned" 'v2 is retired; what was left for v2 is open' "The agent's own \`timeout\` kills a run under \`sudo\` at its time limit"; do grep -c -x -F "## $t" "$f"; done
grep -c -F '**Open, not planned.**' docs/operator-guide.md
grep -c -F '(open, not planned)' docs/project-guide/write-guard.md
```
Expect: five lines, each `1`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: four lines, `0`, then `docs/decisions.md`, `docs/operator-guide.md` and `docs/project-guide/write-guard.md`
````

with

````markdown
```bash
grep -c -i 'left for v2' README.md docs/operator-guide.md docs/project-guide/*.md || true
```
Expect: eleven lines, each ending in `:0`: `README.md:0`, `docs/operator-guide.md:0`, `docs/project-guide/README.md:0`, `docs/project-guide/agents.md:0`, `docs/project-guide/costs.md:0`, `docs/project-guide/git-and-hosting.md:0`, `docs/project-guide/processes-and-checks.md:0`, `docs/project-guide/stages.md:0`, `docs/project-guide/watching.md:0`, `docs/project-guide/work-items.md:0`, `docs/project-guide/write-guard.md:0`

```bash
f=docs/decisions.md
grep -c -F -e 'Left for v2' -e 'the human has not chosen' -e "the operator guide's morning observation" "$f" || true
grep -c -F "The project commands run as the factory's user and are left for v2" README.md docs/operator-guide.md docs/decisions.md docs/project-guide/*.md | grep -v -c ':0$' || true
for t in 'v2 is retired; nothing is left for v2' "The project commands first ran as the factory's user; replaced" "The agent's own \`timeout\` kills a run under \`sudo\` at its time limit" 'The project commands run as the agent user, with the git folder sealed' 'Every agent run and every project command starts from a fresh agent home' 'The factory removes the git-ignored paths after every agent run and at the restore' 'The Claude Code hook is removed; the kernel and the undo are the write guard' "The factory alone writes the checkout's \`.git\`"; do grep -c -x -F "## $t" "$f"; done
```
Expect: ten lines, `0`, `0`, then eight lines `1` (the old words are gone, no document names the old title, and the new entry, the renamed entry and every title the changed lines cite are headings of the log)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/decisions.md`
````

### F0038-S0010 (new)

Verdict: new story, form `ok`. The folded F0034-S0003 lacks the form's two standing criteria and names six story ids. `git log --format=%s 830029c9.. -- claude/agents/` shows these changes of the bodies outside `## Lessons`: F0016-S0002 (the reviewer's checklist item 6 and the two sentences, already in the guide's count), F0021-S0005 and F0034-S0001 (named today), F0019-S0006 (R14's write-guard sentences in all seven bodies), F0041-S0001 (it took out R14's clause "a hook also refuses an edit outside the write paths"), F0022-S0002 (R15 and `Skill` in `tools`), F0035-S0001 (`intake`'s step 2 sentence on `-q`), F0012-S0017 (check 7's Disk comparison), F0024-S0003 (mutation texts, removed again by F0031-S0001) and F0031-S0001 (check 3 *Mutation testing*, and words in check 7, the recommendation, the proposals paragraph and stage steps 1 and 3). F0016-S0001, F0012-S0011 and F0012-S0028 changed only `## Lessons`. No queued story changes `claude/agents/`. Today `agents.md` names F0021-S0005 and F0034-S0001 and counts "Six passages" twice. It touches the same paragraph as S0004 ("(questionnaire 1, Q29)"), so it runs after S0004; I put it last. Smoke today: `2`; two lines `named`, seven `missing`.

The file, `factory/features/F0038-.../backlog/F0038-S0010-the-project-guide-names-every-passage-of-v1-1-s-own-in-the-shipped-agents.md` (the story moves from `folded/` into `backlog/`; `folded/F0034-S0003-...md` is then removed or kept as the record, the human's choice):

````markdown
# The project guide names every passage of v1.1's own in the shipped agents

## Description

`docs/project-guide/agents.md`, *The seven agents*, says the shipped bodies carry v1's texts, "the sentences are not rewritten in other words", and that "Six passages are v1.1's own text and not v1's". *Replaced from v1* repeats the count ("except the six passages"). The count is short. `git log -- claude/agents/` after `830029c9` (F0010-S0017, which carried v1's texts in) shows more passages of v1.1's own outside `## Lessons`: R14's write-guard sentences in every `## Rules` (F0019-S0006; F0041-S0001 took out its clause on the hook), rule R15 on a project's skills and agents (F0022-S0002), `intake`'s sentence in its *Stage* step 2 on a smoke test that passes `-q` (F0035-S0001), the `acceptance-reviewer`'s comparison of the Disk now line with the previous record in its check 7 (F0012-S0017), and its check 3 *Mutation testing*, "By sweep, not run here", with the words F0031-S0001 changed in its check 7, its recommendation, its proposals paragraph and its stage steps 1 and 3. The guide describes R14, R15 and the `-q` sentence elsewhere, but does not count them as v1.1's own, and it does not mention the acceptance reviewer's check 3 or its disk comparison at all. An agent that changes an agent text reads the guide to learn which sentences are v1's and must keep v1's words; a closed count that the next passage makes wrong tells it wrongly. This story makes the guide list every passage of v1.1's own, each with the story that wrote it, with no count (folded in from F0034-S0003, proposed by the acceptance of F0034). The agent texts, the tests and the other documents stay as they are.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/project-guide/agents.md`. It checks the list against `git log -p 830029c9.. -- claude/agents/` and against the shipped bodies under `claude/agents/` as they are: every sentence there that is not in v1's text and is not under `## Lessons` is one of the passages.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/project-guide/agents.md`, and no other file:
   - *The seven agents*: the sentence "Six passages are v1.1's own text and not v1's." and the two sentences after it (to "... (F0034-S0001).") become one sentence, that the passages below are v1.1's own text and not v1's, and a list with one bullet per passage, each naming the agent or agents, the section, what the passage says in a few words, and the story that wrote it. The list holds: the sentence before the `reviewer`'s checklist, the checklist's sixth item *Earlier tests* and the `acceptance-reviewer`'s added sentence in its check 6 (F0016-S0002); the reviewer's `Notes:` from round 1 on and its added criterion (F0021-S0005); the reviewer's correction of a stale Description, named as `description corrected:` (F0034-S0001); R14's write-guard sentences in every `## Rules` (the kernel refuses every other write, a refused write fails with `Permission denied`, temporary files only in `$TMPDIR`; F0019-S0006, and F0041-S0001 took out the clause on the hook); R15 in every `## Rules` (F0022-S0002); `intake`'s sentence in its *Stage* step 2 on a smoke test that passes `-q` (F0035-S0001); the `acceptance-reviewer`'s comparison of the Disk now line with the previous record in its check 7 (F0012-S0017); its check 3 *Mutation testing* with the words F0031-S0001 changed around it (F0031-S0001); and any other passage the Interface's `git log` shows. No sentence of the guide gives a count of the passages.
   - *Replaced from v1*: "except the six passages of v1.1's own text that *The seven agents* names" becomes "except the passages of v1.1's own text that *The seven agents* lists".
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -E '(Three|Six|Seven|Eight|Nine|Ten|three|six|seven|eight|nine|ten) passages' docs/project-guide/agents.md || true
```
Expect: `0`

```bash
for s in F0016-S0002 F0021-S0005 F0034-S0001 F0019-S0006 F0041-S0001 F0022-S0002 F0035-S0001 F0012-S0017 F0031-S0001; do grep -q -F "$s" docs/project-guide/agents.md && echo "named: $s" || echo "missing: $s"; done
```
Expect: nine lines, `named: F0016-S0002`, `named: F0021-S0005`, `named: F0034-S0001`, `named: F0019-S0006`, `named: F0041-S0001`, `named: F0022-S0002`, `named: F0035-S0001`, `named: F0012-S0017`, `named: F0031-S0001`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/project-guide/agents.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
````

### feature.md

Verdict: edits 1 to 6 are required: the scope follows S0009's new shape and the new S0010, the stories list gains S0010, and the build-order sentence and the folded section say what is decided now. The Goal's "(F0031-S0003 running)" is history; I leave it.

Edit 1 (required, Scope, the operator guide's bullet). Replace

```markdown
, the stop tables (S0008; M1), the token gap named open (S0009; H6).
```

with

```markdown
, the stop tables (S0008; M1).
```

Edit 2 (required, Scope, the project guide's bullet). Replace

```markdown
the planning codes and v1 feature ids in the guide files (S0004; M6).
```

with

```markdown
the planning codes and v1 feature ids in the guide files (S0004; M6), every passage of v1.1's own in the shipped agents (S0010; folded in from F0034-S0003).
```

Edit 3 (required, Scope, the decision log's bullet). Replace

```markdown
the v2 gaps named open and a new entry on v2's retirement (S0009; H6).
```

with

```markdown
a new entry on v2's retirement that points each closed gap to the entry that closed it and names the one open gap, the replaced entry on the project commands renamed *The project commands first ran as the factory's user; replaced*, and the settled kill under `sudo` pointed to its entry (S0009; H6).
```

Edit 4 (required, Stories (the folded story becomes S0010; the order is the human's of 2026-10-20)). Replace

```markdown
The build order; start one at a time, the next when the one before is archived in `done/`. All start after F0032-S0001 is merged (decision 2).
```

with

```markdown
The build order; start one at a time, the next when the one before is archived in `done/`. F0032-S0001 is merged (decision 2); by the human's answers all start after F0037, F0030, F0027, F0041, F0040, F0029-S0003 and F0039 are merged, with a pre-check right before.
```

Edit 5 (required, Stories). Replace

```markdown
- S0009: What was left for v2 is named open and not planned
```

with

```markdown
- S0009: What was left for v2 is named open and not planned
- S0010: The project guide names every passage of v1.1's own in the shipped agents
```

Edit 6 (required, Folded in by the human). Replace

```markdown
The round-2 pre-check before this feature starts takes it up as one more story or as criteria of the guide story it fits.
```

with

```markdown
The fresh pre-check of 2026-10-20 takes it up as S0010, a story of its own: it needs a search of `git log` that S0004's list of exact replacements does not, and it rewrites the sentence of `agents.md` whose neighbour S0004 changes, so it runs after S0004.
```

## Questions for the human

1. **The folded F0034-S0003: a story of its own, or criteria of S0004?** (a) S0010, a story of its own, last in the order. Pro: one documenter task with one `git log` search; S0004 stays a list of exact replacements. Con: one more story run. (b) More criteria in S0004. Pro: one run fewer. Con: S0004 grows from exact replacements to a search, and a slip in either part sends the whole story back. Recommended: (a).
2. **The title of S0009's new decision entry.** (a) *v2 is retired; nothing is left for v2*. Pro: true once F0040 and F0027 are merged, and it says the point. Con: none that I see. (b) The drafted *v2 is retired; what was left for v2 is open*. Con: four of the five gaps are closed by then, so the title would mislead. Recommended: (a).
3. **Who removes "(left for v2)" from `write-guard.md`?** (a) S0009, as edited: it checks the bullet after F0027-S0003 and removes the words only if they are still there. Pro: no queued story changes. Con: S0009's criterion and its file list depend on what F0027-S0003's documenter wrote. (b) Add to F0027-S0003's docs criterion now, before it starts: "the bullet loses '(left for v2)'". Pro: the story that rewrites the bullet finishes it; S0009 only checks. Con: one more edit to a queued story. Recommended: (b), if F0027-S0003 is not started yet; otherwise (a).
4. **The hypothetical handler case in the operator guide: S0007 or F0039-S0005?** (a) S0007 keeps it, as edited. Pro: no queued story changes, and S0007 is about exactly such passages. Con: two stories edit the same paragraph one after the other. (b) Widen F0039-S0005's docs criterion to remove it too. Pro: one edit of the paragraph. Con: one more edit to a queued story, outside F0039's goal. Recommended: (a).
5. **The title of *The project commands run as the factory's user and are left for v2*.** (a) It stays, marked replaced by F0040-S0002. Pro: the replacing entry and the history cite it; a heading of the log is a name. Con: the words "left for v2" stay in one heading. (b) S0009 renames it and every citation. Con: it rewrites a closed entry and its citations for no reader's gain. Recommended: (a); S0009 as edited allows it.

## To re-check right before F0038 starts

- The titles of the entries that S0009's new entry and its smoke test cite: *The project commands run as the agent user, with the git folder sealed* (F0040-S0002), *Every agent run and every project command starts from a fresh agent home* (F0040-S0004), *The factory removes the git-ignored paths after every agent run and at the restore* (F0027-S0003).
- How F0040-S0002 marked the old project-commands entry and where it cites its title (S0009 renames it and the citations), how F0040-S0004 marked "Left for v2." on the agent's home, and that F0027-S0003 took "(left for v2)" out of `write-guard.md` (S0009's first smoke block).
- That F0040-S0002 replaced the operator guide's **Left for v2.** paragraph, and where it wrote the `sudo` refusal of the preflight's `lint` (S0008, S0009).
- The *Used by* cell of `remove_ignored` that F0027-S0003 wrote, and its wording of the `checkout_restore_failed` row (S0004, S0008).
- What F0039-S0005 left of the `NOT_YET_HANDLED` sentence in *An event that keeps failing* (S0007).
- Whether F0027-S0002 or F0040-S0004 wrote "morning observation" anywhere in the operator guide (S0006).
- The quotes of S0004 in `agents.md`, *The shared launch module* (F0039-S0001) and in `stages.md` (F0039-S0006).
- The module index after F0040-S0003 and S0004 (S0003's smoke test), and the console scripts in `pyproject.toml` (S0002: six today).
- Then the smoke greps of every story once more on that `main`, and the form check of all ten.
