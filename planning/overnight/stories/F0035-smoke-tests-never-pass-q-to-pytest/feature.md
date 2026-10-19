# Smoke tests never pass -q to pytest

## Goal

`pyproject.toml` already sets `-q` for pytest (`[tool.pytest.ini_options]`, `addopts = "-q --strict-markers"`). A smoke test that passes `-q` again runs pytest at `-qq`, and at `-qq` pytest prints no summary line (`N passed in ...`). Two smoke tests failed on 2026-10-19 for that reason alone, with every test green. F0022-S0005's command 3 (`uv run pytest -q <the nine modules> 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '`) expected `1` and printed `0` in two rounds, and the human answered it in entry 22. F0023-S0004's smoke test failed the same way. The rule was logged on 2026-10-19 and is already in the drafting brief (`planning/overnight/briefs/draft.md`, *Rules for the split*). Nothing that checks or drafts a story carries it yet. This feature puts it in two places: in intake, which checks every story before tokens are spent on it, and in this repository's story form, which the human and the helpers draft from. For the human, who answers the question such a smoke test raises, and for the smoke tester, who otherwise reports a fault in the story's text as a failed run. Done when every story below is merged, the human's change 1 is on `main` and `make check` is green.

## Scope

- `claude/agents/intake.md`, the section *Stage*, step 2: one sentence (S0001).
- `tests/test_claude_agent_texts_smoke_pytest.py` (new): the sentence, its place, and that only intake carries it (S0001).
- `docs/project-guide/agents.md` and `docs/decisions.md`, from the story's docs criterion (S0001).

## Out of scope

- A check in code (`factory-check-story`, `factory.domain.story_form`): the factory knows no pytest, and a project's pytest configuration is the project's own (decision 2).
- `template/`: it ships no `pyproject.toml` and no story form, so it has no pytest configuration and no form to hold the rule. Intake's rule reads the project's own configuration (decision 3).
- The todo demo: its `addopts` is `--strict-markers` without `-q`.
- The smoke tester: it runs the commands as written and reports what it sees. A command that breaks the rule is the story's fault, which intake catches first.
- The archived stories F0022-S0005 and F0023-S0004: they stay as they are.
- Every paid call: no story and no smoke test makes one.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`. The human's change 1 may come before S0001 or with it, at any time; S0001's second smoke test block expects it on `main`.

- S0001: Intake asks about a smoke test that passes -q to pytest a second time

## The human's changes

Checked against `factory/pipeline.yml`: the coder writes `claude/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`. `factory/story-form.md` lies outside every write path.

1. Before S0001's smoke test runs, one commit on `main`. In `factory/story-form.md`, the section `## Smoke test`, append this sentence to its paragraph, after "and stops what it started.":

   ```markdown
    A block that runs pytest never passes `-q`: `pyproject.toml` already sets it, and at `-qq` pytest prints no summary line.
   ```

   The form check reads the form's headings only, so no test and no story changes with it. The tests' own copy of a form, `STORY_FORM` in `tests/git_support.py`, stays as it is.

## Decisions taken for the human

1. The rule goes into intake's step 2, beside "the smoke test commands are runnable and each `Expect:` line says something the output can be checked against". It is a check of the same kind, and a story that breaks it is a question at intake, before any run is paid for. It does not go into the *Lessons*, whose lines `tests/test_claude_agent_texts.py` pins exactly. That would change another story's test (S0001).
2. In intake the rule is general: a command passes no `-q` when the project's pytest configuration already sets one (`addopts` in `pyproject.toml`, `pytest.ini`, `setup.cfg` or `tox.ini`). The shipped intake serves every project, and only this repository's `addopts` holds `-q` today (S0001).
3. No change to `template/`: no file there holds a pytest configuration or a story form (the feature's *Out of scope*).
4. In this repository's story form the rule names `pyproject.toml` directly, because the form is this project's own (the human's change 1).
