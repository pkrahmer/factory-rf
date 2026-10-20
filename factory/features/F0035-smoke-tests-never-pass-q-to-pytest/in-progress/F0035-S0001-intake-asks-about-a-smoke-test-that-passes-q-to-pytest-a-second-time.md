---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-20T04:09:30.540216Z'
  lease_duration: 60
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
