---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 513
comments_read: [6598169268]
handed_over: null
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
