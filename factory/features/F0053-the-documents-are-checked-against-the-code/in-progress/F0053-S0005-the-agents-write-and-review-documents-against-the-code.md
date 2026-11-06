---
stage: review
blocked: round_cap
round: 3
attempts: 0
crashes: 0
pull_request: 590
comments_read: [6682263635, 6682414078]
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
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-06T10:12:40.129536Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T10:12:42.698016Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-06T10:13:40.098358Z'
  stage: doing
  run: f294d23edf764475ba858b55d95c148a
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-06T10:13:45.158942Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-06T10:14:16.473517Z'
  stage: tests
  run: 193c4150145843dc8eba9a8f9a0f1ef7
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-06T10:14:21.724845Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-06T10:18:42.014979Z'
  stage: doing
  run: b3bf2982628345c5915874ddc7a156ad
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-06T10:18:47.441792Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-06T10:20:50.914764Z'
  stage: review
  run: b9ed440a59b343b186897dfbbece4a6d
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-06T10:20:56.347380Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-06T10:23:36.034094Z'
  stage: doing
  run: 35ae9d605270462cba57528558d2bb90
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-06T10:23:41.549883Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-11-06T10:24:21.072795Z'
  stage: tests
  run: 45e7aca838364211a30ef8f7cfe1b6e6
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-06T10:24:26.291992Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-11-06T10:28:52.578663Z'
  stage: doing
  run: 7695aba45c9540d8bb01bf4fbf01e522
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-06T10:28:57.982898Z'
  stage: review
- number: 27
  speaker: reviewer
  kind: result
  at: '2026-11-06T10:30:21.785931Z'
  stage: review
  run: 396ee71df20e4b729345dfdce1ebee27
- number: 28
  speaker: factory
  kind: started
  at: '2026-11-06T10:30:27.338290Z'
  stage: doing
- number: 29
  speaker: coder
  kind: result
  at: '2026-11-06T10:35:12.210695Z'
  stage: doing
  run: d74f05cd7f7c4fd08b189354c5462c28
- number: 30
  speaker: factory
  kind: started
  at: '2026-11-06T10:35:17.553856Z'
  stage: review
- number: 31
  speaker: reviewer
  kind: result
  at: '2026-11-06T10:36:33.346048Z'
  stage: review
  run: 41500be8fceb48bd9cf2f759b64ac1d9
- number: 32
  speaker: factory
  kind: question
  at: '2026-11-06T10:36:33.346048Z'
  stage: review
  run: 41500be8fceb48bd9cf2f759b64ac1d9
  blocked: round_cap
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
11. 2026-11-06 human: (a), with the human's leave: end with `tests`. The tester changes `tests/agent_files/test_claude_agent_texts_mutants.py::test_reviewer_item_6_is_followed_by_the_findings_paragraph` so that a `### Documents` item between item 6 and the "Write findings" paragraph is skipped. It keeps its name and what it checks, and nothing else in that module changes. The entry names it. The item stays in the checklist after item 6.
    On the last line: say "ends with `documents ok (<seconds> s)`" in `documenter.md`, so that the rule names the line exactly as `make documents` prints it.
12. factory: started doing as vm.
13. coder: Test change for the tester, with the human's leave (journal entry 11, option a): change `tests/agent_files/test_claude_agent_texts_mutants.py::test_reviewer_item_6_is_followed_by_the_findings_paragraph` so that it skips a `### Documents` item between checklist item 6 and the "Write findings as a numbered list" paragraph. It keeps its name and what it checks, and nothing else in that module changes.

    What I did in this run:
    - I carried in the human's second answer from entry 11. Step 3 of `agents/agents/documenter.md` now reads: run `make documents` after the last edit, and end only when its last line is `documents ok (<seconds> s)`. That is the line exactly as `make documents` prints it.
    - I kept the literal `` `documents ok` `` in the same sentence ("without `documents ok` there, the documents are not done"). The `make-documents-ends-on-ok` row of `tests/agent_files/test_claude_agent_texts_documents.py` looks for that string with its backticks, and the human did not ask to change that row.
    - I left everything else from the previous run as it was:
      - `documenter.md`: three new Role rules (read the code first; runnable or marked examples copied from a named real run; detail kept in *Reference*) and the `make documents` step.
      - `intake.md`: the new step 4, with the later steps renumbered.
      - `reviewer.md`: the `### Documents` item, after item 6 and before "Write findings".

    Main choice: one sentence holds both the exact printed line and the literal the test looks for. I rejected asking the tester to loosen the `make-documents-ends-on-ok` row, because the human named only the mutants test.

    State: `uv run pytest -q tests/agent_files` has one failure, the mutants test named above (AssertionError at line 85, `'### Documents'.startswith(...)`). All other tests in that folder pass. I did not run `make check` because that test is still red. It should be run once the tester has made the change.

    Refactor: I re-read the diff against `main` for `agents/` and found nothing to change.

    Description: entry 11 does not change the meaning of the task, so it stays as it is.
14. factory: started tests as vm.
15. tester: I made the test change the human approved in entry 11 (option a), which the coder named in entry 13. It is in `tests/agent_files/test_claude_agent_texts_mutants.py::test_reviewer_item_6_is_followed_by_the_findings_paragraph`, a test another story wrote.

    - The test still finds checklist item 6 and still requires a blank line after it.
    - If the next line is `### Documents`, the test now skips that item. The item is its heading, one blank line, its non-blank paragraph lines and the blank line after them. If the item's shape is different, the test fails.
    - Either way, the next line must still start with "Write findings as a numbered list in your entry".
    - The test keeps its name and still checks the same thing. Nothing else in that module changed.

    Why: the human put the `### Documents` item in the reviewer's checklist, after item 6 and before the "Write findings" paragraph. The old test required "Write findings" to follow item 6 directly.

    Files created: none. File changed: `tests/agent_files/test_claude_agent_texts_mutants.py`, with the human's leave (entry 11).

    Run: `uv run pytest -q tests/agent_files/test_claude_agent_texts_mutants.py`, 21 passed, including the changed test against the coder's `reviewer.md`. There were no import failures, because these tests read only the agent files. `make lint`: lint: green (0.2 s).

    Open: the coder's `make check` has not run yet. It should now run without this failure.

    `lint`: lint: green (0.1 s)
16. factory: started doing as vm.
17. coder: `make check` passes (`check: green`, `test: green (104.3 s)`, coverage 99.22 %). The tester's change to `tests/agent_files/test_claude_agent_texts_mutants.py::test_reviewer_item_6_is_followed_by_the_findings_paragraph` (entry 15) fixed the one failure left from entry 13. Every row of the new `tests/agent_files/test_claude_agent_texts_documents.py` passes.

    What I built (my earlier runs, entries 10 and 13; this run changed no file):
    - `agents/agents/documenter.md`, Role: three new rules.
      - Read the code first.
      - Every example is runnable and was run. An example that needs the VM, GitHub or a model is marked as such and copied from a real run, and the text names that run.
      - Exact detail goes in a *Reference* section and is never cut.
      - The old sentence "Examples are runnable and were run." moved into the examples rule.
    - `agents/agents/documenter.md`, Stage step 3: run `make documents` and end only when its last line is `documents ok (<seconds> s)`. That is the human's wording from entry 11, and it keeps the literal `` `documents ok` `` that the test looks for. The step still runs `make check` after that.
    - `agents/agents/intake.md`: a new step 4. A docs criterion that dictates the sentences to write is a question: the agent ends with `question` and asks what the reader must know afterwards. Later steps are renumbered, and "steps 2 to 4" became "steps 2 to 5".
    - `agents/agents/reviewer.md`: a `### Documents` item in the checklist, after item 6 and before "Write findings" (entry 11, option a). It covers the changed documents' claims against the code. Two things are findings: a claim not found in the code, and a command without a runnable or marked example.

    Main choice: `### Documents` is a headed item after the numbered groups, not a numbered item 7. Criterion 5 and the tests ask for the heading. I rejected option (b), putting it at the end of Role, because it would have left the checklist.

    Refactor: I re-read the diff against `main` and found nothing to change.

    Description: entry 11 does not change what the task means, so the Description stays as it is.

    Noticed, not touched: `make documents` prints `documents ok (<seconds> s)`. I took that format from `docs/runs/2026-11-05-f0052/log.md`, not from running it in this stage.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
18. factory: started review as vm.
19. reviewer: Findings:

    1. `agents/agents/documenter.md`, Stage step 3: the shipped documenter serves every project, but the template project has no `documents` target in `operator/template/Makefile` and no `documents` command in `operator/template/factory/pipeline.yml`. A documenter there is told to end only on a line that it can never get. Fix: make the rule apply when the pipeline definition lists a `documents` command, in the same sentence that holds `make documents` and `documents ok`, so the test row still holds.
    2. `agents/agents/documenter.md`, Stage step 3: the step gives two orders for one moment. It says "run `make documents` after your last edit" and then "run `make check` in the same command as your last edit", and fixing a `make documents` finding is another edit. Fix: one order, for example "in the same command as your last edit, run `make documents`, then `make check`".
    3. `agents/agents/reviewer.md`, *Documents* item, line 3: "A command shown without a runnable example, or without one marked for the VM, GitHub or a model ..., is a finding" reads as an OR of two absences, so a runnable example with no mark becomes a finding. Fix: "A command shown with neither a runnable example nor one marked for the VM, GitHub or a model that names the real run it was copied from, is a finding".
    4. `agents/agents/reviewer.md`, *Documents* item, line 1: the item names only `README.md` and files under `docs/`. It leaves out `operator/README.md`, which the documenter may write and which the docs-review scope reads. Fix: name `operator/README.md` too, or say "a document the documenter may write".
    5. `tests/agent_files/test_claude_agent_texts_documents.py`, `_reviewer_checklist`: it cuts the `## Role` section out by hand with `body.index("\n## Role\n")` and `body.index("\n## Stage\n")`. That copies `factory.shared.domain.sections.section_text`, which `stage_section` in `tests/support/shipped_agents.py` already uses. Fix (tester): `section_text(agent_body("reviewer"), "Role")`, or a `role_section` beside `stage_section` in `tests/support/shipped_agents.py`.
    6. Work item, criterion 11 (the docs criterion): it names only how the documenter and the reviewer treat documents. The story also gives `agents/agents/intake.md` its new step 4 (a docs criterion that dictates sentences is a question) and renumbers steps 5 to 7. A reader of `docs/project-guide/agents.md` must know that too. Fix: the docs criterion also names the intake's question on a docs criterion that dictates sentences.

    Checked and fine:
    - Criteria 1 to 9 each have a row in `tests/agent_files/test_claude_agent_texts_documents.py`, and I read each row against the text it pins. The sides of each rule are rows of one parametrized test.
    - The coder's `make check` was green (journal entry 17).
    - No `src/` change, so there is nothing for the architecture or security groups. No suppression markers.
    - The Description matches what was built.

    Earlier tests:
    - `tests/agent_files/test_claude_agent_texts_review_groups.py`: the human's leave in the Interface (2026-11-05). `test_the_rest_of_the_reviewer_body_is_unchanged` keeps its name and only also strips the `### Documents` item.
    - `tests/agent_files/test_claude_agent_texts_mutants.py`: the human's answer in journal entry 11. `test_reviewer_item_6_is_followed_by_the_findings_paragraph` keeps its name and only skips the `### Documents` item. Nothing else in the module changed.
20. factory: started doing as vm.
21. coder: Test change for the tester (review finding 5, entry 19): in `tests/agent_files/test_claude_agent_texts_documents.py`, `_reviewer_checklist` cuts `## Role` out by hand with `body.index`. Replace that with `section_text(agent_body("reviewer"), "Role")` from `factory.shared.domain.sections`, or with a `role_section` helper beside `stage_section` in `tests/support/shipped_agents.py`. Every row should keep its name and check the same thing. No code depends on this change, so the work item can go back to review once it is made.

    I fixed review findings 1 to 4 and 6 in this round. `make check` is green (`check: green`, coverage 99.22 %), and `uv run pytest -q tests/agent_files` passes.

    - **Findings 1 and 2**, `agents/agents/documenter.md` Stage step 3: the step now gives one order. In the same command as the last edit, run `make documents` when the pipeline definition lists a `documents` command, then `make check`. The documenter ends only on `documents ok (<seconds> s)`, and runs the command again after fixing a finding it printed. The literal `` `documents ok` `` and `` `make documents` `` stay in the same paragraph, so the `make-documents-ends-on-ok` row still holds.
    - **Finding 3**, `agents/agents/reviewer.md` *Documents* item: the line now reads "A command shown with neither a runnable example nor an example marked for the VM, GitHub or a model that names the real run it was copied from is a finding." That removes the reading where an unmarked runnable example would count as a finding.
    - **Finding 4**, `agents/agents/reviewer.md` *Documents* item: the item now covers "a document the documenter may write (`README.md`, a file under `docs/`, `operator/README.md`)".
    - **Finding 6**, work item criterion 11: the docs criterion now also asks for the intake's question on a docs criterion that dictates the sentences to write. I edited only that criterion, the way the review asked; the Description's meaning is unchanged. If the coder's write paths don't include the work item, the factory drops this edit and the documenter needs the wording from this entry.

    Main choice: for finding 1, step 3 says the rule applies when the pipeline definition lists a `documents` command. I rejected the other route, taking `make documents` out of step 3, because the criterion and its test row need it there.

    Refactor: I read the diff again and found nothing to change.

    Noticed, not touched: nothing beyond the review's findings.

    `check`: check: green

    The factory left out changes outside the write paths: factory/features/F0053-the-documents-are-checked-against-the-code/in-progress/F0053-S0005-the-agents-write-and-review-documents-against-the-code.md.
22. factory: started tests as vm.
23. tester: I made the test change the coder named in entry 21, which is review finding 5 from entry 19. The change is in `tests/agent_files/test_claude_agent_texts_documents.py`, a test this story wrote.

    - `_reviewer_checklist` no longer cuts the `## Role` section out by hand with `body.index("\n## Role\n")` and `body.index("\n## Stage\n")`. It now returns `section_text(agent_body("reviewer"), "Role") or ""`, using `factory.shared.domain.sections.section_text`, the same helper `stage_section` in `tests/support/shipped_agents.py` uses.
    - The section still ends at the next `## ` heading. A `### Documents` subheading does not end it, so `_documents_item` still finds the item inside the checklist.
    - Every test keeps its name and still checks the same thing. Nothing else in the module changed.

    I rejected adding a `role_section` helper to `tests/support/shipped_agents.py`. Only this module needs that section, so calling `section_text` directly is enough.

    Files created: none. File changed: `tests/agent_files/test_claude_agent_texts_documents.py`.

    Run: `uv run pytest -q tests/agent_files/test_claude_agent_texts_documents.py`: 9 passed against the coder's agent files. Every module imported. `make lint`: lint: green (0.1 s).

    Open: this was the last open finding from the review. The work item can go back to review.

    `lint`: lint: green (0.1 s)
24. factory: started doing as vm.
25. coder: `make check` passes (`check: green`, `test: green (104.0 s)`, coverage 99.22 %). The tester's change in entry 23 (`_reviewer_checklist` now uses `section_text`) was the last open review finding, number 5. I changed no file in this run.

    What is built (my earlier runs, entries 10, 13 and 21):
    - `agents/agents/documenter.md`, Role: three rules.
      - Read the code first.
      - Every example is runnable, or is marked for the VM, GitHub or a model and copied from a real run that the text names.
      - Detail is kept in a *Reference* section and not cut.
    - `agents/agents/documenter.md`, Stage step 3: in the same command as the last edit, run `make documents` (when the pipeline definition lists a `documents` command), then `make check`. The documenter ends only on `documents ok (<seconds> s)`. This covers review findings 1 and 2.
    - `agents/agents/reviewer.md`: a `### Documents` checklist item after group 6. It covers any document the documenter may write. Two things are findings: a claim not found in the code, and a command with neither a runnable example nor a marked one. This covers review findings 3 and 4.
    - `agents/agents/intake.md`: a new step 4. A docs criterion that dictates the sentences to write is a question, and the intake ends with `question`. The criterion should name what the reader must know afterwards.

    Main choice: `### Documents` is a headed item after the numbered groups (the human's option a, entry 11), not a numbered item 7 and not placed at the end of Role.

    Refactor: I re-read the diff against `main` and found nothing to change.

    Still open, not touched: review finding 6. My edit to criterion 11 in entry 21 was dropped, because the work item is outside the coder's write paths. Criterion 11 still names only the documenter and the reviewer. The documenter should also describe the intake's new question on a docs criterion that dictates sentences in `docs/project-guide/agents.md`. Otherwise the human amends the criterion.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
26. factory: started review as vm.
27. reviewer: Findings:

    1. `agents/agents/documenter.md`, Stage step 3: this round's fix makes `make documents` depend on "when the pipeline definition lists a `documents` command". Step 1 of the same file forbids reading `factory/` ("not `factory/`"), so the documenter cannot check that condition. The next sentence, "End only when the last line of `make documents` is `documents ok (<seconds> s)`", is also unconditional, so a documenter in a project without the target still cannot end. Fix: base the condition on something the documenter may read, for example "when the project's Makefile has a `documents` target". Put the "End only when … `documents ok`" sentence inside that same condition, and keep `make documents` and `documents ok` in the one paragraph the test row reads.
    2. `agents/agents/reviewer.md`, `### docs-review`: the first paragraph says the subsection "replaces the Role's scope, its checklist (groups 1 to 6) and its decisions". The new `### Documents` item says it stands "beside groups 1 to 6", so on the docs route it is unclear whether it applies. Step 2 there only asks that every sentence be true of the code. It has nothing on a command shown without a runnable or marked example. The docs route is where the documenter wrote the whole change, and the Description says the reviewer counts such a command as a finding. Fix: in docs-review step 2, add that the *Documents* item's two findings apply there too. Or say in the *Documents* item that it holds in `docs-review` as well. Keep the change inside what `test_the_rest_of_the_reviewer_body_is_unchanged` already strips.
    3. `agents/agents/intake.md`, Stage step 7: it now asks for "one line per check of steps 2 to 5", but the list after the colon still names five lines: the Interface; the criteria; the smoke test; the architecture; the scope. Nothing covers the new step 4, the docs criterion. The step's own rule, "A check you cannot write a line for is one you did not do", then leaves step 4 without a line. Fix: add a line to that list, for example "the docs criterion (names what the reader must know, dictates no sentences)".

    Checked and fine:
    - Criteria 1 to 9 each have a row in `tests/agent_files/test_claude_agent_texts_documents.py`. I read each row against the agent text it pins, and the rows hold. Each rule's sides are rows of one parametrized test. `_reviewer_checklist` now uses `section_text` (round 0 finding 5, entry 23).
    - Round 0 findings 3 and 4 are fixed in the `### Documents` item. It now says "with neither … nor …", and it names every document the documenter may write.
    - The coder's `make check` was green (entries 21 and 25).
    - Nothing changed under `src/`, so the architecture and security groups have nothing to check. The diff adds no suppression markers.
    - The Description matches what was built.

    Withdrawn: round 0 finding 6, which asked criterion 11 to also name the intake's new step. No stage but the human can amend that criterion, and the coder could not (entry 25). The step is about the docs criterion itself, not about how the documenter or the reviewer treat documents. The documenter's cross-read already has to fix the step number this story moves in `docs/project-guide/agents.md:291` ("Step 6: chooses `docs-only`" is now step 7). The human may still widen criterion 11 at the approval.

    Earlier tests:
    - `tests/agent_files/test_claude_agent_texts_review_groups.py`: changed under the human's leave in the Interface (2026-11-05). `test_the_rest_of_the_reviewer_body_is_unchanged` keeps its name, and now also strips the `### Documents` item.
    - `tests/agent_files/test_claude_agent_texts_mutants.py`: changed under the human's answer in journal entry 11. `test_reviewer_item_6_is_followed_by_the_findings_paragraph` keeps its name and only skips the `### Documents` item. Nothing else in that module changed.
28. factory: started doing as vm.
29. coder: Round 2: I fixed review findings 1 to 3 from entry 27. `make check` is green (`check: green`, `test: green (102.3 s)`, coverage 99.22 %), and `uv run pytest -q tests/agent_files` passes.

    - **Finding 1**, `agents/agents/documenter.md` Stage step 3: the condition is now "when the project's Makefile has a `documents` target". The documenter may read the Makefile; it may not read `factory/`. The end condition now sits inside that condition too: "With that target, end only when the last line of `make documents` is `documents ok (<seconds> s)` …; without that target, `make check` alone." `make documents` and `documents ok` stay in one paragraph, so the `make-documents-ends-on-ok` row still holds.
    - **Finding 2**, `agents/agents/reviewer.md` `### Documents` item: it has a new last line, "This item holds in the stage `docs-review` as well, beside its step 2: the two findings above are findings there too." I put the fix in the item and not in docs-review step 2, so the change stays inside what `_DOCUMENTS_ITEM` strips in `test_the_rest_of_the_reviewer_body_is_unchanged`. The item still has the shape the mutants test skips: heading, blank line, paragraph lines, blank line.
    - **Finding 3**, `agents/agents/intake.md` Stage step 7: the list of lines for the accepted entry now includes "the docs criterion (names what the reader must know, dictates no sentences)". It sits between the smoke test and the architecture, in step order.

    Main choice: for finding 2, one sentence in the *Documents* item says it also holds in docs-review. I rejected editing docs-review step 2, because two places would then have to say the same rule, and other tests pin that subsection.

    Refactor: I re-read the three-line diff and found nothing to change.

    Description: no journal entry in this round changes what the task means.

    Noticed, not touched: the docs criterion (11) still names only the documenter and the reviewer, and the reviewer withdrew that point (entry 27). `docs/project-guide/agents.md:291` names the intake's route step as step 6, and it is now step 7. The documenter's cross-read should fix that.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
30. factory: started review as vm.
31. reviewer: Findings:

    1. `agents/agents/documenter.md`, Stage step 3 and the last bullet of `## Lessons`: the problem is where the rule sits. The rule that the documenter runs `make documents` and ends only on `documents ok (<seconds> s)` (criterion 4, rule 10) is in step 3. The Lessons bullet "When every file you changed is a document (`README.md` or a file under `docs/`), end without running `make check`, in place of step 3 of the stage" replaces all of step 3. That is the documenter's usual case, so in most stories the `make documents` rule is dropped with it. Only a documenter that changed a file outside the documents would still run it. The test row `make-documents-ends-on-ok` passes anyway, because it only counts the paragraph and does not see that the lesson overrides it. Fix: move the `make documents` sentence out of what the lesson replaces. One way is to keep step 3 for the documents check alone and put `make check` in its own step, then make the lesson say "end without running `make check`" and no longer "in place of step 3". The other way is to make the lesson name only the `make check` half of step 3. Either way, `make documents` and `documents ok` must stay in one paragraph so the test row still holds.

    Checked and fine:
    - Every criterion from 1 to 9 has a row in `tests/agent_files/test_claude_agent_texts_documents.py`. I read each row against the agent text it pins, and they hold. The sides of each rule are rows of one parametrized test.
    - The coder's `make check` was green (journal entry 29).
    - `make documents` prints `documents ok (<n> s)` as its last line (`src/factory/entry/check_documents.py:194`), which matches the wording in step 3.
    - Round 1 finding 1 is fixed. The step 3 condition is now on the project's Makefile, which the documenter may read. Without the target, the step ends on `make check` alone.
    - Round 1 finding 2 is fixed. The `### Documents` item now says it applies in `docs-review` too, so it no longer contradicts the docs-review sentence that replaces groups 1 to 6.
    - Round 1 finding 3 is fixed. Intake step 7's list now has a line for the docs criterion of step 4.
    - No other agent file names the intake's step numbers.
    - Nothing changed under `src/`, so the architecture and security groups have nothing to check, and the diff adds no suppression markers.
    - The Description matches what was built.
    - Criterion 11, the docs criterion, still says what the reader must know.

    Earlier tests:
    - `tests/agent_files/test_claude_agent_texts_review_groups.py` was changed under the human's leave in the Interface (2026-11-05). `test_the_rest_of_the_reviewer_body_is_unchanged` keeps its name; the only change is that it also strips the `### Documents` item.
    - `tests/agent_files/test_claude_agent_texts_mutants.py` was changed under the human's answer in journal entry 11. `test_reviewer_item_6_is_followed_by_the_findings_paragraph` keeps its name; the only change is that it skips the `### Documents` item. Nothing else in that module changed.
32. factory: This work item has now been sent back 3 times, more than 2. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.
