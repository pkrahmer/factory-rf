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
