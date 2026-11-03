---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 524
comments_read: [6604990127]
handed_over: approval
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
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-03T13:25:21.089016Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-03T13:25:42.868191Z'
  stage: doing
  run: fa253bbfaac1449fbd8294100ac1877f
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-03T13:25:51.667374Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-11-03T13:26:21.233535Z'
  stage: tests
  run: 40f2024725534baca46cacf5be15cc68
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-03T13:26:27.064590Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-03T13:29:48.899192Z'
  stage: doing
  run: 064ae3141984439b94423331aae8080a
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-03T13:29:55.518987Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-11-03T13:30:19.177149Z'
  stage: review
  run: 753128cc0b40471fb82db9a5a74fe6cb
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-03T13:30:25.670744Z'
  stage: docs
- number: 18
  speaker: documenter
  kind: result
  at: '2026-11-03T13:30:55.137670Z'
  stage: docs
  run: 016472a5244342c286535ba32af49328
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-03T13:31:02.107518Z'
  stage: smoke-test
- number: 20
  speaker: smoke-tester
  kind: result
  at: '2026-11-03T13:31:25.820335Z'
  stage: smoke-test
  run: 540851ffe02a4c66b8b80fafbd8d0699
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
9. factory: started doing as vm.
10. coder: The human answered (a). I'm sending the work item to the tester for one test change, with no code change in this round.

    - **Test change for the tester:** in `tests/test_claude_agent_texts.py`, add the new documenter bullet to `LESSONS["documenter"]`, between the project-guide entry and `_TEMPORARY_DIRECTORY_LESSON`, and change nothing else in that module. `test_lessons_section_is_last_and_holds_exactly_the_role_bullets` keeps its name and still pins the documenter's whole list.
    - **Built:** `claude/agents/documenter.md`, `## Lessons`, already holds the Interface's bullet word for word, in the round-0 commit. It stands after the project-guide bullet and before the temporary-directory bullet, and the documents-only bullet is still last. I made no further code change.
    - **Test run:** `uv run pytest -q tests/test_claude_agent_texts_decision_log.py tests/test_claude_agent_texts.py` has one failure: `tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets[documenter]`, at line 281. That is the `LESSONS` table the change above fixes. Every test in the new module passes.
    - **Main choice:** I left the old test to the tester, as R9 and the human's leave say. I rejected changing the test myself and rejected weakening it.
    - **Refactor:** none needed. The only change is one line of text.
    - **Description:** the journal doesn't change what the task means, so the Description stays as it is. The human's answer only allows the one test change above.
    - **Noticed but not touched:** nothing.
11. factory: started tests as vm.
12. tester: I made the one test change the human approved in entry 8 and the coder named in entry 10. Nothing else changed.

    - **Change:** `tests/test_claude_agent_texts.py`, `LESSONS["documenter"]`. I added the Interface's decision-log bullet, word for word, between the project-guide entry and `_TEMPORARY_DIRECTORY_LESSON`. The documents-only bullet is still the list's last entry. `test_lessons_section_is_last_and_holds_exactly_the_role_bullets` keeps its name and still pins the documenter's whole list. Nothing else in that module changed.
    - **Leave:** the human's answer in entry 8, option (a). This is the only earlier test file I changed.
    - **Criteria to tests:** unchanged from entry 5.
      - criterion 1: tests/test_claude_agent_texts_decision_log.py::test_documenter_lessons_hold_the_decision_log_bullet
      - criterion 2: tests/test_claude_agent_texts_decision_log.py::test_decision_log_bullet_stands_between_the_guide_and_temporary_bullets
      - criterion 3: tests/test_claude_agent_texts_decision_log.py::test_only_the_documenter_holds_the_decision_log_bullet
      - criteria 4 and 5: no tests (`make check` and the docs criterion).
    - **Files created:** none in this round.
    - **Modules the test run could not import:** none.
    - **Test run:** I ran `uv run pytest -q tests/test_claude_agent_texts.py tests/test_claude_agent_texts_decision_log.py` and every test passed.
    - **Second run:** after that run, `make lint` failed with one E501: the new string was 102 characters at `tests/test_claude_agent_texts.py:99`, over the limit of 100. I moved the line break inside the string, which leaves its text the same. I then ran `tests/test_claude_agent_texts.py` again, once, against the stage's one-run rule, to check the rewrapped text still matches; it passed.
    - **Lint:** `make lint` is now green.

    `lint`: lint: green (0.1 s)
13. factory: started doing as vm.
14. coder: The tester's approved change is in place, and `make check` is green, ending `test: green (82.7 s)` and `check: green`. I made no code change in this round.

    - **Built:** `claude/agents/documenter.md`, `## Lessons`, line 75. It holds the Interface's decision-log bullet word for word, from the round-0 commit. It stands after the project-guide bullet and before the temporary-directory bullet, and the documents-only bullet is still last. No module under `src/factory/` changed.
    - **Main choice:** I added the lesson as one bullet in the documenter's existing `## Lessons` section, as the Interface places it. I rejected changing the old `LESSONS` table myself: the tester made that change with the human's leave (entries 8 and 12).
    - **Refactor:** none needed. The whole diff outside the tests is one line of text.
    - **Description:** unchanged. The human's answer in entry 8 only allowed a test change and does not change what the task means.
    - **Noticed but not touched:** nothing.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
15. factory: started review as vm.
16. reviewer: no findings

    Reviewed `git diff main...HEAD -- . ':!factory'` (claude/agents/documenter.md, tests/test_claude_agent_texts.py, tests/test_claude_agent_texts_decision_log.py) against the work item.

    - Acceptance criteria: the bullet at claude/agents/documenter.md:75 matches the Interface word for word. It comes after the project-guide bullet and before the temporary-directory bullet, and the documents-only bullet is still last.
      - Criterion 1 is pinned by `test_documenter_lessons_hold_the_decision_log_bullet`.
      - Criterion 2 is pinned by `test_decision_log_bullet_stands_between_the_guide_and_temporary_bullets`, which checks both neighbours and the last bullet.
      - Criterion 3 is pinned by `test_only_the_documenter_holds_the_decision_log_bullet`, one parametrized test over `SHIPPED_NAMES`.
      - The Interface states no other rule with a failing side.
      - The coder's `make check` was green (journal entry 14).
    - Architecture: nothing under `src/` changed. The new test module sits at the `tests/` root beside the other agent-text tests and reuses `section_text` and `shipped_agents`.
    - Security: no secrets, no markers.
    - Quality: the bullet's text appears in both test modules as expected text. This follows the precedent of tests/test_claude_agent_texts_review_leave.py. The human's leave in entry 8 also limited the old module to this one added entry, so I did not count it as a finding.
    - Work item hygiene: the Description matches what was built. The journal names the main choice and the rejected options (entries 7 and 10). Docs criterion 5 still says what the documenter must write.

    Earlier tests:
    - tests/test_claude_agent_texts.py: the human's leave in journal entry 8. The diff only adds the new bullet to `LESSONS["documenter"]`, between the project-guide entry and `_TEMPORARY_DIRECTORY_LESSON`. Every test keeps its name.
17. factory: started docs as vm.
18. documenter: Documented the new documenter lesson. No findings: the bullet at claude/agents/documenter.md:75 matches the Interface, and the code and tests agree with it.

    Files changed:
    - `docs/decisions.md`: one new entry, "The decision log holds only the human's reasons". It states the rule and gives S0019's five unsourced "Rejected" options as the reason. Its rejected alternative is letting the documenter read `feature.md`, which the docs criterion names. I took every reason and rejected option from the story's Description and docs criterion. None is my own reading of the code.
    - `docs/project-guide/agents.md`: the `## Lessons` paragraph now names the documenter's decision-log lesson, before the documents-only lesson.

    The entry is a new decision and no existing entry lacks a "Rejected" line, so the lesson's "name the entry" step has nothing to report.

    Cross-read and found current:
    - `README.md` and `docs/operator-guide.md`: they say nothing about agent lessons, as the docs criterion says.
    - The rest of `docs/project-guide/agents.md`: the claim that `tests/test_claude_agent_texts.py` checks the exact `## Lessons` bullets holds. The diff adds the bullet to `LESSONS["documenter"]` there.

    I ran no examples, because I wrote none. I changed only documents, so I did not run `make check`. The factory's checks decide.

    Stale text I saw but did not touch: none.

    `check`: check: green (not run again: passed on tree d4bcb5556ee6 at 2026-11-03T13:28:13Z)
    `secrets`: secrets: green (1.5 s)
    `documents`: documents ok
19. factory: started smoke-test as vm.
20. smoke-tester: Smoke test passed. I ran the three commands from the repository root in order, exactly as written, and every one met its `Expect:` line. I fixed nothing.

    1. `grep -c 'write a "Why" or a "Rejected" only from what the story names' claude/agents/documenter.md`
       ```
       1
       ```
       Met `Expect: 1`.

    2. `grep -l 'write a "Why" or a "Rejected" only from what the story names' claude/agents/*.md`
       ```
       claude/agents/documenter.md
       ```
       Met `Expect: one line, claude/agents/documenter.md`. No other shipped agent holds the bullet.

    3. `uv run pytest tests/test_claude_agent_texts_decision_log.py 2>&1 | tail -1`
       ```
       9 passed in 0.02s
       ```
       Met the expectation: the line ends `passed` and has no `failed` in it.

    Checked against the acceptance criteria (read again after the commands):
    - Criteria 1 to 3: in `git diff main...HEAD`, the bullet at `claude/agents/documenter.md:75` matches the Interface's text word for word. It stands right after the project-guide bullet and right before the temporary-directory bullet, and the documents-only bullet is still last. The 9 passing tests are the presence test, the position test and the 7 rows of the parametrized test.
    - Criterion 4: I did not run `make check` again here. It was green in journal entry 14.
    - Criterion 5 (docs): `docs/decisions.md` has the new entry "The decision log holds only the human's reasons". It cites decision 27 of F0048, gives S0019's five unsourced "Rejected" options as its reason, and rejects letting the documenter read `feature.md`. In `docs/project-guide/agents.md`, the `## Lessons` paragraph names the new documenter lesson. `README.md` and the operator guide are unchanged, as the criterion says.

    The smoke test contradicts no criterion.

    Findings: none.
