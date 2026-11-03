---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 513
comments_read: []
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
---

# A missing test row for a side the code already handles is a note

<!-- written by the human on 2026-11-03 from the acceptance F0048-A0001's decision 9 (decision 23) -->

## Description

Three times in F0048 (S0001 entry 33, S0003 entry 30, S0005 entry 26) the human answered the same question the same way: when the reviewer finds a side of a stated limit without a test, and the code already handles that side correctly, the missing test row is a note, not a reason to send the story back. Each time the question cost a wait or a round. The rule is written nowhere lasting: `claude/agents/reviewer.md` still says that "an untested side of a stated limit" is a finding, and `CLAUDE.md` (*Tests*) says that "the reviewer counts an untested side as a finding". This story writes the human's rule into the reviewer's text and the decision log, so that the question does not come again.

The reviewer must still read the code and confirm that it handles the side; a side the code gets wrong, or does not handle, stays a finding. The tester's rule to test every stated limit on both sides stays as it is: the change is only in what the reviewer sends back.

## Interface

- `claude/agents/reviewer.md`, the paragraph on notes: a stated limit's side that has no test is a note, not a finding, when the reviewer has read the code and it handles that side as the Interface says; the note names the side, the code's location and the missing row. A side the code does not handle, or handles otherwise, is still a finding. This holds from round 0. Every other sentence of the paragraph stays.
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
