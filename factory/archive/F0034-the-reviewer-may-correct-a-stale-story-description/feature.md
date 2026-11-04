# The reviewer may correct a stale story Description

## Goal

A story's `## Description` is the current meaning of its task (rule R5), and the documenter writes from it and from the docs criterion. Several times it went stale against what the story built, and no stage could put it right. F0025-S0002's Description says "Three smaller passages" above a list of two. Intake, the coder, the reviewer and the documenter each noted it, and it was archived that way. F0026-S0002's says "This story pins all of that", although line 87 of `watch.py` stays uncovered. The reviewer made it a finding, and the coder could not write the work item (`Permission denied`) and asked. The human answered (a) in entry 14, and the archived Description still holds the old sentence. F0019-S0003's reviewer asked the human who should bring the Description in line with entry 12. Yet the work item is in the reviewer's own write paths (`factory/pipeline.yml`, `reviewer: {write_paths: ["{work_item}"]}`). The human decided on 2026-10-19 that the reviewer may rewrite a story's Description when it has gone stale against what the story built. This feature gives the shipped reviewer that rule. Then the human's answer or a criterion that settles the meaning reaches the Description in the review stage, with no send-back and no question. It is for the human, who reads the Description at the approval, and for the documenter, who writes from it. Done when every story below is merged and `make check` is green.

## Scope

- `claude/agents/reviewer.md`, the section *Role*: one paragraph after the one on the added criterion (S0001).
- `tests/test_claude_agent_texts_description.py` (new): the paragraph, its place, and that only the reviewer carries it (S0001).
- `docs/operator-guide.md`, `docs/decisions.md` and `docs/operator-playbook.md`, from the story's docs criterion (S0001).

## Out of scope

- The Interface, the criteria and the smoke test: the reviewer still corrects none of them. Its added criterion (F0021-S0005) stays as it is, and every other wrong text stays a finding or a question.
- The other agents: intake already rewrites the Description from the human's answer (its step 1). The coder, the tester, the documenter and the smoke tester do not write the work item's text.
- Archived stories in `done/`: they stay as they are.
- `factory/pipeline.yml`: the reviewer's write paths already hold `{work_item}`.
- The factory's code: nothing under `src/` changes.
- Every paid call: no story and no smoke test makes one.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The reviewer corrects a stale Description itself
- S0002: The playbook and the project guide say the reviewer corrects a stale Description (proposed by A0001)

## The human's changes

None. Checked against `factory/pipeline.yml`: the coder writes `claude/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`, and the reviewer already writes its own work item. `docs/operator-playbook.md` is named by the docs criterion, which the project's `CLAUDE.md` (*Docs*) allows.

## Decisions taken for the human

1. The Description is corrected only when the human's answers in the journal, the Interface or the criteria already settle what it should say. The account of the coder or the tester alone is not enough, since the reviewer "must not trust the work item's own account" (its *Role*). A Description that the code contradicts while nothing settles which is right stays a finding, or a question when no stage can fix it (S0001).
2. The correction is not a finding: with no other finding the reviewer ends with `docs`. So it costs no round and no question, and the entry line `description corrected: <what it said> -> <what it says now>` lets the human see it at the approval (S0001).
3. The reviewer changes the stale sentences of the Description alone and nothing else in the work item. Item 5 of the checklist (*Work item hygiene*) keeps its words (S0001).
4. The new paragraph lies in its own test module, `tests/test_claude_agent_texts_description.py`, so `tests/test_claude_agent_texts_review_leave.py` (F0021-S0005) stays unchanged and needs no leave (S0001).
