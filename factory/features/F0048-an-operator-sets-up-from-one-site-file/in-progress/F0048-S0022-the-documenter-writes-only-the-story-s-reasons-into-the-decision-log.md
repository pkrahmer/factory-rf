---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 524
comments_read: [6604990127]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T13:17:30.791116Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T13:17:30.797353Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-03T13:18:06.812345Z'
  stage: intake
  run: 78738c4bd07b4f53a5e3fd1e076ba65b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-03T13:18:15.726390Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-03T13:18:47.181525Z'
  stage: tests
  run: 42e7e5b734ff47ca83daa3c1cdf78073
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-03T13:18:53.031626Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-11-03T13:21:17.099645Z'
  stage: doing
  run: 97ad538ed816430a8afedf0658ef0612
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-11-03T13:25:17.944790Z'
  stage: doing
---

# The documenter writes only the story's reasons into the decision log

<!-- proposed by feature acceptance of 2026-11-03; refine before starting -->

## Description

F0048-S0019's documenter wrote seven decision log entries with "Why" and "Rejected" lines it read from the scripts and the operator guide. Five of the rejected options were named by no decision and no journal, and later agents cite the log as the human's reasons (R4). Decision 27 of F0048 says the decision log holds only the human's reasons, and F0048-S0021 repaired those entries one by one. The rule itself is written nowhere an agent reads it: the shipped `claude/agents/documenter.md` says what to write and where, but not where a decision entry's reasons come from, and its stage forbids it to read `feature.md`. So the next feature's documenter can do the same again. This story adds one lesson to the shipped documenter: a "Why" or a "Rejected" in `docs/decisions.md` comes from the story itself (its Description, Interface, docs criterion or journal, where the human's answers stand), never from the documenter's own reading of the code. Where the story names no rejected option, the entry has no "Rejected" line, and the documenter's journal entry names the entry that lacks one. The other lessons, the role and the stage of the documenter stay as they are, and no other agent's text changes. Existing entries of the log stay as they are.

## Interface

- `claude/agents/documenter.md`, `## Lessons`: one new bullet, placed after the bullet on the project guide's size ("The project guide is an index plus one file for each domain ...") and before the temporary-directory bullet, so that the documents-only lesson stays last. Its text, word for word:

  ```text
  - In `docs/decisions.md`, write a "Why" or a "Rejected" only from what the story names: its Description, its Interface, its docs criterion and its journal, where the human's answers stand. Never add a reason or a rejected option of your own reading of the code or the documents. When the story names no rejected option for an entry, write no "Rejected" line, and name that entry in your journal entry.
  ```

- No module under `src/factory/` changes. The template's pipeline definition and the other six shipped agents stay as they are.
- `tests/test_claude_agent_texts_decision_log.py` (new) pins the bullet in the documenter's `## Lessons` section (`section_text(agent_body("documenter"), "Lessons")`, as `tests/test_claude_agent_texts_review_leave.py` does), its place between the two bullets named above, and its absence from every other shipped agent (`SHIPPED_NAMES` of `tests/shipped_agents.py`).

## Acceptance criteria

1. The `## Lessons` section of `claude/agents/documenter.md` holds the bullet of the Interface word for word; a body without it fails the test.
2. The bullet stands directly after the project guide's bullet and directly before the temporary-directory bullet, and the documents-only bullet is still the section's last; a body with the bullet elsewhere in the section fails the test.
3. No other shipped agent (`intake`, `tester`, `coder`, `reviewer`, `smoke-tester`, `acceptance-reviewer`) holds the bullet: one parametrized test, a row for each agent, the documenter's row holding it and the six others not.
4. `make check` stays green.
5. docs: `docs/decisions.md`: one entry for the rule (decision 27 of F0048: the decision log holds only the human's reasons), with S0019's five unsourced "Rejected" options as its reason and the rejected alternative of letting the documenter read `feature.md` (its stage keeps it to the story). `docs/project-guide/agents.md`: the paragraph on the `## Lessons` sections names the new documenter lesson. `README.md` and the operator guide: none, since they say nothing about the agents' lessons.

## Smoke test

```bash
grep -c 'write a "Why" or a "Rejected" only from what the story names' claude/agents/documenter.md
```
Expect: `1`

```bash
grep -l 'write a "Why" or a "Rejected" only from what the story names' claude/agents/*.md
```
Expect: one line, `claude/agents/documenter.md`

```bash
uv run pytest tests/test_claude_agent_texts_decision_log.py 2>&1 | tail -1
```
Expect: a line that ends `passed` with no `failed` in it, for example `8 passed in 0.31s`

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names one concrete file (`claude/agents/documenter.md`, `## Lessons`), the bullet's exact text, its place (after the project guide bullet, line 74, before the temporary-directory bullet, line 75; the documents-only bullet is already last) and the new test module. The helpers it cites exist (`tests/shipped_agents.py` with `SHIPPED_NAMES` and `agent_body`; `section_text` in `factory.domain.sections`). No `src/` change.
   - Criteria: 1 (exact text present), 2 (position between the two bullets, documents-only still last) and 3 (one parametrized test, documenter holds it, six others do not) are each testable by one test function. The Interface states no rule with a failing side beyond these: "absent elsewhere" is criterion 3 and "elsewhere in the section" is criterion 2. The behaviours in the bullet (no Rejected line, name the entry in the journal) are the bullet's text, pinned word for word by criterion 1. Criterion 4 is `make check`; criterion 5 is the docs criterion.
   - Smoke test: the two greps are runnable and have checkable Expect lines (`1`, and one line naming the documenter). The pytest command passes no `-q`, and `pyproject.toml` already sets `-q` in `addopts`, so `tail -1` shows a summary line ending in `passed`.
   - Architecture: the change is a text in the shipped agent files under `claude/`, covered by the coder's write paths (`claude/*`). Its test sits at the `tests/` root with the other agent-text tests. No layer is touched.
   - Scope: within F0048 (decision 27, the decision log holds only the human's reasons). It changes nothing from "Out of scope" (no `src/factory/` change, no other agent's text). The Description's "the other lessons stay" matches the Interface. Nothing is carried in from a journal answer.
4. factory: started tests as vm.
5. tester: Wrote the tests for criteria 1 to 3. They fail now because the bullet is not in the documenter's text yet.
   - criterion 1: tests/test_claude_agent_texts_decision_log.py::test_documenter_lessons_hold_the_decision_log_bullet. The Interface's bullet, word for word, must be one line of the documenter's `## Lessons` section.
   - criterion 2: tests/test_claude_agent_texts_decision_log.py::test_decision_log_bullet_stands_between_the_guide_and_temporary_bullets. The line just before the bullet must be the project guide bullet and the line just after it the temporary-directory bullet. The section's last line must still be the documents-only bullet. The test matches those three neighbours by how their lines start.
   - criterion 3: tests/test_claude_agent_texts_decision_log.py::test_only_the_documenter_holds_the_decision_log_bullet. Parametrized over `SHIPPED_NAMES`, one row per agent: the documenter's body must hold the bullet and the six others must not.
   - criteria 4 and 5: no tests (`make check` and the docs criterion).

   Files created: tests/test_claude_agent_texts_decision_log.py. It reuses `section_text` and `shipped_agents.agent_body`/`SHIPPED_NAMES`, as tests/test_claude_agent_texts_review_leave.py does. The lesson lines are a fixture shared by the first two tests.

   Test run (`uv run pytest -q` on the new file): 3 failed with AssertionError, because the bullet is not yet in claude/agents/documenter.md: the presence test, the position test and the `documenter` row of the parametrized test. The six other rows pass, as they should. There were no import or collection errors, and every module imported. `make lint` is green.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: Stopped at `make check`: an earlier story's test pins the documenter's whole `## Lessons` list, so the Interface's bullet can't pass without changing that test. I didn't change the test.

   - Built: `claude/agents/documenter.md`, `## Lessons`. The Interface's bullet is in word for word, after the project-guide bullet and before the temporary-directory bullet. The documents-only bullet is still last. I left this edit in the working tree. The new test module `tests/test_claude_agent_texts_decision_log.py` should pass with it; I didn't run it alone.
   - Red: `make test` has exactly one failure: `tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets[documenter] - assert ['- Run `make...step 3 says.'] == ['- Run `make...step 3 says.']`. That test (line 276) checks that each shipped agent's `## Lessons` lines equal `LESSONS[name]` exactly. `LESSONS["documenter"]` (from line 91) has the five old bullets. Both the Interface and that table hold for themselves, but together they can't pass. The test was written by another story, and the standing leave covers only moving shared helpers, so changing it needs your word (R9).

   Options:
   - (a) The tester adds the new bullet to `LESSONS["documenter"]` in `tests/test_claude_agent_texts.py`, between the project-guide entry and `_TEMPORARY_DIRECTORY_LESSON`. The test still checks what it did, with the documenter's new list. I'd choose (a). With your answer I end with `tests` and name this change.
   - (b) Drop the bullet from the documenter. That undoes the story.
   - (c) Change the old test to stop pinning the full list for the documenter. That weakens a test of another story.

   Noticed but not touched: nothing else. No `src/` change, so nothing to refactor yet.
8. 2026-11-03 human: (a). The tester has leave to add the new bullet to `LESSONS["documenter"]` in `tests/test_claude_agent_texts.py`, between the project-guide entry and `_TEMPORARY_DIRECTORY_LESSON`, and nothing else in that module. The test keeps its name and still pins the documenter's whole list.

   — Kumpel, for the human who owns this project
   <!-- kumpel -->
