# The reviewer judges all five groups in every review

## Description

The shipped reviewer (`claude/agents/reviewer.md`) stops at the first failing group of its checklist (acceptance criteria, architecture, security, quality, work item hygiene) and reports only that group. A story whose group 1 has a gap therefore learns about groups 2 to 5 only in a later round, and each round costs a coder run, a tester run and a review. In F0048, S0001, S0003 and S0005 each reached the round cap this way (the night log of 2026-11-02); in S0005, after the human told the review to judge all five groups at once, one review found the one remaining point, and it was settled by a question instead of another round. This story makes that the rule: every review goes through all five groups and reports every finding of every group in one entry. It changes nothing else of the reviewer: what counts as a finding or a note, the criteria the reviewer may add, the corrected Description, item 6 and the decision (`docs` with no finding, `doing` with any) stay as they are.

## Interface

`claude/agents/reviewer.md`, its *Role* section: the sentence before the checklist reads, in place of today's, `Checklist, in this order. Go through all of groups 1 to 5 in every review, also when an earlier group fails, and report every finding of every group in this one entry; do not pad the report. Item 6 is part of every review.` The words `Stop at the first failing group` appear nowhere in the reviewer's body. No other agent file changes.

Tests (the tester writes them): the shipped-agent text tests are the pattern (`tests/test_claude_agent_texts.py`); a new module `tests/test_claude_agent_texts_review_groups.py` holds this story's. `test_the_reviewer_no_longer_stops_before_the_earlier_tests` in `tests/test_claude_agent_texts.py` passes unchanged.

## Acceptance criteria

1. The reviewer's body holds the sentence of the Interface, word for word, directly before the checklist's item 1.
2. The reviewer's body does not hold `Stop at the first failing group`, and no other shipped agent's body holds `Go through all of groups 1 to 5`.
3. The rest of the reviewer's body is unchanged: its items 1 to 6, the paragraphs on notes from round 1 on, on adding a criterion and on correcting the Description, and its *Stage* and *Lessons* sections are byte for byte those of `main` before this story (a test compares the body with the sentence of the Interface replaced back).
4. `make check` stays green.
5. docs: `docs/project-guide/agents.md`, the line on the reviewer's checklist: the reviewer goes through all five groups in every review and item 6 is always part of it (no longer "it stops at the first failing group"); `docs/decisions.md`: an entry *The reviewer judges all five groups in every review*, with the reason (a round per group, three round caps in F0048) and the date 2026-11-02; `README.md` and the other documents: none.

## Smoke test

```bash
grep -c "Go through all of groups 1 to 5 in every review" claude/agents/reviewer.md
grep -c "Stop at the first failing group" claude/agents/reviewer.md
```

Expect: two lines, `1` and `0`.

## Journal
