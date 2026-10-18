---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 239
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T23:50:32.863919Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T23:50:32.869781Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T23:50:51.439242Z'
  stage: intake
  run: c1c694801ae1425997d9639bb5ed1211
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T23:51:11.226300Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T23:53:11.509869Z'
  stage: tests
  run: 03f208f9b840403d8b1103af6dc68852
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-18T23:53:31.880702Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-18T23:55:34.162702Z'
  stage: doing
  run: 95814edefb5e4f14b155cf65b1e9b7fe
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-18T23:55:54.233713Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-18T23:56:35.877483Z'
  stage: review
  run: a793badd8b3040e880b3013ecbf9f192
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-18T23:56:56.248192Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-18T23:58:04.750485Z'
  stage: docs
  run: b86ad4a6fa424a97b7543acd645d8624
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-18T23:58:24.836865Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-18T23:58:54.159393Z'
  stage: smoke-test
  run: 78a960933e3240a0a477ce7d77d59cad
---

# The reviewer's notes and leave, and the rule never to edit a running work item on main

## Description

Two questions keep reaching the human. The first: at every review round, the reviewer sends a story back for points that are only the quality of the story's own new tests (a copied helper, a name, a duplicate test), and the round cap then asks the human whether to go on. The second: a review finds behaviour the diff already builds that no criterion names, and the reviewer asks the human for a criterion that needs no code at all. This story changes the shipped agent texts so that, from round 1 on, such test-quality points go forward as notes in the reviewer's entry instead of back, while a point on a criterion, the architecture, security or `src/` still sends the story back; and so that the reviewer may itself add a criterion that only pins behaviour already built, writing it into the work item and naming it in its entry, the coder handing it on to the tester without a code change and the tester writing the test (the feature's decisions 10 and 11). The tester's step 0 gains one sentence, so that it writes that test without a human's answer to edit. The acceptance reviewer's cost check names the new facts line of S0002. A further text is the operator's: `docs/operator-guide.md` says never to edit a running work item on `main`, but to answer in its pull request, since the agents amend the story on its branch and a human's edit on `main` conflicts with the branch at the next stage start, as F0019-S0004 showed. Every other text of the agents stays as it is, the lessons sections included.

## Interface

`claude/agents/reviewer.md` (the coder writes it), section `## Role`:

- The paragraph that begins `Your recommendation is your decision:` and ends `Never both, never "pass with remarks": a remark worth writing is a finding.` becomes exactly:

  ```markdown
  Your recommendation is your decision: `docs` passes, `doing` sends the work item back. Never both, and never "pass with remarks": a remark worth writing is a finding, except for the notes from round 1 on below.
  ```

- Right after it, two new paragraphs, exactly:

  ```markdown
  From round 1 on (your prompt names the round; the first review, at round 0, still sends such a point back), a point that is only about the quality of a test file the diff adds (a copied helper, a name, a duplicate test) is a note, not a finding: write the notes under `Notes:` after the findings, or after `no findings`, one line each with its location; they do not send the work item back. This holds for the copied helper and the separate test functions your lessons count as findings, when they are in a test file the diff adds. A point on an acceptance criterion (an untested side of a stated limit among them), the architecture, security or anything under `src/` is still a finding and sends it back with `doing`.

  When the diff builds a behaviour that no criterion names, and pinning it needs no change under `src/`, add the criterion yourself instead of asking the human: write it into the work item's `## Acceptance criteria` before the two closing ones and renumber those, name it in your entry as the finding `criterion <n> added: it needs its test`, and end with `doing`. The coder hands it to the tester, who writes the test. A criterion that needs a code change stays a finding or a question.
  ```

`claude/agents/coder.md`, section `## Stage`, step 2: one sentence appended at its end, exactly:

```markdown
When the reviewer's latest entry adds a criterion that needs only its test, change no code: end with `tests` and an entry naming the criterion.
```

`claude/agents/tester.md`, section `## Stage`, step 0: one sentence appended at its end, exactly:

```markdown
When the coder's entry names a criterion the reviewer added that needs only its test, there is no test to edit: write the test of that criterion as the role section describes, run `make test` once, and end with `doing`.
```

`claude/agents/acceptance-reviewer.md`, section `## Role`, check 8 (**Cost.**): one sentence appended at its end, exactly:

```markdown
Your prompt's `Human interventions of the stories` line counts the questions the human answered, by cause, and the hours the stories waited for them: give both in the cost section, and name the story that needed the human most when its journal shows why.
```

- No other line of the four files changes; the `## Lessons` sections stay exactly as `tests/test_claude_agent_texts.py` pins them, and no new text uses a word that test bans.

`docs/operator-guide.md` (the documenter writes it, from the docs criterion).

Test module (new): `tests/test_claude_agent_texts_review_leave.py`, reading the bodies through `agent_body` of `tests/shipped_agents.py`. No earlier test changes.

## Acceptance criteria

1. Rows of one parametrized test, each a text that the body of an agent holds in the named section (`section_text`): the reviewer's new recommendation paragraph, its paragraph of notes from round 1 on and its paragraph of the added criterion, each exactly as the Interface gives it, in `Role`; the coder's sentence in `Stage`; the tester's sentence in `Stage`; the acceptance reviewer's sentence in `Role`.
2. The reviewer's body no longer holds `Never both, never "pass with remarks": a remark worth writing is a finding.`, and its three paragraphs of criterion 1 follow each other in the order the Interface gives them (rows of one parametrized test on the position of each paragraph).
3. Every test of `tests/test_claude_agent_texts.py` passes unchanged, its exact lessons of the reviewer, the coder and the acceptance reviewer included.
4. `make check` stays green.
5. docs:
   - `docs/operator-guide.md`, *A stage changed by hand*: a new subsection with the heading line exactly `### Never edit a running work item on main`. It says: do not edit the file of a work item in `in-progress/` on `main`; answer in its pull request, and the agents amend the story on its branch; an edit on `main` conflicts with the branch when the next stage start merges `main` into it, and the stage stalls with the reason `merge_conflict` (F0019-S0004 showed it); and, when it has happened, revert the edit on `main`.
   - `docs/operator-guide.md`, *The hand-over at the approval* or *The factory's own questions*: one paragraph on the reviewer's notes from round 1 on and its added criterion, so that the human reading a review entry knows what `Notes:` and `criterion <n> added` mean, and that an added criterion is a send-back that counts a round, so the round cap may still ask the human afterwards.
   - `docs/decisions.md`: a new entry, "The reviewer passes test-quality points on as notes from round 1 on, and may add a criterion that needs no code", with the reason (two recurring questions to the human; the factory's way from an LLM on watch to running alone) and the rejected alternatives: raising the round cap, and leaving every criterion to the human.

## Smoke test

```bash
grep -cx '### Never edit a running work item on main' docs/operator-guide.md
```

Expect: `1`

```bash
grep -c 'From round 1 on (your prompt names the round; the first review, at round 0, still sends such a point back), a point that is only about the quality of a test file the diff adds' claude/agents/reviewer.md
grep -c 'criterion <n> added: it needs its test' claude/agents/reviewer.md
grep -c 'When the reviewer.s latest entry adds a criterion that needs only its test, change no code' claude/agents/coder.md
grep -c 'there is no test to edit: write the test of that criterion' claude/agents/tester.md
grep -c 'Human interventions of the stories' claude/agents/acceptance-reviewer.md
```

Expect: five lines, each `1`.

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: concrete. It names four agent files and sections, the exact replacement paragraph and the exact new paragraphs and sentences, the new test module `tests/test_claude_agent_texts_review_leave.py` that reads bodies through `agent_body`, and the docs file. The old reviewer paragraph exists at `claude/agents/reviewer.md:62`. The new texts use none of the words that `_BANNED_WORDS` in `tests/test_claude_agent_texts.py` bans.
   - Criteria: each is testable by one parametrized test function. Criterion 1 pins every stated text exactly, with its agent and section. Criterion 2 covers both sides of the replacement: the old sentence is gone, and the three paragraphs follow in order. Criterion 3 keeps the earlier text tests and the lessons unchanged. Criterion 4 is `make check`. The docs criterion lists three items. The Interface states no limit, validation or error whose failing side needs a separate criterion. Its behaviours (notes from round 1 on, the added criterion) are the texts criterion 1 pins.
   - Smoke test: the greps are runnable. Each Expect line (`1`, or five lines of `1`) can be checked against the output.
   - Architecture: only shipped agent texts, one new test module and docs change. No layer or `src/` code is touched. The paths fit the roles' write paths: the coder writes `claude/*`, the tester writes `tests/*`, the documenter writes `docs/*`.
   - Scope: this is S0005 of F0021, listed in the feature's Scope under "The texts". Decisions 10, 11 and 12 are followed, including the smoke-test pin for the operator guide. Nothing in "Out of scope" is touched.
4. factory: started tests as self.
5. tester: Tests written for the agent text criteria. They are red on purpose: the new texts are not yet in `claude/agents/`.

   - criterion 1: tests/test_claude_agent_texts_review_leave.py::test_agent_section_holds_the_review_leave_text has six rows. Each row checks that one text is in its section, read with `section_text` over `agent_body`. The rows are:
     - the reviewer's recommendation paragraph, notes paragraph and added-criterion paragraph, in `Role`
     - the coder's sentence, in `Stage`
     - the tester's sentence, in `Stage`
     - the acceptance reviewer's sentence, in `Role`
   - criterion 2: two tests.
     - tests/test_claude_agent_texts_review_leave.py::test_reviewer_no_longer_holds_the_old_recommendation_sentence checks that the old sentence is gone.
     - tests/test_claude_agent_texts_review_leave.py::test_reviewer_paragraph_follows_the_one_before_it has two rows, one per pair of paragraphs (recommendation→notes, notes→added criterion). Each row checks that the later paragraph comes right after the earlier one, with one blank line between them.
   - criterion 3: no new test. The unchanged tests/test_claude_agent_texts.py covers it, the `test_lessons_section_is_last_and_holds_exactly_the_role_bullets` rows and the banned-word tests included. I did not touch that file.
   - criterion 4: `make check`, run by the coder and the factory.
   - criterion 5 (docs): no test. The documenter writes it, and the smoke test greps for it.

   Files created: tests/test_claude_agent_texts_review_leave.py. No earlier test file changed.

   Every module imported. One run of `make test`: the new tests fail on a wrong result because the texts are missing; the acceptance reviewer row and those of the coder, the tester and the reviewer's added criterion are among them. `make lint` is green.

   What I chose not to do: I check that the paragraphs are adjacent by matching the text `earlier\n\nlater`, not by comparing positions with `index`. "Follow each other" in criterion 2 means adjacent, and comparing positions would only check the order. I did not check that the coder's and the tester's sentences come at the very end of their numbered step. Criterion 1 asks only that the section holds the text.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/test_claude_agent_texts_review_leave.py::test_agent_section_holds_the_review_leave_text[acceptance]
6. factory: started doing as self.
7. coder: I added the shipped agent texts exactly as the Interface gives them. `make check` is green.

   - `claude/agents/reviewer.md`, `## Role`: the paragraph that began `Your recommendation is your decision:` is replaced by the new one. Right after it come the notes paragraph (from round 1 on) and the added-criterion paragraph, separated by single blank lines.
   - `claude/agents/coder.md`, `## Stage` step 2: the new sentence is appended after "The tester makes the change and sends the work item back."
   - `claude/agents/tester.md`, `## Stage` step 0: the new sentence is appended after "Skip the steps below."
   - `claude/agents/acceptance-reviewer.md`, `## Role` check 8 (**Cost.**): the new sentence is appended at its end.

   Main choice: I made the replacements with a throwaway script in `$TMPDIR`. It reads the expected strings from the tester's module and checks that each anchor appears exactly once, so the shipped text matches the tests character for character. I rejected retyping the paragraphs by hand, which risked a small mismatch in long exact strings. No other line of the four files changed, and the `## Lessons` sections are untouched.

   Refactor: there was nothing to change, since the diff is only the stated text.

   Noticed but not touched:
   - In the tester's step 0, the new sentence comes after "Skip the steps below." This is the order the Interface asks for ("appended at its end"). It reads a little oddly, because the new case also skips the steps below but is a different mode.
   - The docs criterion (`docs/operator-guide.md`, `docs/decisions.md`) is the documenter's.
   - The journal did not change the meaning of the task.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   - Criteria 1 and 2 (the new agent texts): the four agent files change only on the lines the Interface names, and each new text matches the Interface word for word.
     - `claude/agents/reviewer.md:62-66` holds the new recommendation paragraph, then the notes paragraph, then the added-criterion paragraph, in that order.
     - `claude/agents/coder.md:59`, `claude/agents/tester.md:59` and `claude/agents/acceptance-reviewer.md:58` each end with their new sentence.
     - `tests/test_claude_agent_texts_review_leave.py` checks each text in its section with one six-row parametrized test. It checks that the old sentence is gone, and that each paragraph comes straight after the one before it with two rows of one parametrized test. Checking that they sit next to each other is stricter than checking the order alone.
   - Criteria 3 and 4: `tests/test_claude_agent_texts.py` is unchanged and none of the `## Lessons` sections were touched. The factory's `make check` after the coder was green (entry 7).
   - The new texts fit the factory as it is:
     - The reviewer's write paths in `factory/pipeline.yml` include `{work_item}`, so the reviewer can write an added criterion into the work item.
     - The `Human interventions of the stories` line exists in `src/factory/domain/acceptance.py:215`.
     - When the coder ends with `tests`, the factory gives the tester the mode line that step 0 handles (`src/factory/domain/prompts.py:41`).
   - Architecture and security: nothing under `src/` changed, and no marker that silences a check was added.
   - Quality and work item hygiene: the new test module has a module docstring and uses plain parametrized tests. The journal gives the coder's main choice and what it rejected, and the Description matches what was built. The docs criterion is the documenter's next job.

   Earlier tests: none. The only test file in the diff is the new `tests/test_claude_agent_texts_review_leave.py`.
10. factory: started docs as self.
11. documenter: No findings. The code matches the Interface.

    Files changed (documents only, so I did not run `make check`; the factory's run after this stage decides):
    - `docs/operator-guide.md`: new `### Never edit a running work item on main` at the end of *A stage changed by hand*. It says to answer in the pull request, and that an edit on `main` conflicts at the next stage start and stalls with `merge_conflict` (F0019-S0004). When it has happened, revert the edit on `main`.
    - `docs/operator-guide.md`: new `### The reviewer's notes and added criteria` at the end of *The factory's own questions*. It explains `Notes:` from round 1 on and `criterion <n> added`. It also says an added criterion is a send-back that counts a round, so the round cap may still ask the human.
    - `docs/decisions.md`: new entry "The reviewer passes test-quality points on as notes from round 1 on, and may add a criterion that needs no code". It gives the reason and the rejected alternatives: raising the round cap, and leaving every criterion to the human.

    Checks run: `grep -cx '### Never edit a running work item on main' docs/operator-guide.md` gives `1`, as the smoke test expects. I did not run the agent-file greps, which the smoke tester runs.

    Cross-read and found current: the operator guide's *The agent files* section, whose list of seven agents is unchanged, and the story's diff, which is only the four agent texts and the new test module.

    Stale text noticed, not touched: in `docs/operator-guide.md`, the rows "The form has findings" and "The round cap" of the table in *The factory's own questions* have a "Comment reads" cell that says `no claude process of agent; see "A time_limit under sudo" above`. That is unrelated to this story.

    `check`: check: green
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed. I ran both commands from the repository root exactly as written, and both met their `Expect:` lines.

    Command 1:

    ```bash
    grep -cx '### Never edit a running work item on main' docs/operator-guide.md
    ```

    ```
    1
    ```

    Met: `Expect: 1`.

    Command 2 (five greps):

    ```bash
    grep -c 'From round 1 on (your prompt names the round; the first review, at round 0, still sends such a point back), a point that is only about the quality of a test file the diff adds' claude/agents/reviewer.md
    grep -c 'criterion <n> added: it needs its test' claude/agents/reviewer.md
    grep -c 'When the reviewer.s latest entry adds a criterion that needs only its test, change no code' claude/agents/coder.md
    grep -c 'there is no test to edit: write the test of that criterion' claude/agents/tester.md
    grep -c 'Human interventions of the stories' claude/agents/acceptance-reviewer.md
    ```

    ```
    1
    1
    1
    1
    1
    ```

    Met: `Expect: five lines, each 1`.

    Checked against the acceptance criteria:
    - **Criterion 2:** `grep -c 'Never both, never "pass with remarks"' claude/agents/reviewer.md` gives `0`, so the old sentence is gone.
    - **Docs criterion, operator guide (stage changed by hand):** `docs/operator-guide.md:1136` has the new subsection. It says:
      - do not edit an `in-progress/` work item on `main`, but answer in its pull request;
      - the agents amend the story on its branch;
      - an edit on `main` conflicts at the next stage start and stalls with `merge_conflict` (F0019-S0004);
      - when it has happened, revert the edit on `main`.
    - **Docs criterion, operator guide (the factory's own questions):** `docs/operator-guide.md:632` explains `Notes:` from round 1 on and `criterion <n> added`. It also says an added criterion is a send-back that counts a round, so the round cap may still ask the human.
    - **Docs criterion, decision log:** `docs/decisions.md:628` has the decision entry with the stated title.
    - **Other criteria:** nothing in the smoke test contradicts criteria 1, 3 or 4. I did not run `make check`, because it is not part of the smoke test; the factory runs it as the stage's check.

    Findings: none.
