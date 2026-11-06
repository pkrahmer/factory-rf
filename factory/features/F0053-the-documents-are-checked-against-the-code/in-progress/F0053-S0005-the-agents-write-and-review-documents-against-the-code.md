---
stage: doing
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 590
comments_read: [6682263635]
handed_over: null
claim: null
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
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-06T10:06:55.357047Z'
  stage: tests
  run: 703f8042058e417490395d077318ac88
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T10:07:00.691412Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-06T10:08:48.246744Z'
  stage: doing
  run: 657966f167a54bf299ed91152ebecf46
  blocked: question
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
8. tester: Tests written for the agent texts. Each criterion's test looks for one paragraph (one non-blank line of the agent file, compared case-insensitively) that names the criterion's key words. The tests do not pin wording, because the Interface gives none.

   - criterion 1: tests/agent_files/test_claude_agent_texts_documents.py::test_the_documenter_has_one_rule_for_each_way_a_document_stays_true[read-the-code-first] (read, code, before, sentence)
   - criterion 2: …::test_the_documenter_has_one_rule_for_each_way_a_document_stays_true[detail-kept-in-reference] (`*Reference*`, cut)
   - criterion 3: …::test_the_documenter_has_one_rule_for_each_way_a_document_stays_true[runnable-or-marked-examples] (runnable, marked, VM, GitHub, model, real run)
   - criterion 4: …::test_the_documenter_has_one_rule_for_each_way_a_document_stays_true[make-documents-ends-on-ok] (`` `make documents` ``, `` `documents ok` ``)
   - criterion 5: …::test_the_reviewer_checklist_has_a_documents_item_naming_claims_against_code_and_examples. The reviewer's `## Role` holds exactly one `### Documents` heading, and its text up to the next heading names claim, code and example.
   - criterion 6: …::test_the_reviewer_documents_item_counts_an_untrue_document_as_a_finding[claim-not-in-the-code] (claim, cannot find, code, finding, inside the Documents item)
   - criterion 7: …::test_the_reviewer_documents_item_counts_an_untrue_document_as_a_finding[command-without-example] (command, runnable, marked, finding, inside the Documents item)
   - criterion 8: …::test_the_intake_asks_about_a_docs_criterion_that_dictates_sentences[dictated-sentences-are-a-question] (docs criterion, sentences, question, what the reader must know)
   - criterion 9: …::test_the_intake_asks_about_a_docs_criterion_that_dictates_sentences[ends-with-question] (docs criterion, sentences, end with `question`)
   - criteria 10 and 11: not tested here (the `make check` gate and the docs stage).

   Files created: tests/agent_files/test_claude_agent_texts_documents.py.

   Earlier test changed under the human's leave in the Interface (2026-11-05): tests/agent_files/test_claude_agent_texts_review_groups.py::test_the_rest_of_the_reviewer_body_is_unchanged.
   - It now also strips the new `### Documents` item before checking the CRC. A new regex `_DOCUMENTS_ITEM` removes the text from that heading up to the next heading, or up to the paragraph "Write findings as a numbered list".
   - The coder should put the item after checklist item 6 and before that paragraph, with blank lines around it. Otherwise the CRC pin fails.
   - The test keeps its name and still pins the rest of the reviewer's body.

   Run: `uv run pytest -q` on the two files. All nine rows of the new file fail because the agent texts do not hold the rules yet; the tail showed the reviewer and intake rows. A grep confirmed that no paragraph of documenter.md holds the documenter rows' words. The changed CRC test passes. No module failed to import, because the tests read only agent files. `make lint` is green.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: Question: three tests on `agents/agents/reviewer.md` leave no place for the `### Documents` item. I stopped before `make check`.

    Where I stopped. The new rules are written in the working tree:
    - `agents/agents/documenter.md`, Role: three new bullets.
      - Read the code first.
      - Every example is runnable, or marked for the VM, GitHub or a model and copied from a real run the text names.
      - Exact detail is kept in a *Reference* section, not cut.
      - The bullet's old sentence "Examples are runnable and were run." went into the examples bullet.
    - `agents/agents/documenter.md`, Stage step 3: it now runs `make documents` and ends only on `documents ok`.
    - `agents/agents/intake.md`: a new step 4. A docs criterion that dictates the sentences to write is a question, and the agent ends with `question`. The criterion names what the reader must know afterwards. Steps 4 to 6 became 5 to 7, and "steps 2 to 4" became "steps 2 to 5".
    - `agents/agents/reviewer.md`: the `### Documents` item, with three paragraphs: the changed documents' claims against the code; a claim you cannot find in the code is a finding; a command without a runnable or marked example is a finding.

    Every row of `tests/agent_files/test_claude_agent_texts_documents.py` passes. One earlier test fails.

    The contradiction. In `## Role`, the item can only go where `_DOCUMENTS_ITEM` (the CRC test in `test_claude_agent_texts_review_groups.py`) strips exactly the item. That regex removes text from the heading up to the next line starting with `#` or `Write findings as a numbered list`. So the item must sit either just before the "Write findings" paragraph or just before `## Stage`. Two earlier tests pin both spots:
    1. Just before "Write findings", after item 6 (where the tester said to put it, and where it is now): `tests/agent_files/test_claude_agent_texts_mutants.py::test_reviewer_item_6_is_followed_by_the_findings_paragraph` fails. It needs the line after item 6's blank line to start with "Write findings" (AssertionError at line 85: `'### Documents'.startswith(...)`).
    2. At the end of Role, before `## Stage`: `tests/agent_files/test_claude_agent_texts_description.py::test_description_correction_sits_between_added_criterion_and_stage[before-stage]` fails. It needs "when no stage can fix it.\n\n## Stage".

    Anywhere else in Role, the regex strips too much and the CRC pin fails. I cannot edit tests, and the Interface's leave covers tests that pin an agent file's whole text. These two pin positions, so the leave does not clearly cover them.

    Options:
    - (a) Keep the item after item 6, inside the checklist as criterion 5 says. The tester changes `test_reviewer_item_6_is_followed_by_the_findings_paragraph` so that it skips a `### Documents` item between item 6 and "Write findings", keeping its name and what it checks. **I would choose (a).** It puts the item in the checklist, and the tester's CRC regex was written for that spot.
    - (b) Put the item at the end of Role. The tester changes the `before-stage` row to allow the `### Documents` item between the correction paragraph and `## Stage`.
    - (c) Make the item a numbered checklist item 7 instead of a heading. That contradicts criterion 5 (`### Documents`) and the new tests.

    With (a) or (b), I would end with `tests` naming that one change. Then `make check` is run once the test is changed.

    Noticed, not touched: `make documents` ends with `documents ok (<seconds> s)`, per `docs/runs/2026-11-05-f0052/log.md`. The documenter's rule says to end on its last line `documents ok`, which holds for that format.
