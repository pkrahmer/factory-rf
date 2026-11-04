---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 513
comments_read: [6598169268, 6598279355]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T07:42:34.553073Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T07:42:34.559287Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-03T07:42:54.722578Z'
  stage: intake
  run: b209edc61ff5441194c85b7b35149e43
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-03T07:44:46.168201Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-03T07:44:49.155102Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-03T07:45:09.766705Z'
  stage: intake
  run: 22eff09d79eb405fafa8e7f533008c84
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T07:45:15.807964Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-03T07:45:47.495187Z'
  stage: tests
  run: 9264cc5771e4454b8fbf142dc633fc95
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-03T07:45:53.564942Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-03T07:49:29.469657Z'
  stage: doing
  run: 813600e76b864ad0957bb88634dd4d45
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-03T07:51:20.520587Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-03T07:51:23.419586Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-03T07:51:41.820453Z'
  stage: doing
  run: 34f9f6e1d97541dcab401d9e7278cecf
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-03T07:51:47.407253Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-03T07:52:20.367801Z'
  stage: tests
  run: 306579f893974285b2bf2388c4d9fa6b
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-03T07:52:26.002574Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-03T07:55:44.507220Z'
  stage: doing
  run: fddb7be870d34885bf67dedb9714dd98
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-03T07:55:50.218894Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-03T07:56:26.054555Z'
  stage: review
  run: dd9c6366f15547bba3d0bb9344639362
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-03T07:56:32.104743Z'
  stage: docs
- number: 21
  speaker: documenter
  kind: result
  at: '2026-11-03T07:56:55.780770Z'
  stage: docs
  run: 8d40a351a3c74c5ebbd004b035eaedbc
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-03T07:57:01.931027Z'
  stage: smoke-test
- number: 23
  speaker: smoke-tester
  kind: result
  at: '2026-11-03T07:57:16.410856Z'
  stage: smoke-test
  run: b03052b54cb14a6e800a853a9ce666db
- number: 24
  speaker: factory
  kind: done
  at: '2026-11-03T08:03:15.284988Z'
  stage: approval
---

# A missing test row for a side the code already handles is a note

<!-- written by the human on 2026-11-03 from the acceptance F0048-A0001's decision 9 (decision 23) -->

## Description

Three times in F0048 (S0001 entry 33, S0003 entry 30, S0005 entry 26) the human answered the same question the same way: when the reviewer finds a side of a stated limit without a test, and the code already handles that side correctly, the missing test row is a note, not a reason to send the story back. Each time the question cost a wait or a round. The rule is written nowhere lasting: `claude/agents/reviewer.md` still says that "an untested side of a stated limit" is a finding, and `CLAUDE.md` (*Tests*) says that "the reviewer counts an untested side as a finding". This story writes the human's rule into the reviewer's text and the decision log, so that the question does not come again.

The reviewer must still read the code and confirm that it handles the side; a side the code gets wrong, or does not handle, stays a finding. The tester's rule to test every stated limit on both sides stays as it is: the change is only in what the reviewer sends back.

## Interface

- `claude/agents/reviewer.md`, the paragraph on notes: a stated limit's side that has no test is a note, not a finding, when the reviewer has read the code and it handles that side as the Interface says; the note names the side, the code's location and the missing row. A side the code does not handle, or handles otherwise, is still a finding. This holds from round 0. Every other sentence of the paragraph stays. The sentence "A point on an acceptance criterion (an untested side of a stated limit among them), the architecture, security or anything under `src/` is still a finding and sends it back with `doing`." is replaced, word for word, by these three (journal entry 4): "A point on an acceptance criterion, the architecture, security or anything under `src/` is still a finding and sends it back with `doing`. One exception holds from round 0: a side of a stated limit that has no test is a note, not a finding, when you have read the code and it handles that side as the Interface says; the note names the side, the code's location and the missing row. A side the code does not handle, or handles otherwise, is a finding." The coder copies them into `claude/agents/reviewer.md`; the text test pins them, the clause "One exception holds from round 0" included.
- `tests/test_claude_agent_texts_review_leave.py` pins the new text in place of the sentence it changes (the human's leave in `feature.md`).

## Acceptance criteria

1. `claude/agents/reviewer.md` holds the rule of the Interface, which the text test pins word for word; the sentence that counted "an untested side of a stated limit" among the findings no longer does so for a side the code handles.
2. The text test still pins every other sentence of the notes paragraph as before.
3. `make check` stays green.
4. docs: `docs/decisions.md`: one entry stating the rule, the three answers it comes from, and the rejected alternative (sending every missing row back, which cost a round each time). `CLAUDE.md` is the human's to change and is changed with this story's merge by the human, not by a stage. `README.md`, the operator guide and the project guide: none.

## Smoke test

```bash
grep -c 'handles that side' claude/agents/reviewer.md
```

Expect: `1`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: 1. Criterion 1 says the text test pins the new rule "word for word", but neither the Interface nor the criteria give the words. The tester writes the pin before the coder writes `claude/agents/reviewer.md`, so it cannot know the wording. The only fixed fragment is `handles that side` (the smoke test). Please give the exact replacement sentence(s) for the one in `tests/test_claude_agent_texts_review_leave.py` lines 20-22 ("A point on an acceptance criterion (an untested side of a stated limit among them), ... is still a finding"). The sentence should cover: a side the code handles is a note with its location, the side and the missing row; a side the code does not handle, or handles otherwise, is a finding; and it holds from round 0. I would choose a sentence you write, which the coder copies and the tester pins.
   2. The existing paragraph limits notes to "round 1 on", while the Interface says the new rule "holds from round 0". Please say whether the test pins the round-0 wording as a separate clause. I would choose yes, inside the sentence from question 1.
   3. Criterion 1 also says the old sentence "no longer counts" a handled side as a finding. That is checkable only through the new wording from question 1, so no separate criterion is needed once you give it.
   Everything else is fine: the Interface names concrete files, the smoke test runs and its `Expect: 1` can be checked, and the story fits the feature's scope and its leave for the test change. It also fits the architecture, because it touches no code under `src/`.
4. 2026-11-03 human: 1. The sentence "A point on an acceptance criterion (an untested side of a stated limit among them), the architecture, security or anything under `src/` is still a finding and sends it back with `doing`." is replaced, word for word, by these three sentences:

   > A point on an acceptance criterion, the architecture, security or anything under `src/` is still a finding and sends it back with `doing`. One exception holds from round 0: a side of a stated limit that has no test is a note, not a finding, when you have read the code and it handles that side as the Interface says; the note names the side, the code's location and the missing row. A side the code does not handle, or handles otherwise, is a finding.

   The coder copies them into `claude/agents/reviewer.md`, and the tester pins them in place of the old sentence. Every other sentence of the paragraph stays.
   2. Yes: the round-0 wording is the clause "One exception holds from round 0" inside the text above, and it is pinned with it.
   3. Agreed: no separate criterion is needed; criterion 1 is met by the pinned text.

   — Kumpel, for the human who owns this project
   <!-- kumpel -->
5. factory: started intake as vm.
6. intake: accepted
   - Interface: names concrete files (`claude/agents/reviewer.md` notes paragraph, line 66; `tests/test_claude_agent_texts_review_leave.py` `_NOTES`). Carrying in the human's answer (journal entry 4), I wrote the replacement three sentences into the Interface word for word, replacing the old sentence at the end of `_NOTES`. That is the human's edit, not mine. The Description needed no change.
   - Criteria: criterion 1 is testable by one text-pin test now that the words are fixed, and the round-0 clause "One exception holds from round 0" is pinned with them (answer 2). Criterion 2 is testable: every other sentence of `_NOTES` stays pinned. The rule's failing side ("a side the code does not handle, or handles otherwise, is a finding") is in the pinned text. Criteria 3 and 4 are the closing ones. The criterion for the docs entry is checkable by reading `docs/decisions.md`.
   - Smoke test: `grep -c 'handles that side' claude/agents/reviewer.md` is runnable. It prints 0 now, because the new text isn't in the file yet. Once the three sentences are copied in, it prints 1, because "handles that side" appears once. `Expect: 1` is checkable.
   - Architecture: only agent text and a text test change. Nothing under `src/` changes, so the layers are untouched.
   - Scope: this is within F0048 (the feature lists S0017 and decision 23). The change to the pinned sentence in the text test is covered by the feature's leave for S0017, and the tester changes nothing else in that module.
7. factory: started tests as vm.
8. tester: I changed the pinned notes paragraph in `tests/test_claude_agent_texts_review_leave.py`, as the feature's leave for this story allows. In `_NOTES`, the old last sentence ("A point on an acceptance criterion (an untested side of a stated limit among them), …") is replaced by the human's three sentences from journal entry 4, word for word. The clause "One exception holds from round 0" is included. Every other sentence of `_NOTES` is unchanged, and so are the other constants and test functions.

   - criterion 1: tests/test_claude_agent_texts_review_leave.py::test_agent_section_holds_the_review_leave_text[reviewer-notes] pins the new rule word for word. tests/test_claude_agent_texts_review_leave.py::test_reviewer_paragraph_follows_the_one_before_it[added-criterion-follows-notes] requires that the paragraph end with the new text right before the next paragraph. So the old sentence, which counted an untested side among the findings, can no longer close the paragraph.
   - criterion 2: the same two tests, plus test_reviewer_paragraph_follows_the_one_before_it[notes-follow-recommendation]. They pin every other sentence of the notes paragraph and its place, as before.
   - criterion 3 (`make check` green) and criterion 4 (docs) are not tester work: the coder's check and the docs stage cover them.

   Files created: none. Changed: tests/test_claude_agent_texts_review_leave.py, the `_NOTES` constant only, under the feature's leave named in the Interface.

   Modules the test run could not import: none. The run (`uv run pytest -q tests/test_claude_agent_texts_review_leave.py`) fails on purpose in three tests: [reviewer-notes], [notes-follow-recommendation] and [added-criterion-follows-notes]. They fail with an AssertionError because `claude/agents/reviewer.md` still holds the old sentence. `make lint` is green.

   Rejected: a separate test that the old parenthetical is absent from the file. The adjacency test already rules it out of the paragraph, and the leave covers only the pinned sentence, not new tests in that module.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I copied the human's three sentences (journal entry 4) word for word into `claude/agents/reviewer.md`, in the notes paragraph, in place of the sentence "A point on an acceptance criterion (an untested side of a stated limit among them), …". All tests in `tests/test_claude_agent_texts_review_leave.py` now pass, and the smoke test `grep -c 'handles that side' claude/agents/reviewer.md` prints `1`. The edit is in the working tree.

    I stopped here because `make check` is red, and the only cause is a test another story wrote:

    ```
    E   AssertionError: assert 1638756616 == 3903663111
    FAILED tests/test_claude_agent_texts_review_groups.py::test_the_rest_of_the_reviewer_body_is_unchanged
    ```

    That test takes the whole reviewer body, swaps the checklist sentence back to its earlier wording, and compares the CRC-32 with `_EARLIER_BODY_CRC32 = 3903663111`. Any change to the reviewer body breaks it, so this story's own change breaks it too. With my edit stashed, the test passes. The feature's leave covers only `tests/test_claude_agent_texts_review_leave.py`, and the standing leave in `CLAUDE.md` covers only moving shared helpers. So neither the tester nor I may change this test without your leave (R9, and "Not without asking").

    The options I see:
    (a) Give the tester leave to change `test_the_rest_of_the_reviewer_body_is_unchanged` so that, before it takes the CRC, it also swaps this story's three new sentences back to the old sentence. `_EARLIER_BODY_CRC32` stays as it is. The test keeps checking exactly what it checked before: nothing else in the body changed.
    (b) Give leave to set `_EARLIER_BODY_CRC32` to the new body's value (1638756616, after the checklist sentence is swapped back). This is simpler, but the constant then no longer means "the body on `main` before the checklist change", and its comment would need rewriting.
    (c) Something else you prefer.

    I would choose (a). Once you answer, I end with `tests`, naming that change.

    Rejected: I did not reword the reviewer text to dodge the CRC. That is not possible, and the words are fixed by entry 4.

    Not done yet: the refactor step (there is nothing to refactor in a one-sentence text replacement) and `docs/decisions.md`, which the docs stage writes.
11. 2026-11-03 human: (a). The tester has leave to change `test_the_rest_of_the_reviewer_body_is_unchanged` in `tests/test_claude_agent_texts_review_groups.py`, and only that test: before it takes the CRC, it also swaps this story's three sentences back to the old sentence. `_EARLIER_BODY_CRC32` and every other line of the module stay as they are, and the test keeps its name. The tester's entry names the change.

    — Kumpel, for the human who owns this project
    <!-- kumpel -->
12. factory: started doing as vm.
13. coder: The human's answer (journal entry 11, option (a)) calls for a test change. Only the tester may make it, so I changed no code in this run. The tester should change `test_the_rest_of_the_reviewer_body_is_unchanged` in `tests/test_claude_agent_texts_review_groups.py`, and only that test. Before it takes the CRC-32, it also swaps this story's three new sentences in the reviewer body back to the old sentence ("A point on an acceptance criterion (an untested side of a stated limit among them), the architecture, security or anything under `src/` is still a finding and sends it back with `doing`."). `_EARLIER_BODY_CRC32`, the test's name and every other line of the module stay as they are.

    State of the code: the three sentences from journal entry 4 are already in `claude/agents/reviewer.md`, committed with the previous doing run. `grep -c 'handles that side' claude/agents/reviewer.md` prints `1`. Once the tester's change is in, I run `make check` and end with `review`; the refactor step has nothing to change in a one-sentence text replacement.

    Rejected: going on to `make check` now. It stays red on the CRC test until the tester changes it.

    Open: `docs/decisions.md` is the docs stage's work.
14. factory: started tests as vm.
15. tester: I made the test change the human approved in journal entry 11, option (a), and the coder named it in entry 13. It is in `tests/test_claude_agent_texts_review_groups.py::test_the_rest_of_the_reviewer_body_is_unchanged`, and only in that test.

    The test already swapped the checklist sentence back to its earlier wording. Now, before it takes the CRC-32, it also swaps this story's three new sentences (journal entry 4) back to the old sentence: "A point on an acceptance criterion (an untested side of a stated limit among them), the architecture, security or anything under `src/` is still a finding and sends it back with `doing`." Both texts are local values inside the test body, so nothing at module level changed. `_EARLIER_BODY_CRC32`, the test's name and every other line of the module stay as they were. The test still checks the same thing: nothing else in the reviewer body changed.

    Why: the human's answer in entry 11. This story's change to the reviewer body broke the CRC, and the test was meant to watch only the rest of the body.

    Mapping to criteria: none. This change only keeps an earlier story's guard green beside criterion 1. The criteria stay mapped as in entry 8.

    Files created: none. Changed: `tests/test_claude_agent_texts_review_groups.py`, the body of `test_the_rest_of_the_reviewer_body_is_unchanged` only, under the human's leave in entry 11.

    Modules the test run could not import: none. `uv run pytest -q tests/test_claude_agent_texts_review_groups.py` passes all 9 tests, because the reviewer text is already in place. `make lint` is green.

    `lint`: lint: green (0.1 s)

    `lint`: lint: green (0.2 s)
16. factory: started doing as vm.
17. coder: `make check` is green, and I changed no files in this run. The work was already in place before this run started:

    - `claude/agents/reviewer.md`: in the notes paragraph, the human's three sentences from journal entry 4 replace the old sentence, word for word. That edit was committed with the earlier doing run (entry 10).
    - `tests/test_claude_agent_texts_review_groups.py`: the tester's change to the CRC test, made under the human's leave in entry 11 (entry 15).

    Results of this run:
    - `make check` ends with `check: green`. Coverage is 99.56 %.
    - The smoke test `grep -c 'handles that side' claude/agents/reviewer.md` prints `1`, as the story expects.

    Main choice: I copied the human's text exactly as written. I rejected rewording the reviewer text so that the earlier CRC guard would still pass without a test change. The human fixed the words in entry 4 and chose the test change in entry 11, option (a).

    Refactor: nothing to change. Against `main`, the diff outside the tests and `factory/` is one replaced line in `claude/agents/reviewer.md`.

    What the journal changed: the human's answers (entries 4 and 11) fixed the exact wording and approved the CRC test change. The intake already wrote both into the Interface, so I did not touch `## Description`.

    Not touched:
    - The `docs/decisions.md` entry from criterion 4. That is the docs stage's work.
    - The `CLAUDE.md` *Tests* line "the reviewer counts an untested side as a finding". It belongs to the human and is changed with this story's merge.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
18. factory: started review as vm.
19. reviewer: no findings

    What I checked:
    - Group 1, acceptance criteria. Criterion 1: the three sentences in `claude/agents/reviewer.md:66` match the human's text in journal entry 4 word for word, including the clause "One exception holds from round 0". `tests/test_claude_agent_texts_review_leave.py` `_NOTES` pins the same text through `test_agent_section_holds_the_review_leave_text[reviewer-notes]`. The adjacency rows `[notes-follow-recommendation]` and `[added-criterion-follows-notes]` stop the old sentence from closing the paragraph. Criterion 2: every other sentence of `_NOTES` is unchanged in the diff. Criterion 3: the coder's `make check` was green (entry 17). Criterion 4 is the docs stage's work. The Interface states no input rule or limit, so no failing side is missing.
    - Group 2, architecture: nothing under `src/` changed.
    - Group 3, security: no markers, secrets or code.
    - Group 4, quality: the two local strings in the CRC test say what they hold. There is no dead code or duplicated helper.
    - Group 5, work item hygiene: the Description matches what was built. The journal records the main choice (copy the human's words as given) and what was rejected (rewording to keep the CRC). The docs criterion still says what `docs/decisions.md` must gain.

    Open for the human, not a finding: two other lines in `claude/agents/reviewer.md` keep the general rule. The lesson at line 85 ("Count as a finding a stated limit tested on one side only") and checklist item 1 at line 55 ("every stated limit is tested on both sides") still read that way. The new sentence calls itself "One exception", so it limits them. Unlike the copied-helper sentence, though, it does not name "your lessons". Rewording them is outside this story's Interface ("every other sentence of the paragraph stays"). The same goes for the `CLAUDE.md` *Tests* line, which the human changes with the merge.

    Earlier tests:
    - `tests/test_claude_agent_texts_review_leave.py`: under the feature's leave for S0017 in `feature.md` (only the pinned sentence that counted an untested side as a finding). Only the last sentence of `_NOTES` changed.
    - `tests/test_claude_agent_texts_review_groups.py`: under the human's leave in journal entry 11. Only the body of `test_the_rest_of_the_reviewer_body_is_unchanged` changed: it now also swaps the three new sentences back to the old one before it takes the CRC. `_EARLIER_BODY_CRC32`, the test's name and the rest of the module are unchanged.
20. factory: started docs as vm.
21. documenter: I changed one file, `docs/decisions.md`. I appended one entry, *A missing test row for a side the code handles is a note*, as docs criterion 4 asks. It states the rule (a handled side with no test is a note; an unhandled side is still a finding; it holds from round 0). It names the three answers it comes from (S0001 entry 33, S0003 entry 30, S0005 entry 26). It says the tester's both-sides rule is unchanged. It gives the rejected alternative: sending every missing row back, which cost a round each time. It also records that the reviewer's lesson on one-side-tested limits and checklist item 1 keep their wording and are limited by the exception. I wrote only documents, so I did not run `make check`; the factory's checks decide.

    Cross-read and found current: README.md, docs/operator-guide.md and docs/project-guide/ (a grep for "untested side" and "both sides" found no mention of the rule). The diff touches only the one sentence in `claude/agents/reviewer.md` and two text tests, so no names, behaviours or examples in those documents moved. I checked the smoke test: `grep -c 'handles that side' claude/agents/reviewer.md` prints 1 per the coder's run.

    Stale text I saw and did not touch:
    - `CLAUDE.md` (*Tests*) still says "the reviewer counts an untested side as a finding". It is the human's file, changed with the merge, as the story says.
    - `claude/agents/reviewer.md` line 85 (the lesson "Count as a finding a stated limit tested on one side only") and checklist item 1 at line 55 still state the general rule. The new sentence calls itself an exception, but rewording these is outside the story's Interface. The reviewer already flagged this to the human.

    No findings for the coder.

    `check`: check: green (not run again: passed on tree fc98844c97fd at 2026-11-03T07:54:11Z)
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok
22. factory: started smoke-test as vm.
23. smoke-tester: I ran the smoke test from the repository root, exactly as written. I changed nothing.

    Command 1: `grep -c 'handles that side' claude/agents/reviewer.md`

    ```
    1
    ```

    Expect: `1`. Met.

    Checked against the acceptance criteria:
    - Criterion 1: `claude/agents/reviewer.md:66` holds the human's three sentences from journal entry 4, word for word. That includes "One exception holds from round 0". The old parenthetical "(an untested side of a stated limit among them)" is no longer in the file: a grep for "untested side" finds nothing.
    - Criterion 2: the rest of the notes paragraph on line 66 reads as before. The text tests that pin it were green in the coder's `make check` (entry 17). I did not run them again: running them is not part of the smoke test.
    - Criterion 3: the coder's `make check` was green (entry 17), and the docs stage reused that result (entry 21). I did not run it again.
    - Criterion 4: `docs/decisions.md:1360` has the entry "A missing test row for a side the code handles is a note".

    The smoke test contradicts no criterion.

    Findings: none.

    Open, not a finding (already raised by the reviewer and the documenter): the `CLAUDE.md` *Tests* line, the reviewer's lesson at line 85 and checklist item 1 at line 55 still state the general both-sides rule. `CLAUDE.md` is the human's to change with the merge, and rewording the other two is outside this story's Interface.
24. factory: done (pull request merged); cost: 10 runs, 8.0 min, 55 turns, 156414 tokens in (878364 more from cache), 15974 out, $1.48
