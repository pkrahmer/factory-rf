---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 503
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-02T19:42:35.716893Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-02T19:42:35.723101Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-02T19:43:15.756650Z'
  stage: intake
  run: 40254bec641c4b90b2dd242aab00aa5d
---

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

1. 2026-11-02 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names the concrete file `claude/agents/reviewer.md`, its Role section, and gives the replacement sentence word for word. Today's line (line 53) matches the "today's" it replaces. Test module and the unchanged existing test are named. The existing test at tests/test_claude_agent_texts.py:272 only asserts the old phrase "Stop at the first failing group and report it" is absent, so it still passes.
   - Criteria: 1 (exact sentence directly before item 1), 2 (old phrase absent; the new phrase absent from the other agents' bodies), 3 (rest of the body is byte-for-byte unchanged, compared against the body with the sentence put back) and 4 (`make check`) are each testable by one test function. The Interface states no limit, validation or error, so there is no failing side to cover. Criterion 5 is the docs criterion, and its targets are named.
   - Smoke test: two grep -c commands, runnable. The Expect line (`1` and `0`) can be checked against the output. No pytest command, so there is no `-q` concern. Note that `grep -c` exits 1 on a zero count, which is harmless for the check.
   - Architecture: only a shipped agent text under `claude/` changes. No layer or code is touched, and the file lies within the coder's write paths.
   - Scope: within F0048 (listed as S0011 in its Scope and Stories, and decision 15). Nothing in the feature's Out of scope is touched, and no other agent file changes.
