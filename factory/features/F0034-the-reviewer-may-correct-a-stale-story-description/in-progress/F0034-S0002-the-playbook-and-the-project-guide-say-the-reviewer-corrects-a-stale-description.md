---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 331
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-20T04:15:54.515694Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T04:10:07.264353Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T04:10:07.270666Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T04:10:25.216923Z'
  stage: intake
  run: 4ae475764ccd4370b7542e4f433bc9e2
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T04:10:46.013567Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T04:11:45.967525Z'
  stage: tests
  run: 4729b9ed095a4a68b0b625a693feef3c
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T04:12:06.650571Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T04:13:58.931557Z'
  stage: doing
  run: 5a26f85e1da144969443d3a1b7dfb40f
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T04:14:19.436855Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T04:14:47.993065Z'
  stage: review
  run: c73a274c8f63433d96f9a6f2f76db1d1
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T04:15:09.330803Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T04:15:33.738366Z'
  stage: docs
  run: 1336af79a1ac485280e06ccf29a4ec3f
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T04:15:54.515694Z'
  stage: smoke-test
---

# The playbook and the project guide say the reviewer corrects a stale Description

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0034-S0001 gave the shipped reviewer the rule to rewrite a stale `## Description` itself (`claude/agents/reviewer.md:70`). Its docs criterion named one line of `docs/operator-playbook.md` (section 3, check 2 at approval). Three other places in the playbook still say the edit does not exist yet. Section 3, *Never edit a running story's work item*, says "Until a story gives the reviewer that edit, the correction goes into your answer". The table of section 5 says "the reviewer is to rewrite a stale Description (a story to draft)". The table of section 7 lists "A stale Description corrected through the journal" with the state "a small story to draft". The docs criterion also said the project guide does not describe the reviewer's checklist. Yet `docs/project-guide/agents.md`, *The seven agents*, says "Three passages are v1.1's own text and not v1's", and its renaming table repeats "the three passages". The reviewer's *Role* now holds three more passages of v1.1's own: the `Notes:` paragraph from round 1 on and the added-criterion paragraph (both F0021-S0005), and the Description paragraph (F0034-S0001). This story is for the operator, who reads the playbook at a question, and for the agent who reads the guide before changing an agent text. It brings those five places in line with the shipped reviewer. The agent texts, the tests, the operator guide, the decision log and the playbook's list *What changed against the draft* (a record of the draft, item 17) stay as they are. It changes no behaviour, so it has no criterion beyond the two closing ones.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The documenter checks the text against `claude/agents/reviewer.md`, section *Role* (the paragraphs from `From round 1 on` to `when no stage can fix it.`), and against `docs/decisions.md`, *The reviewer corrects a stale Description*.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/operator-playbook.md`. In section 3, *Never edit a running story's work item*, the bullet on a stale Description says the reviewer rewrites it when the human's answers, the Interface or the criteria settle what it should say (F0034), and names each correction in its entry as `description corrected:`. An answer that settles the meaning is therefore enough; it no longer says "Until a story gives the reviewer that edit". In the table of section 5, the row "A push to a work item's branch, to fix its Description, refused" ends with "the reviewer rewrites a stale Description (F0034)" in place of "(a story to draft)". In the table of section 7, the row "A stale Description corrected through the journal" has the state `built (F0034, the reviewer may correct a stale story Description)`. Item 17 of *What changed against the draft* stays as it is. `docs/project-guide/agents.md`, *The seven agents*: the sentence "Three passages are v1.1's own text and not v1's" names, beside the three it lists, the reviewer's three *Role* paragraphs of v1.1's own: the `Notes:` from round 1 on and the added criterion (F0021-S0005), and the correction of a stale Description (F0034-S0001). The renaming table's "except the three passages" gives the same count. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, since F0034-S0001 already wrote them.

## Smoke test

```bash
p=docs/operator-playbook.md
for s in 'Until a story gives the reviewer that edit' '(a story to draft) |' 'corrected through the journal | the reviewer may rewrite a stale Description | a small story to draft'; do grep -qF -e "$s" "$p" && echo "still: $s" || echo gone; done
```
Expect: three lines `gone`

```bash
grep -c -F 'built (F0034, the reviewer may correct a stale story Description)' docs/operator-playbook.md
```
Expect: `1`

```bash
grep -c -F 'Three passages are v1.1' docs/project-guide/agents.md; grep -c -F 'F0034-S0001' docs/project-guide/agents.md
```
Expect: two lines, `0` (the count of three is gone) and a number of at least `1` (the guide names the Description paragraph's story)

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no module under src/ changes. The story names the files and sections it reads (claude/agents/reviewer.md *Role*, docs/decisions.md). No behaviour is stated there, so no rule needs a criterion.
   Criteria: only the two closing ones, `make check` and `docs:`. The docs criterion names each edit by file, section and exact wording: the section 3 bullet, the section 5 row, the section 7 row, the two counts in agents.md, and item 17 left unchanged. This is a documentation-only story and states no rule with a failing side.
   Smoke test: runnable. I grepped the current files and each searched string exists today: playbook lines 50, 127 and 148, and agents.md lines 248 and 305. The three commands therefore show a change after the edit. Each Expect line is checkable: three `gone` lines, `1`, and `0` plus a count of at least 1.
   Architecture: documents only, within the documenter's write paths (README.md, docs/*). The playbook is named by the docs criterion, as CLAUDE.md *Docs* allows. No layer is touched.
   Scope: within F0034's goal of bringing the docs in line with the reviewer's new rule. The out-of-scope items (agent texts, tests, decisions, archived stories) are respected, and item 17 stays as it is. Two things to note. The feature's Scope and Stories lists name only S0001 and the playbook; agents.md and S0002 are not in them. S0002 was proposed by the acceptance reviewer and reached backlog through the human's merge, so I took it as approved. I did not ask.
4. factory: started tests as self.
5. tester: No tests written. The Interface says no module under src/factory/ changes and the tester writes no test module. This story only changes documents, so no criterion has an executable form.
   criterion 1 (`make check` stays green): no test of its own. The factory's checks cover it.
   criterion 2 (docs: operator-playbook.md sections 3/5/7, project-guide/agents.md *The seven agents*): no test. The documenter writes it, and the docs stage's `make documents` and the story's smoke test check it.
   Files created: none.
   Modules the test run could not import: none. No new test exists, so the branch has no red tests and the existing suite is unchanged.
   `make lint`: green. I did not run `make test`, because no test changed and the factory runs it after this stage. Nothing was interpreted and nothing is open.

   `lint`: lint: green (0.0 s)
   `test`: test: green (45.9 s)
6. factory: started doing as self.
7. coder: Built nothing. The story only changes documents. The Interface says no module under `src/factory/` changes and that there is no test module. Its one substantive criterion is the docs criterion, covering `docs/operator-playbook.md` sections 3, 5 and 7 and `docs/project-guide/agents.md` *The seven agents*. Under CLAUDE.md *Docs*, the documenter stage writes those files, not the coder, so I left the working tree as it was.
   Main choice: hand forward with no change. The alternative I rejected was editing the playbook and agents.md here. That would take on the documenter's work, and those files are not mine to write in this stage.
   Refactor: no diff of mine, so nothing to change.
   `make check`: green (`test: green (40.4 s)`, `check: green`).
   Noticed but did not touch: as intake noted, the feature's Scope and Stories lists do not name this story or agents.md. That is the feature's `feature.md`, which is the human's file.
   Description: no journal entry changed its meaning.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and adds its `.costs.jsonl` sidecar, both under `factory/`. This is a documentation-only story. Its one substantive criterion is the docs criterion, and the documenter stage writes that next. CLAUDE.md *Docs* says the coder does not write those documents, so a coder who changed nothing is correct here.

   Checklist:
   1. Acceptance criteria: criterion 1 (`make check` stays green) holds. The coder's entry 7 records `check: green` from the factory. Criterion 2 is the docs criterion and is the documenter's to fulfil. The Interface states no rule or limit, so no failing side needs a test.
   2. to 4. Architecture, security, quality: there is no diff under `src/` or anywhere outside `factory/`, so there is nothing to check. The factory's `duplicates: 5 new` record cannot come from this diff, which touches no code.
   5. Work item hygiene: entry 7 explains the main choice (hand forward with no change) and the rejected alternative (editing the docs in the doing stage). I compared the Description and the docs criterion with the files they name. All five places still read as the Description says:
      - `docs/operator-playbook.md:50`, `:127` and `:148`
      - `docs/project-guide/agents.md:248` and `:305`
      The three *Role* paragraphs the docs criterion names are at `claude/agents/reviewer.md:66`, `:68` and `:70`. So the criterion still tells the documenter what to write.
   6. Earlier tests: the diff changes no test file. None needed.
10. factory: started docs as self.
11. documenter: Files changed:
    - `docs/operator-playbook.md`: three edits.
      - Section 3, the bullet on a stale Description, now says the reviewer rewrites it when the human's answers, the Interface or the criteria settle it (F0034). It says an answer is enough, and that the reviewer names each correction as `description corrected:`. "Until a story gives the reviewer that edit" is gone.
      - The section 5 row on the refused push now ends with "the reviewer rewrites a stale Description (F0034)" in place of "(a story to draft)".
      - The section 7 row "A stale Description corrected through the journal" now has the state `built (F0034, the reviewer may correct a stale story Description)`.
    - `docs/project-guide/agents.md`, *The seven agents*: "Three passages are v1.1's own text" is now "Six passages". The three listed ones stay. The other three are the reviewer's *Role* paragraphs: the `Notes:` from round 1 on, the added criterion (F0021-S0005), and the correction of a stale Description (F0034-S0001). The smoke test expects the count of three to be gone, so I rewrote the sentence's opening. The criterion's wording would have kept it.
    - `docs/project-guide/agents.md`, *Replaced from v1*: the renaming table's lead-in now says "except the six passages", the same count.

    Not changed: item 17 of *What changed against the draft*, as the criterion says. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, since F0034-S0001 already wrote them.

    I checked the new text against `claude/agents/reviewer.md`, *Role*, lines 66 to 70. I ran the smoke-test greps: the three old strings are gone, the new section 7 state appears once, and `Three passages are v1.1` appears 0 times in `agents.md`. I ran `make check` neither before nor after the edits.

    Cross-read and found current: `README.md`, `docs/operator-guide.md`, `docs/decisions.md` (*The reviewer corrects a stale Description*). `agents.md` has no other mention of the old count.

    Stale text I saw but did not touch: none. Findings: none.

    `check`: check: green (not run again: passed on tree 450879e8d6a9 at 2026-10-20T04:13:05Z)
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
