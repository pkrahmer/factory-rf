---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 397
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T08:04:01.722312Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T08:04:01.728550Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T08:04:43.932317Z'
  stage: intake
  run: a953bb6566414227bf6cf823d6ea5848
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T08:05:04.826460Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T08:07:48.092291Z'
  stage: tests
  run: 478480fcbc6c46f7883e4e4220924aee
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T08:08:09.659271Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T08:09:58.576483Z'
  stage: doing
  run: 4556aa960c57462ca4d36c5cee8583f1
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T08:10:19.535288Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T08:10:38.549567Z'
  stage: review
  run: 6877e294c0344afbadde5ee1cc5fa13c
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T08:10:59.384393Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T08:11:33.983293Z'
  stage: docs
  run: 11b451fb676544c58afc0123ce9f087c
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-21T08:11:54.916936Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-21T08:12:29.788852Z'
  stage: smoke-test
  run: 668d6cd3817344ffbff3be938c781bc8
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-21T08:12:50.322676Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-21T08:13:22.601303Z'
  stage: doing
  run: cb3c2193ecbf4c85a17e5fd4e2021edb
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-21T08:13:43.521893Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-21T08:14:20.187548Z'
  stage: review
  run: d62974da58874f719db8550ca71841c1
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-21T08:14:40.981389Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-21T08:15:15.738557Z'
  stage: docs
  run: de595fbe148f49389fe1acfc197dbb2b
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-21T08:15:36.645484Z'
  stage: smoke-test
- number: 21
  speaker: smoke-tester
  kind: result
  at: '2026-10-21T08:16:06.684653Z'
  stage: smoke-test
  run: db3a19ca239f41ec90080de51016cfa2
---

# What was left for v2 is named open and not planned

## Description

The documents say of five known gaps that they are "left for v2". On 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009: v1.1 evolves), and the decision log does not record that. Four of the gaps are closed, each by a story merged before this one: the project commands run as the agent user (F0040-S0002, which also replaced the operator guide's **Left for v2.** paragraph and marked the entry *The project commands run as the factory's user and are left for v2* replaced), the agent's home starts fresh before every run (F0040-S0004, which marked the decision log's "Left for v2." on the agent's writable home closed), the git-ignored paths are removed after every agent run (F0027-S0003, which rewrote the undo's *Limits* in `docs/project-guide/write-guard.md` and took out its "(left for v2)"), and the hook and its reading of a payload are gone (F0041). One gap is open and nothing plans it: the checkout's seal does not cover the clone's working folder (the checkout's parent) or the process environment `GitCli` passes on first, which the entry *The factory alone writes the checkout's `.git`* calls "Left for v2:". The paragraph on the agent's writable home also still says "Open: the kill of a timed-out agent under `sudo` ... the human has not chosen", which *The agent's own `timeout` kills a run under `sudo` at its time limit* settled on 2026-10-17. This story records the retirement in one new decision entry, which points each closed gap to the entry that closed it and names the open one "open, not planned"; it takes the words "Left for v2" out of the two paragraphs that still carry them and out of the line of *Every agent run and every project command starts from a fresh agent home* that quotes one of them, and points the settled question to its entry (finding H6 of the documentation review of 2026-10-20; the human's answers of 2026-10-20). The entry *The project commands run as the factory's user and are left for v2* gets a plain title that says what it now is, *The project commands first ran as the factory's user; replaced*, and a line that points to *The project commands run as the agent user, with the git folder sealed* (the human, 2026-10-20). The night logs under `docs/runs/` are the human's and stay as they are. Whether the open gap becomes v1.1 backlog is the human's decision; this story plans nothing.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/decisions.md`, a new last entry `## v2 is retired; nothing is left for v2`, dated with the story, in the bullet form. Decision: on 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009): v1.1 evolves, and nothing is left for a v2. Of the gaps the log and the guides left for v2, four are closed: the project commands run as the factory's user (*The project commands run as the agent user, with the git folder sealed*), the agent's writable home (*Every agent run and every project command starts from a fresh agent home*), the git-ignored paths the undo did not see (*The factory removes the git-ignored paths after every agent run and at the restore*), and the guard's reading of a hook payload it cannot read, which went with the hook (*The Claude Code hook is removed; the kernel and the undo are the write guard*). One is open and not planned: the checkout's seal does not cover the clone's working folder (the checkout's parent) or the process environment `GitCli` passes on first (*The factory alone writes the checkout's `.git`*). Why: a gap named "left for v2" reads as planned work, and no v2 will come. Open: whether the open gap becomes v1.1 backlog is the human's decision. Rejected: keeping "left for v2" in the documents.
   - `docs/decisions.md`, *The factory alone writes the checkout's `.git`*, the paragraph that begins "Rejected: a sticky bit on the checkout's root": "Left for v2: the clone's working folder" becomes "Open, not planned (see *v2 is retired; nothing is left for v2*): the clone's working folder", and "is the operator guide's morning observation" becomes "is one of the operator guide's checks on a running instance".
   - `docs/decisions.md`, the paragraph that begins "The agent's home stays writable by the agent": "Left for v2 (closed on 2026-10-20 by *Every agent run and every project command starts from a fresh agent home*)." becomes "Closed by *Every agent run and every project command starts from a fresh agent home*.", and the text from "Open: the kill of a timed-out agent under `sudo`." to the end of the paragraph becomes "The kill of a timed-out agent under `sudo` was settled later: see *The agent's own `timeout` kills a run under `sudo` at its time limit*."
   - `docs/decisions.md`, *The project commands run as the factory's user and are left for v2*: the heading becomes `## The project commands first ran as the factory's user; replaced`, and directly under it a paragraph of its own says "Replaced by *The project commands run as the agent user, with the git folder sealed*.", in place of F0040-S0002's mark "Replaced on 2026-10-20 by *The project commands run as the agent user, with the git folder sealed* (F0040-S0002). ", which is removed from the start of the paragraph that begins with it (the paragraph then begins "Date: 2026-10-16"). The rest of its text stays. In *The project commands run as the agent user, with the git folder sealed*, "It replaces *The project commands run as the factory's user and are left for v2*." becomes "It replaces *The project commands first ran as the factory's user; replaced*."
   - `docs/decisions.md`, *Every agent run and every project command starts from a fresh agent home*: "It closes the sentence *The agent's home stays writable by the agent (L69) ... Left for v2* of the entry of 2026-10-16." becomes "It closes the sentence on the agent's writable home (L69) in *The agent is started through `sudo -n -u agent -- env -i`, and a run's files are `0640`*."
   - No `README.md`, no `docs/operator-guide.md` and no file under `docs/project-guide/` says "left for v2", in any case (already true before the story; it stays so). `docs/decisions.md` says "Left for v2" nowhere, and "left for v2" only in the new entry's title and text and where a line cites its title. No document cites the old title. Every title that the new and the changed lines cite is a heading of the log. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -i 'left for v2' README.md docs/operator-guide.md docs/project-guide/*.md || true
```
Expect: eleven lines, each ending in `:0`: `README.md:0`, `docs/operator-guide.md:0`, `docs/project-guide/README.md:0`, `docs/project-guide/agents.md:0`, `docs/project-guide/costs.md:0`, `docs/project-guide/git-and-hosting.md:0`, `docs/project-guide/processes-and-checks.md:0`, `docs/project-guide/stages.md:0`, `docs/project-guide/watching.md:0`, `docs/project-guide/work-items.md:0`, `docs/project-guide/write-guard.md:0` (true already before the story, since F0040-S0002 and F0027-S0003; the story must keep it so)

```bash
f=docs/decisions.md
grep -c -F -e 'Left for v2' -e 'the human has not chosen' -e "the operator guide's morning observation" "$f" || true
grep -c -F "The project commands run as the factory's user and are left for v2" README.md docs/operator-guide.md docs/decisions.md docs/project-guide/*.md | grep -v -c ':0$' || true
for t in 'v2 is retired; nothing is left for v2' "The project commands first ran as the factory's user; replaced" "The agent's own \`timeout\` kills a run under \`sudo\` at its time limit" 'The project commands run as the agent user, with the git folder sealed' 'Every agent run and every project command starts from a fresh agent home' 'The factory removes the git-ignored paths after every agent run and at the restore' 'The Claude Code hook is removed; the kernel and the undo are the write guard' "The factory alone writes the checkout's \`.git\`" "The agent is started through \`sudo -n -u agent -- env -i\`, and a run's files are \`0640\`"; do grep -c -x -F "## $t" "$f"; done
```
Expect: eleven lines, `0`, `0`, then nine lines `1` (the old words are gone, no document names the old title, and the new entry, the renamed entry and every title the changed lines cite are headings of the log)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/decisions.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is right for a documents-only story. Nothing under src/, tests/, image/, template/, demo/ or claude/ changes, and the one touched file is named (docs/decisions.md).
   Criteria: criterion 1 (nothing outside docs changes), criterion 2 (make check) and the docs criterion's bullets are each checkable by one grep or diff. I checked the quoted old text against docs/decisions.md on this branch. The headings the new lines cite each exist exactly once. The old entry heading is at line 294. "Left for v2" is at lines 304, 452 and 976, and "left for v2" is at line 958. "Open: the kill of a timed-out agent under `sudo`." is in line 304. "the operator guide's morning observation" is in line 452. The failing side is covered: the old words, and the old title cited anywhere, must be gone (count 0). Three other lines (318, 406, 517) say "morning observation" without the quoted phrase. They are not matched by the criteria or the smoke test, so they stay.
   Smoke test: the commands are runnable. The grep -c over eleven files prints eleven lines. The second block prints 1 + 1 + 9 = eleven lines. The third prints two lines. I read the Expect lines as checkable. No pytest command is involved, so the -q rule does not apply. I did not run make documents.
   Architecture: documents only, so no layer is touched. docs/decisions.md is the documenter's file.
   Scope: it is within F0038's scope (S0009: the new entry, the renamed entry, the settled kill pointed to its entry). It leaves out docs/runs/, write-guard.md and the playbook, as the human's answers of 2026-10-20 say.
4. factory: started tests as self.
5. tester: I wrote no tests. This story only changes documents. Its Interface is "None", and criterion 1 says nothing under `tests/` changes. So none of the criteria has a pytest test.
   - criterion 1 (nothing changes under src/, tests/, image/, template/, demo/ or claude/): no test. It is met because I changed nothing under those paths, including `tests/`. The smoke test's `git diff --name-only origin/main -- src tests image template demo claude` checks it.
   - criterion 2 (`make check` stays green): no test. The factory's checks cover it.
   - criterion 3 (docs, `docs/decisions.md`): no test. The documenter writes it. The smoke test's greps and `make documents` check it.
   Files created: none. Modules the test run could not import: none. `make test` is green and was not red, because there is nothing for the coder to implement. `make lint` is green.

   `lint`: lint: green (0.8 s)
   `test`: test: green (71.3 s)
6. factory: started doing as self.
7. coder: I built nothing. This story only changes documents. Its Interface is "None", and criterion 1 says nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. I changed nothing under those paths, and nothing anywhere else either. `git status --short` shows only the factory's `.costs.jsonl` sidecar.
   - criterion 1: met, because no file changed. The smoke test's `git diff --name-only origin/main -- src tests image template demo claude` checks it.
   - criterion 2: `make check` is green (`test: green (74.6 s)`, `check: green`).
   - criterion 3 (docs): this is the documenter's work in `docs/decisions.md`. I did not write it, as CLAUDE.md says the coder does not.
   Main choice: I left the decision log to the docs stage. The alternative I rejected was editing `docs/decisions.md` here. It is not the coder's file, and the criterion names the documenter.
   Refactor: there is no diff, so there was nothing to refactor.
   Description: no journal entry changed the meaning of the task, so I left it as it is.
   Noticed but not touched: intake found that lines 318, 406 and 517 of `docs/decisions.md` say "morning observation" without the quoted phrase. The criteria leave those lines alone.

   `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   I reviewed `git diff main...HEAD -- . ':!factory'`, which is empty. The only changes on the branch are the work item and its `.costs.jsonl` sidecar under `factory/`. This matches the Interface ("None") and criterion 1: nothing changes under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The tester's entry (5) and the coder's entry (7) each say so. The coder's entry records `check: green`, from the factory's passed result on the tree, which criterion 2 needs. `duplicates: 0 new`.

   Criterion 3 is the documenter's next. I checked its quoted old text against `docs/decisions.md` on this branch, and every quoted text is there:
   - the heading at line 294
   - the mark "Replaced on 2026-10-20 by ... (F0040-S0002). " at the start of line 296
   - "Left for v2 (closed on 2026-10-20 by ...)." and "Open: the kill of a timed-out agent under `sudo`." at line 304
   - "Left for v2: the clone's working folder" and "the operator guide's morning observation" in the "Rejected: a sticky bit" paragraph at line 452
   - the citation of the old title at line 958
   - the "*The agent's home stays writable by the agent (L69) ... Left for v2*" sentence at line 976

   `README.md`, `docs/operator-guide.md` and `docs/project-guide/*.md` already say "left for v2" nowhere. The docs criterion still says what the reader must know after this story. The Description matches what the story is to deliver, and the coder's journal entry gives the main choice (leave the log to the docs stage) and what was rejected.

   Earlier tests: none. The diff changes, renames or deletes no test file that `main` holds.
10. factory: started docs as self.
11. documenter: Changed one file, `docs/decisions.md`, as the docs criterion says:
    - New last entry `## v2 is retired; nothing is left for v2` in the bullet form (Decision, Why, Open, Rejected). It points the four closed gaps to the entries that closed them and names the checkout-seal gap "open and not planned".
    - *The factory alone writes the checkout's `.git`*: "Left for v2:" became "Open, not planned (see *v2 is retired; nothing is left for v2*):", and "the operator guide's morning observation" became "one of the operator guide's checks on a running instance".
    - The paragraph on the agent's writable home: "Left for v2 (closed ...)." became "Closed by *Every agent run ...*.". The "Open: the kill of a timed-out agent under `sudo`" text became a pointer to *The agent's own `timeout` kills a run under `sudo` at its time limit*.
    - The old entry on the project commands is retitled *The project commands first ran as the factory's user; replaced*. Its own paragraph says "Replaced by *The project commands run as the agent user, with the git folder sealed*.", and the mark came off the "Date:" paragraph.
    - *The project commands run as the agent user ...* now cites the new title, and *Every agent run ... fresh agent home* now cites *The agent is started through `sudo -n -u agent -- env -i` ...* instead of the old "Left for v2" sentence.

    Checks I ran: `make documents` ends with `documents ok`. Each of the seven cited existing titles is a heading of the log exactly once. "Left for v2" with a capital L no longer appears in the log. The lowercase "left for v2" appears only in the new entry's title and text and in the *The factory alone writes the checkout's `.git`* citation of it.

    Not run: `make check`, because I changed only a document; the factory's checks follow.

    Cross-read and found current: `README.md`, `docs/operator-guide.md` and `docs/project-guide/*.md`. None says "left for v2", and none cites the old title. I did not open `docs/runs/`, which is the human's.

    Stale but not mine: lines in `docs/decisions.md` that say "morning observation" without the quoted phrase (the intake entry found three; one is in an `init`/reaping entry). The criteria leave them alone. No findings for the coder.

    `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
    `secrets`: secrets: green (1.5 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: I ran the four smoke-test commands from the repository root exactly as written, in order. All four met their `Expect:` lines. When I read the acceptance criteria again, I found one criterion that the commands do not cover and that the smoke test contradicts: the new entry is not dated. That is a finding, so I end with `doing`. I fixed nothing.

    Command 1: `grep -c -i 'left for v2' README.md docs/operator-guide.md docs/project-guide/*.md || true`
    ```
    README.md:0
    docs/operator-guide.md:0
    docs/project-guide/README.md:0
    docs/project-guide/agents.md:0
    docs/project-guide/costs.md:0
    docs/project-guide/git-and-hosting.md:0
    docs/project-guide/processes-and-checks.md:0
    docs/project-guide/stages.md:0
    docs/project-guide/watching.md:0
    docs/project-guide/work-items.md:0
    docs/project-guide/write-guard.md:0
    ```
    Met: eleven lines, each ending in `:0`.

    Command 2: the old-words count, the old-title count, and the nine heading checks in `docs/decisions.md`
    ```
    0
    0
    1
    1
    1
    1
    1
    1
    1
    1
    1
    ```
    Met: `0`, `0`, then nine lines `1`.

    Command 3: `git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs`
    ```
    0
    docs/decisions.md
    ```
    Met.

    Command 4: `make documents 2>&1 | tail -n 1`
    ```
    documents ok
    ```
    Met.

    Reading the criteria again: I read the changed parts of `docs/decisions.md` against each bullet of criterion 3.
    - Line 454 has the "Open, not planned (see ...)" text and "one of the operator guide's checks on a running instance".
    - Line 306 has "Closed by ..." and the pointer to the `timeout` entry.
    - Lines 294–298: the renamed heading, the "Replaced by ..." paragraph on its own line, then "Date: 2026-10-16 ...".
    - Lines 960 and 978 cite the new titles.
    - Lowercase "left for v2" appears only in the new entry (lines 992–997) and at the citation on line 454.

    All of these match. The one exception is the new entry's date (finding 1).

    Findings:
    1. Command: none of the four commands checks this. I found it by reading the criteria again (`sed -n '/^## v2 is retired/,$p' docs/decisions.md`).
       - Expected (criterion 3, first bullet): "a new last entry `## v2 is retired; nothing is left for v2`, dated with the story, in the bullet form". The neighbouring entries put a date line directly under the heading, for example `Date: 2026-10-20 (F0030-S0002). ...` under *The work tree's id copies the index with its timestamps*.
       - Observed: the entry runs from the heading at line 992, through a blank line, straight to `- Decision: on 2026-10-19 v2 was retired ...` at line 994, then the Why, Open and Rejected bullets. It has no `Date:` line and gives no story id anywhere, so it is not dated with the story.
       - Criterion: 3 (docs), first bullet.

    Open: the date line is the documenter's to add in `docs/decisions.md`. After the fix, the smoke test's commands should still give the same output.
14. factory: started doing as self.
15. coder: Round 1: the smoke-tester's one finding is real, but it is in `docs/decisions.md`, and that file is the documenter's to fix, not mine. I changed no file. `git status --short` shows only the factory's `.costs.jsonl` sidecar, and `git diff --name-only main -- src tests image template demo claude` prints nothing.

    - **The finding (criterion 3, first bullet):** I checked it with `sed -n '/^## v2 is retired/,$p' docs/decisions.md`. The new last entry `## v2 is retired; nothing is left for v2` at line 992 goes straight from the heading to `- Decision: ...` at line 994. There is no date line.
    - **What the fix looks like:** the neighbouring bullet-form entries put a paragraph like `Date: 2026-10-20 (F0030-S0002). ...` between the heading and the first bullet (lines 978 and 986). The new entry needs `Date: 2026-10-21 (F0038-S0009).` in that place, with the story's date and id. Nothing else in the entry needs to change, and all four smoke-test commands should still give the same output.
    - **Main choice:** I send the work item forward so the docs stage can add the date line. The alternative I rejected was adding the line myself here: CLAUDE.md says the documenter keeps `docs/decisions.md` and the coder does not write it.
    - **Criterion 1:** still met. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed.
    - **Criterion 2:** `make check` was green on this tree in the earlier round. I did not run it again because nothing it reads has changed; the factory checks after this stage.
    - **Refactor:** there is no diff, so there was nothing to refactor.
    - **Description:** no journal entry changes what the task means, so I left it as it is.
    - **Noticed, not touched:** three other lines in `docs/decisions.md` (318, 406 and 517 by intake's count) still say "morning observation" without the quoted phrase. The criteria leave them alone.

    `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
    `duplicates`: duplicates: 0 new, 38 known, 0 gone
16. factory: started review as self.
17. reviewer: no findings

    I reviewed `git diff main...HEAD -- . ':!factory'`. It changes one file, `docs/decisions.md`. The documenter changed it in the earlier docs stage, and the coder changed nothing in round 1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed, so criterion 1 holds. The journal records `check: green` on this tree (entries 7 and 15), so criterion 2 holds. The Interface is "None", so no rule needs a test. No architecture, security or code-quality point applies to a change that touches only documents.

    I checked the diff against the docs criterion:
    - The old entry has the new heading `## The project commands first ran as the factory's user; replaced`. Under it, a paragraph of its own says "Replaced by ...". The F0040-S0002 mark is gone, and the next paragraph begins "Date: 2026-10-16". The rest of its text is unchanged.
    - *The project commands run as the agent user, with the git folder sealed* cites the new title.
    - The paragraph on the agent's writable home now says "Closed by ...". It points the `sudo` kill question to *The agent's own `timeout` kills a run under `sudo` at its time limit*.
    - The "Rejected: a sticky bit" paragraph says "Open, not planned (see *v2 is retired; nothing is left for v2*)" and "one of the operator guide's checks on a running instance".
    - *Every agent run and every project command starts from a fresh agent home* cites *The agent is started through `sudo -n -u agent -- env -i`, and a run's files are `0640`*.
    - The new last entry is in bullet form. It names the four closed gaps with their entries, and the one gap that is open and not planned.
    - The smoke tester's grep output (entry 13) confirms that the old words and the old title are gone, and that every cited title is a heading.

    Open for the docs stage, not a finding against the coder: the smoke tester's finding in entry 13 still holds on this tree. The new entry `## v2 is retired; nothing is left for v2` (the last entry in `docs/decisions.md`) has no date line, but the docs criterion asks for it to be "dated with the story". The fix is a paragraph `Date: 2026-10-21 (F0038-S0009).` between the heading and the first bullet, as the entries above it have. `docs/decisions.md` is the documenter's file, and the coder cannot write it (entry 15). Sending this back to `doing` would only loop, so I end with `docs`, the stage that writes that line.

    Earlier tests: none. The diff changes, renames or deletes no test file that `main` holds.
18. factory: started docs as self.
19. documenter: Round 1: I fixed the smoke-tester's finding. The new last entry `## v2 is retired; nothing is left for v2` had no date. I changed one file, `docs/decisions.md`: a paragraph `Date: 2026-10-21 (F0038-S0009).` now sits between that heading and the first bullet, in the form of the neighbouring entries. Nothing else in the entry changed, so the four smoke-test commands should give the same output as before. I ran `make documents` and it ends with `documents ok`.

    Cross-read and found current: `README.md`, `docs/operator-guide.md` and `docs/project-guide/*.md`. None says "left for v2" and none cites the old title. I did not open `docs/runs/`, which is the human's.

    Stale but not mine: three lines in `docs/decisions.md` (318, 406 and 517 by intake's count) say "morning observation" without the quoted phrase. The criteria leave them alone.

    No findings for the coder. I did not run `make check`, because I changed only a document. The factory's checks follow.

    `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
    `secrets`: secrets: green (1.5 s)
    `documents`: documents ok
20. factory: started smoke-test as self.
21. smoke-tester: Round 1: I ran the four smoke-test commands from the repository root exactly as written, in order. All four met their `Expect:` lines. I then read the acceptance criteria again against `docs/decisions.md`, and the smoke test contradicts none of them. The finding from the earlier smoke test (entry 13, the new entry had no date) is fixed. No findings, so I end with `approval`. I fixed nothing.

    Command 1: `grep -c -i 'left for v2' README.md docs/operator-guide.md docs/project-guide/*.md || true`
    ```
    README.md:0
    docs/operator-guide.md:0
    docs/project-guide/README.md:0
    docs/project-guide/agents.md:0
    docs/project-guide/costs.md:0
    docs/project-guide/git-and-hosting.md:0
    docs/project-guide/processes-and-checks.md:0
    docs/project-guide/stages.md:0
    docs/project-guide/watching.md:0
    docs/project-guide/work-items.md:0
    docs/project-guide/write-guard.md:0
    ```
    Met: eleven lines, each ending in `:0`.

    Command 2: the old-words count, the old-title count, then the nine heading checks in `docs/decisions.md`
    ```
    0
    0
    1
    1
    1
    1
    1
    1
    1
    1
    1
    ```
    Met: `0`, `0`, then nine lines of `1`.

    Command 3: `git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs`
    ```
    0
    docs/decisions.md
    ```
    Met.

    Command 4: `make documents 2>&1 | tail -n 1`
    ```
    documents ok
    ```
    Met.

    Reading the criteria again (criterion 3, one bullet at a time):
    - New last entry (line 992): `## v2 is retired; nothing is left for v2`, then `Date: 2026-10-21 (F0038-S0009).`, then the Decision, Why, Open and Rejected bullets. It is dated with the story, so the finding from entry 13 is fixed. It names the four closed gaps, each with the entry that closed it, and the checkout-seal gap as "open and not planned".
    - Line 454: "Open, not planned (see *v2 is retired; nothing is left for v2*): the clone's working folder …" and "one of the operator guide's checks on a running instance". Matches.
    - Line 306: "Closed by *Every agent run …*." followed by "The kill of a timed-out agent under `sudo` was settled later: see *The agent's own `timeout` …*." Matches.
    - Lines 294–298: the heading is `## The project commands first ran as the factory's user; replaced`, then the paragraph "Replaced by *The project commands run as the agent user, with the git folder sealed*." on its own, then a paragraph beginning "Date: 2026-10-16". The rest of the text is unchanged. Matches.
    - Line 960 cites the new title, and line 978 cites *The agent is started through `sudo -n -u agent -- env -i`, and a run's files are `0640`*. Both match.
    - In `docs/decisions.md`, lowercase "left for v2" appears only in the new entry (lines 992, 996, 997, 999) and in the citation of its title at line 454. "Left for v2" with a capital L does not appear.

    Criterion 1: met (command 3). Criterion 2: the journal records `check: green` on this tree. I did not run `make check` myself, because the smoke test does not include it.

    Observations (no finding): in the new entry's Decision bullet, the first closed gap reads "the project commands ran as the factory's user", where the criterion's paraphrase says "run". It names the same gap and cites the same entry, so it does not contradict the criterion. Lines 408 and 788 still say "closed on 2026-10-20 by …" and "morning observation". The criteria leave those lines alone.

    Findings: none.
