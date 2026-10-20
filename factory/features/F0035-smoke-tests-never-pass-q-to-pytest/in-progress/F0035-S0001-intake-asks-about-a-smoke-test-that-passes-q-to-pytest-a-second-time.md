---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 330
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T04:09:30.534300Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T04:09:30.540216Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T04:09:46.942220Z'
  stage: intake
  run: d2927e3a98e5442a800f42227aef9e14
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T05:00:28.018083Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T05:02:23.916118Z'
  stage: tests
  run: 1d03ba10977f455d9b31ec52e877d9b3
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T05:02:44.293061Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T05:04:45.903970Z'
  stage: doing
  run: 37468963f7d0449894750fe830c5af56
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T05:05:06.304214Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T05:05:35.497120Z'
  stage: review
  run: c9e525608282449d9c48812a56c01e8c
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T05:05:56.256239Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T05:06:22.309073Z'
  stage: docs
  run: 60f3b2954d1d4c50bd7d4f26847a238e
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T05:06:42.713224Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T05:07:00.501773Z'
  stage: smoke-test
  run: 8b2c667b2c864fd3a12fed845c38d03f
---

# Intake asks about a smoke test that passes -q to pytest a second time

## Description

A project whose pytest configuration already sets `-q` (this repository's `pyproject.toml`: `addopts = "-q --strict-markers"`) runs pytest at `-qq` when a smoke test passes `-q` again. At `-qq` pytest prints no summary line. On 2026-10-19 that alone failed the smoke tests of F0022-S0005 and F0023-S0004, with every test green, and it cost a question each. Intake checks that each smoke test command is runnable and that each `Expect:` can be checked against the output. This story adds the `-q` rule to that check, in intake's step 2. A smoke test command that runs pytest passes no `-q` when the project's pytest configuration already sets one, and a command that does is a question. The rule is general, because the shipped intake serves every project. The human's change 1 puts the same rule, in this repository's words, into `factory/story-form.md`. Unchanged: intake's other steps, its lessons and front matter, and the six other agents. Nothing under `src/` changes.

## Interface

No module under `src/factory/` changes. The coder changes one file, `claude/agents/intake.md`, and nothing else in it.

`claude/agents/intake.md`, the section *Stage*, step 2: its line ends today with ``the smoke test commands are runnable and each `Expect:` line says something the output can be checked against.`` That line gains, after one space, these sentences at its end, still on the same line:

```markdown
A smoke test command that runs pytest passes no `-q` when the project's pytest configuration already sets one (`addopts` in `pyproject.toml`, `pytest.ini`, `setup.cfg` or `tox.ini`): at `-qq` pytest prints no summary line, so an `Expect:` that counts or names it cannot be met. Such a command is a question.
```

- Step 2 still starts with `2. The factory has already checked the story's form`, and the steps keep their numbers 0 to 6.
- No other agent file gains the text ``passes no `-q` when the project's pytest configuration already sets one``.

Tests (the tester writes them): `tests/test_claude_agent_texts_smoke_pytest.py` (new), through `agent_body` of `tests/shipped_agents.py` and `section_text` of `factory.domain.sections`. `tests/test_claude_agent_texts.py` passes unchanged.

## Acceptance criteria

1. The new sentences, as the Interface gives them, are in `section_text(agent_body("intake"), "Stage")`.
2. They end step 2: the line of `section_text(agent_body("intake"), "Stage")` that starts with `2. The factory has already checked the story's form` holds ``each `Expect:` line says something the output can be checked against. A smoke test command that runs pytest passes no `-q` `` and ends with `Such a command is a question.`.
3. Only intake carries the rule (rows of one parametrized test, one per shipped agent, each the count of ``passes no `-q` when the project's pytest configuration already sets one`` in `agent_body(<name>)`): `intake` 1, and `tester`, `coder`, `reviewer`, `documenter`, `smoke-tester` and `acceptance-reviewer` each 0.
4. `make check` stays green.
5. docs: `docs/project-guide/agents.md`, *The seven agents*: one sentence after the list of an agent file's sections. Intake asks about a smoke test command that passes pytest a `-q` the project's pytest configuration already sets, because at `-qq` pytest prints no summary line. `docs/decisions.md`: an entry *A smoke test passes no -q that the pytest configuration already sets*, dated with the story, from the feature's decisions 1 to 4. Its reason: the smoke tests of F0022-S0005 and F0023-S0004 on 2026-10-19. It rejects a check in code (the factory knows no pytest) and a lesson line (pinned by another story's test). `README.md` and `docs/operator-guide.md`: none, since nothing the operator does changes.

## Smoke test

```bash
grep -c -F 'passes no `-q` when the project'"'"'s pytest configuration already sets one' claude/agents/*.md
```
Expect: seven lines, `claude/agents/acceptance-reviewer.md:0`, `claude/agents/coder.md:0`, `claude/agents/documenter.md:0`, `claude/agents/intake.md:1`, `claude/agents/reviewer.md:0`, `claude/agents/smoke-tester.md:0`, `claude/agents/tester.md:0`

```bash
grep -c -F 'A block that runs pytest never passes `-q`' factory/story-form.md
```
Expect: `1` (the human's change 1 is on `main`)

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: one file, `claude/agents/intake.md`, Stage step 2 (line 53, which ends today with "can be checked against."). The Interface gives the exact sentences to append on the same line. Step numbers 0 to 6 stay, and no other agent file gains the text. The test module and the helpers it uses (`agent_body`, `section_text`) are named.
   - Criteria: 1 (sentences present), 2 (they end step 2, with a start and an end anchor), 3 (a parametrized count for each of the seven agents, intake 1 and the others 0) and 4 (`make check`) are each one test function. Rules with a failing side: the rule is a question for a command that passes `-q`, and the Interface's only rule is that sentence. Criteria 1 and 2 pin "Such a command is a question", and the 0 rows of criterion 3 cover the side where the rule is absent. Criterion 5 (docs) is the documenter's.
   - Smoke test: both commands are runnable `grep -c` calls. Each `Expect:` is checkable. The first lists seven exact lines and the second expects `1`. I ran the second: `factory/story-form.md` already holds the human's sentence, so it prints 1. The first prints 0 for intake until the coder has run, which is expected.
   - Architecture: nothing under `src/` changes. It is an agent text, a test at the `tests/` root (the module is outside the layers) and docs, which fits CLAUDE.md. `docs/project-guide/agents.md` has the *The seven agents* section that criterion 5 names.
   - Scope: it matches the feature's Scope list. The feature's Out of scope (code check, `template/`, demo, smoke tester, archived stories) is untouched. It changes no existing test: `tests/test_claude_agent_texts.py` passes unchanged, and the Lessons are not edited (feature decision 1).
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 3. They read the agent file through `agent_body` (tests/shipped_agents.py) and `section_text` (factory.domain.sections), as the Interface says.
   - criterion 1: tests/test_claude_agent_texts_smoke_pytest.py::test_intake_stage_holds_the_pytest_quiet_rule. The Interface's sentences, verbatim, are in intake's *Stage* section.
   - criterion 2: tests/test_claude_agent_texts_smoke_pytest.py::test_pytest_quiet_rule_ends_step_two_of_intake. Exactly one *Stage* line starts with `2. The factory has already checked the story's form`. That line holds the join text from "each `Expect:` line says something..." to "passes no `-q` ", and it ends with `Such a command is a question.`.
   - criterion 3: tests/test_claude_agent_texts_smoke_pytest.py::test_only_intake_carries_the_pytest_quiet_rule. It is one parametrized test with a row for each of the seven shipped agents: intake 1, the six others 0.
   - criterion 4 (`make check`) is the factory's gate, and criterion 5 (docs) is the documenter's. Neither has a test.
   Files created: tests/test_claude_agent_texts_smoke_pytest.py. No earlier test file was changed.
   Import errors: none. Every module the tests use already exists.
   `make test`: the criterion 1 and criterion 2 tests fail, and so does the `intake` row of the criterion 3 test. In each case the sentences are not yet in claude/agents/intake.md. The six rows with a count of 0 pass already, as expected.
   `make lint`: green.
   No criterion needed interpreting.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/test_claude_agent_texts_smoke_pytest.py::test_only_intake_carries_the_pytest_quiet_rule[intake]
6. factory: started doing as self.
7. coder: Added the Interface's sentences to the end of step 2 in the *Stage* section of `claude/agents/intake.md`. They follow one space after "can be checked against." on the same line. Step 2 still starts the same way and keeps its number 0 to 6 order. No other file changed.
      - Main choice: I added the text exactly as the Interface gives it, on the existing line. I rejected a separate line or sub-bullet under step 2, because criterion 2 needs the rule on the step's own line and it must end with "Such a command is a question."
      - Refactor: the diff is one appended line, so there was nothing to change.
      - `make check`: green (`check: green`). This includes tests/test_claude_agent_texts_smoke_pytest.py and the unchanged tests/test_claude_agent_texts.py.
      - Noticed, not touched: the template/ copies of the agent files, if any, are out of scope under the feature's Out of scope list. Criterion 5's docs in `docs/project-guide/agents.md` and `docs/decisions.md` are the documenter's.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   - Acceptance criteria: `claude/agents/intake.md:53` (step 2 of *Stage*) now ends with the Interface's sentences, word for word. They follow one space after "can be checked against." on the same line. The line still starts with `2. The factory has already checked the story's form`, and steps 0 to 6 keep their numbers. Each criterion has a test in `tests/test_claude_agent_texts_smoke_pytest.py`:
     - Criterion 1: `test_intake_stage_holds_the_pytest_quiet_rule` checks that the full sentences are in `section_text(agent_body("intake"), "Stage")`.
     - Criterion 2: `test_pytest_quiet_rule_ends_step_two_of_intake` checks the start anchor, that exactly one line has it, the joining text and the ending `Such a command is a question.`.
     - Criterion 3: `test_only_intake_carries_the_pytest_quiet_rule` is one parametrized test with seven rows (intake 1, the six other agents 0). The 0 rows cover the side where the rule is absent.
     - Criterion 4: the factory's `make check` after the coder was green (journal entry 7).
   - Architecture: nothing under `src/` changes. The test sits at the `tests/` root, and its module is outside the layers. It uses the existing helpers `agent_body` (`tests/shipped_agents.py`) and `section_text` (`factory.domain.sections`), the way the other agent-text tests do. No helper is copied.
   - Security: no code, secrets or markers that silence a check.
   - Quality: the names say what they hold, the module has a docstring, and there is no dead code.
   - Work item hygiene: the Description matches what was built, and the coder's journal entry names the main choice (on the same line) and what was rejected (a separate line or sub-bullet). Criterion 5 (docs) still describes what the documenter needs: one sentence in `docs/project-guide/agents.md` and an entry in `docs/decisions.md`.
   - Earlier tests: none. The diff only adds `tests/test_claude_agent_texts_smoke_pytest.py` (status A), and no test file on `main` is changed, renamed or deleted.
10. factory: started docs as self.
11. documenter: Files changed (documents only, so I did not run `make check`; the factory's checks decide):
    - `docs/project-guide/agents.md`, *The seven agents*: one paragraph after the list of an agent file's sections. Intake's Stage step 2 asks about a smoke test command that passes pytest a `-q` the project's pytest configuration already sets, because at `-qq` pytest prints no summary line. The paragraph names the test that pins it.
    - `docs/decisions.md`: new entry *A smoke test passes no -q that the pytest configuration already sets*, dated 2026-10-20 with F0035-S0001. It gives the decisions, the reason (the smoke tests of F0022-S0005 and F0023-S0004 on 2026-10-19) and the two rejected options (a check in code, a Lessons line).

    Cross-read against the diff and found current: `README.md`, `docs/operator-guide.md` (nothing the operator does changes, as the docs criterion says). The diff is `claude/agents/intake.md` step 2, one line, which matches the Interface word for word; I found no contradiction between code and criteria. The rest of `docs/project-guide/agents.md` describes the Lessons and the pinned tests, and none of that changed.

    Stale text noticed, not touched: none.

    No findings.

    `check`: check: green (not run again: passed on tree 692d1fffd52d at 2026-10-20T05:03:52Z)
    `secrets`: secrets: green (1.0 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: I ran both smoke test commands from the repository root, as written and in order. Both met their `Expect:` lines. No findings.

    Command 1:
    ```bash
    grep -c -F 'passes no `-q` when the project'"'"'s pytest configuration already sets one' claude/agents/*.md
    ```
    ```
    claude/agents/acceptance-reviewer.md:0
    claude/agents/coder.md:0
    claude/agents/documenter.md:0
    claude/agents/intake.md:1
    claude/agents/reviewer.md:0
    claude/agents/smoke-tester.md:0
    claude/agents/tester.md:0
    ```
    Met: seven lines, exactly the ones expected (intake 1, the six others 0). Exit status 0.

    Command 2:
    ```bash
    grep -c -F 'A block that runs pytest never passes `-q`' factory/story-form.md
    ```
    ```
    1
    ```
    Met: `1`. The human's change 1 is on the branch. Exit status 0.

    Cross-check against the acceptance criteria. Nothing the smoke test showed contradicts any of them.
    - Criteria 1 to 3: the rule is in `claude/agents/intake.md:53`, the line that starts with `2. The factory has already checked the story's form`. That line ends with `Such a command is a question.`. The rule is in no other agent file (command 1).
    - Criterion 4: the smoke test does not run `make check`, so it does not show this one. The factory's earlier checks were green (journal entries 7 and 11).
    - Criterion 5: `docs/decisions.md:869` has the entry *A smoke test passes no -q that the pytest configuration already sets*. `docs/project-guide/agents.md:248` has the sentence about intake.
