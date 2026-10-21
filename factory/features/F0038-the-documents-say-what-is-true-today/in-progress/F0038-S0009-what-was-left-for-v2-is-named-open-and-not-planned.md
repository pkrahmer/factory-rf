---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 397
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-21T08:10:59.384393Z'
  lease_duration: 60
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
