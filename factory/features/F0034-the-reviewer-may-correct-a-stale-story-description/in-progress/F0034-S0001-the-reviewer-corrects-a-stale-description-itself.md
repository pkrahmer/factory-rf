---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 328
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T03:54:43.210047Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T03:54:43.215728Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T03:54:58.544764Z'
  stage: intake
  run: 1b5acae23a004518ba612ac527dedc42
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T03:55:18.972306Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T03:57:20.291505Z'
  stage: tests
  run: a0c12a0503ad410d8ab44a40ea4c705b
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T03:57:40.847703Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T03:59:43.842106Z'
  stage: doing
  run: 7f072df7199f4c4cad8f13aadb147802
---

# The reviewer corrects a stale Description itself

## Description

On 2026-10-19 the human decided that the reviewer may rewrite a story's `## Description` when it has gone stale against what the story built. Until now a stale Description was a finding that no later stage could fix. F0026-S0002's coder was refused the work item and asked. F0019-S0003's reviewer asked the human. F0025-S0002's "Three smaller passages" above a list of two went to `done/` unchanged, although four stages noted it. The work item is already in the reviewer's write paths. This story adds one paragraph to the shipped reviewer's *Role*. The reviewer rewrites the stale sentences itself, when the human's answers in the journal, the Interface or the criteria already settle what the Description should say. It names the correction in its entry as `description corrected: <what it said> -> <what it says now>`. The correction is not a finding, so with no other finding the reviewer ends with `docs`. A Description the code contradicts while nothing settles which is right stays a finding, or a question when no stage can fix it. Unchanged: the checklist (item 5 keeps its words), the reviewer's other paragraphs, its front matter and lessons, and the six other agents. Nothing under `src/` changes.

## Interface

No module under `src/factory/` changes. The coder changes one file, `claude/agents/reviewer.md`, and nothing else in it.

`claude/agents/reviewer.md`, the section *Role*: after the paragraph that begins `When the diff builds a behaviour that no criterion names` and ends `A criterion that needs a code change stays a finding or a question.`, one blank line and then this paragraph, followed by one blank line before the `## Stage` heading:

```markdown
When the work item's `## Description` has gone stale against what the story built, and the human's answers in the journal, the Interface or the criteria already settle what it should say, rewrite the stale sentences of the Description yourself and change nothing else in the work item. Name the correction in your entry as `description corrected: <what it said> -> <what it says now>`, one line each. A correction is not a finding: with no other finding, end with `docs`. A Description that the code contradicts while neither the journal nor the Interface nor the criteria settle which is right stays a finding, or a question when no stage can fix it.
```

- Item 5 of the checklist keeps its exact line: ``5. **Work item hygiene**: the journal explains the main decision and what was rejected; the `## Description` matches what was built; the docs criterion still describes what the reader must know after this story (the documenter writes it next, from that criterion).``
- No other agent file gains the text `description corrected:`.

Tests (the tester writes them): `tests/test_claude_agent_texts_description.py` (new), through `agent_body` of `tests/shipped_agents.py` and `section_text` of `factory.domain.sections`, as `tests/test_claude_agent_texts_review_leave.py` reads the reviewer's other paragraphs. That module and `tests/test_claude_agent_texts.py` pass unchanged.

## Acceptance criteria

1. The paragraph of the Interface, the whole text from `When the work item's` to `when no stage can fix it.`, is in `section_text(agent_body("reviewer"), "Role")`.
2. It follows the added-criterion paragraph and ends before `## Stage`: `agent_body("reviewer")` holds the added-criterion paragraph's last sentence `A criterion that needs a code change stays a finding or a question.`, then exactly one blank line (`"\n\n"`), then the paragraph's first words `When the work item's`; and it holds the paragraph's last words `when no stage can fix it.` followed by exactly `"\n\n## Stage"`.
3. Only the reviewer carries the rule (rows of one parametrized test, one per shipped agent, each the count of `description corrected:` in `agent_body(<name>)`): `reviewer` 1, and `intake`, `tester`, `coder`, `documenter`, `smoke-tester` and `acceptance-reviewer` each 0.
4. Item 5 of the checklist is unchanged: its line as the Interface gives it occurs exactly once in `section_text(agent_body("reviewer"), "Role")`.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, *The reviewer's notes and added criteria*, a new last paragraph, and the section's first sentence ("Two things in a reviewer's entry ...") counts the correction too. When a story's Description has gone stale against what it built, and the human's answers, the Interface or the criteria settle what it should say, the reviewer rewrites the stale sentences itself. Its entry names each correction as `description corrected: <what it said> -> <what it says now>`. That is not a send-back and counts no round; read those lines at the approval. A Description the code contradicts with nothing to settle it still comes back as a finding or a question. `docs/decisions.md`: an entry *The reviewer corrects a stale Description*, dated with the story, from the feature's decisions 1 to 3. Its reasons are the human's decision of 2026-10-19 and the stale Descriptions of F0019-S0003, F0025-S0002 and F0026-S0002. It rejects giving the coder the work item (a second writer of the story's text) and leaving it to the human (a question about nothing the human decides). `docs/operator-playbook.md`, section 3, check 2 at approval (*The reviewer.*): after "and any `criterion <n> added`", add "and any `description corrected:`". `README.md` and the project guide: none, since neither describes the reviewer's checklist.

## Smoke test

```bash
grep -c -F 'description corrected:' claude/agents/*.md
```
Expect: seven lines, `claude/agents/acceptance-reviewer.md:0`, `claude/agents/coder.md:0`, `claude/agents/documenter.md:0`, `claude/agents/intake.md:0`, `claude/agents/reviewer.md:1`, `claude/agents/smoke-tester.md:0`, `claude/agents/tester.md:0`

```bash
grep -c -F '5. **Work item hygiene**: the journal explains the main decision and what was rejected; the `## Description` matches what was built;' claude/agents/reviewer.md
```
Expect: `1`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: one file, `claude/agents/reviewer.md`, section *Role*. The anchor paragraph (line 68, ending `A criterion that needs a code change stays a finding or a question.`) and the `## Stage` heading (line 70) exist as the Interface describes. The new paragraph's text is given in full. The helpers it names exist (`agent_body` in `tests/shipped_agents.py`, and the sibling module `tests/test_claude_agent_texts_review_leave.py`).
   Criteria: 1 and 2 are the paragraph's text and its place, with exact boundaries. 3 is one parametrized test with a row per agent (reviewer 1, the six others 0). 4 is the unchanged item 5, which occurs once. 5 and 6 are the closing criteria. Each is testable by one test function. Every clause of the paragraph (the correction, the entry format, "not a finding" with `docs`, and the finding-or-question side where nothing settles it) lies inside the exact text that criterion 1 pins. The failing side of "only when settled" is therefore pinned by that text.
   Smoke test: both greps are runnable. The expected counts (seven lines with 0 or 1, and `1`) can be checked against the output.
   Architecture: nothing under `src/` changes, so the layers are untouched. The change is an agent file under `claude/`, which the coder writes. The tests are under `tests/` at the root, as for the other agent-text modules.
   Scope: it matches the feature's Scope and touches nothing in its Out of scope. No other agent changes, and there is no pipeline change. The story edits no test another story wrote, and the new test module is its own.
4. factory: started tests as self.
5. tester: Tests written for criteria 1 to 4 in one new module, reading the reviewer's text through `agent_body` (tests/shipped_agents.py) and `section_text` (factory.domain.sections), the same way tests/test_claude_agent_texts_review_leave.py does.
   criterion 1: tests/test_claude_agent_texts_description.py::test_reviewer_role_holds_the_description_correction
   criterion 2: tests/test_claude_agent_texts_description.py::test_description_correction_sits_between_added_criterion_and_stage (rows `after-added-criterion`: the added-criterion paragraph's last sentence + "\n\n" + `When the work item's`; `before-stage`: `when no stage can fix it.` + "\n\n## Stage")
   criterion 3: tests/test_claude_agent_texts_description.py::test_only_the_reviewer_names_a_description_correction (one row per name in `SHIPPED_NAMES`: reviewer 1, the other six 0)
   criterion 4: tests/test_claude_agent_texts_description.py::test_reviewer_checklist_keeps_its_work_item_hygiene_item
   criterion 5: `make check` (the coder's gate), no test of its own.
   criterion 6: docs, no test.
   File created: tests/test_claude_agent_texts_description.py. No other test file changed.
   Every module imported; nothing failed to import. `make test` fails as intended. These 4 fail because the paragraph is not in claude/agents/reviewer.md yet: the criterion-1 test, both rows of the criterion-2 test, and the `reviewer` row of the criterion-3 test. The criterion-4 test and the six 0-count rows pass already, because they check text that must stay unchanged. `make lint` is green. The type check was skipped, as this stage says.
   Rejected: listing the seven agent names by hand in the criterion-3 test. `SHIPPED_NAMES` already holds exactly those seven, and tests/test_claude_agent_refusal.py parametrizes over it the same way.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/test_claude_agent_texts_description.py::test_description_correction_sits_between_added_criterion_and_stage[before-stage]
6. factory: started doing as self.
7. coder: Built: `claude/agents/reviewer.md`, section *Role*. I added the Interface's paragraph word for word, after the added-criterion paragraph and before `## Stage`, with one blank line on each side. No other line in the file changed, and nothing under `src/` or `tests/` changed.
   Main choice: I copied the Interface's text exactly, because criteria 1 and 2 pin it to the character. I rejected rewording it or merging it into checklist item 5, since criterion 4 keeps item 5's exact line.
   Refactor: I read the diff (2 inserted lines). Nothing needed changing.
   Checks: `make check` is green (`check: green`), and the four new tests in tests/test_claude_agent_texts_description.py pass. The first smoke-test grep gives the expected seven counts: reviewer 1, the other six 0.
   The journal does not change what the task means, so the Description stays as it is.
   Noticed but not touched: the docs criterion (operator guide, decision log, playbook) is for the documenter.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
