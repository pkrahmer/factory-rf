---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 590
comments_read: [6682263635]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-06T10:05:19.372924Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T10:00:36.456939Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T10:00:36.463722Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T10:00:56.128360Z'
  stage: intake
  run: 3462562d1fcb42cf8e6226b61bb41de2
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T10:04:48.570677Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T10:04:51.115348Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T10:05:13.942470Z'
  stage: intake
  run: 820e3ea30f8c40c7baa7940b99b07a3e
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T10:05:19.372924Z'
  stage: tests
---

# The agents write and review documents against the code

## Description

The checks catch names, settings and examples; the rest of a document's truth depends on how the agents work. Today a documenter writes from the story and the old text, and a reviewer reads the diff of the code, not the documents. This story changes their instructions: the documenter reads the code it describes before it writes a sentence about it, writes every command it shows as a runnable example (or marks it for the VM, GitHub or a model, and then copies it from a real run and says where it ran), runs `make documents`, and keeps exact detail in a *Reference* section rather than cutting it. The reviewer reads the changed documents against the code, and counts a claim it cannot find in the code, and a command shown without a runnable or marked example, as findings. The style rules of `planning/doc-style-drafts.md` (rules 8 to 10) become theirs.

## Interface

- `agents/agents/documenter.md`: one rule each for: read the code first; examples are runnable, or marked and copied from a real run that the text names; keep detail in *Reference*; run `make documents` and end only on `documents ok`.
- `agents/agents/reviewer.md`: in its checklist, an item *Documents*: the changed documents' claims against the code, and examples runnable or marked; a failure is a finding.
- `agents/agents/intake.md`: a docs criterion that dictates sentences is a question; it should name what the reader must know.
- Tests of the agent texts: `tests/agent_files/test_claude_agent_texts_documents.py`, one row per rule. The human's leave (2026-11-05): the tester may change the earlier tests that pin an agent file's whole text (such as `test_the_rest_of_the_reviewer_body_is_unchanged` in `tests/agent_files/test_claude_agent_texts_review_groups.py`) so that they leave out the new rules' lines, as F0052-S0002 did for its `### docs-review` subsection; each keeps its name and pins the rest as before.

## Acceptance criteria

1. `agents/agents/documenter.md` has the rule "read the code first": the documenter reads the code it describes before it writes a sentence about it (rule 8, facts from the code).
2. `agents/agents/documenter.md` has the rule that detail is kept in a *Reference* section and not cut (rule 9).
3. `agents/agents/documenter.md` has the rule that every example is runnable, or marked for the VM, GitHub or a model and then copied from a real run that the text names (rule 10, real or marked values).
4. `agents/agents/documenter.md` has the rule that the documenter runs `make documents` and ends only on `documents ok` (rule 10).
5. `agents/agents/reviewer.md` has the item *Documents* (heading `### Documents`) in its checklist, naming the changed documents' claims against the code and the examples.
6. `agents/agents/reviewer.md` names a claim it cannot find in the code as a finding.
7. `agents/agents/reviewer.md` names a command shown without a runnable or marked example as a finding.
8. `agents/agents/intake.md` makes a docs criterion that dictates the sentences to write a question, and says the criterion names what the reader must know afterwards.
9. `agents/agents/intake.md` tells the agent to end with `question` for such a criterion.
10. `make check` stays green.
11. docs: `docs/project-guide/agents.md`: how the documenter and the reviewer treat documents. `docs/decisions.md`: an entry, naming F0053 and the human's concern of 2026-11-05 that the stages' documents were not reliably true.

## Smoke test

```bash
grep -q "documents ok" agents/agents/documenter.md && grep -q "### Documents" agents/agents/reviewer.md && echo named
```
Expect: `named`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed, so none from it):

   1. Criterion 2 does not state the failing side. The Interface says "a failure is a finding" and the Description says the reviewer counts a claim it cannot find in the code, and a command shown without a runnable or marked example, as findings. Should criterion 2 say that `reviewer.md` names both as findings? I would choose yes: split it into the item's presence and the two findings, each testable by one row.
   2. The Description says rules 8 to 10 of `planning/doc-style-drafts.md` become the agents' rules, and no criterion tests that. The Interface's four documenter rules (read the code first; runnable or marked examples copied from a named real run; detail kept in *Reference*; `make documents` run, end only on `documents ok`) are not the same as "rules 8 to 10". Do the four rules cover rules 8 to 10, or does a rule need its own criterion? I would choose to state in the criteria that the four rules are rules 8 to 10 (or drop that sentence from the Description).
   3. Criterion 3 is cut off ("the rule on a docs criterion that dictates sentences, ."). I read it as: `intake.md` makes a docs criterion that dictates sentences a question, and says the criterion should name what the reader must know. Please confirm that wording, or correct it. The behaviour has no failing-side criterion either: should one row test that `intake.md` tells the agent to end with `question` for such a criterion?
   4. The smoke test only counts the string "make documents" in `documenter.md`. That passes before the story if the string is already there, and it checks none of the other rules. Please give an `Expect:` that the story changes: for example grep for `documents ok` in `documenter.md`, and for the *Documents* item in `reviewer.md`.

   Scope and architecture are fine: the Interface changes only agent files under `agents/agents/` and the tests under `tests/agent_files/`, which fits the documented layout. The human's leave to change the whole-text pinning tests is stated. Route would be `tests`.
4. 2026-11-06 human: 1. Yes: split criterion 2. One row for the *Documents* item in `reviewer.md`, one row that it names a claim it cannot find in the code as a finding, and one row that it names a command shown without a runnable or marked example as a finding.
   2. The four rules are rules 8 to 10, split by task: rule 8 (facts from the code) is "read the code first"; rule 9 (keep the detail in a *Reference* section) is "detail kept in *Reference*"; rule 10 (every example run with real or marked values) is "runnable or marked examples, copied from a named real run" plus "run `make documents` and end only on `documents ok`". Say so in the criterion, one row per rule; the Description's sentence then holds.
   3. Confirmed: `intake.md` makes a docs criterion that dictates the sentences to write a question, and says the criterion names what the reader must know afterwards. Yes to the failing-side row: such a criterion ends the intake with `question`.
   4. Yes: `grep -q "documents ok" agents/agents/documenter.md && grep -q "### Documents" agents/agents/reviewer.md && echo named` with `Expect: named`, or the exact heading the tester gives the *Documents* item, so that the smoke test fails before the story.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) carried into the story.
   - Interface: concrete. It names `agents/agents/documenter.md`, `reviewer.md` and `intake.md`, and the test file `tests/agent_files/test_claude_agent_texts_documents.py`. The human's leave to change the whole-text pinning tests is stated.
   - Criteria: I rewrote the list from entry 4. Answer 1 splits the reviewer criterion into the *Documents* item, a claim not found in the code as a finding, and a command without a runnable or marked example as a finding. Answer 2 splits the documenter's rules by task, one criterion each: rule 8 is read the code first, rule 9 is *Reference*, rule 10 is runnable or marked examples copied from a named real run, and rule 10 also covers `make documents` ending on `documents ok`. Answer 3 repairs the cut-off intake criterion and adds a row for ending with `question`. The two closing criteria stay last. Each is now testable by one row, and each rule has its failing side. The Description is unchanged: its rules 8 to 10 sentence now holds.
   - Smoke test: replaced by the grep from answer 4 (`documents ok` in `documenter.md` and `### Documents` in `reviewer.md`, then `echo named`). It fails before the story and is runnable. `Expect: named` is checkable. It runs no pytest.
   - Architecture: the Interface changes only agent files and tests under `tests/agent_files/`, which fits the layout in CLAUDE.md.
   - Scope: within F0053's "the agents' rules" scope. Nothing in Out of scope is touched. `factory/story-form.md` is a human change at merge and is not part of this story.
   Route: `tests`, since the Interface changes `agents/agents/`, which the documenter may not write.
7. factory: started tests as vm.
