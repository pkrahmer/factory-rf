---
stage: docs
pr: 130
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
# The shipped agents and settings

## Assignment (as of log entry 1)

Ship the seven agents of the pipeline in v1.1's names, the settings every agent run shares, and the pipeline definition template they belong to. Each agent file holds only the four keys the runner applies, and each of those keys has an effect that a test sees in the call the runner makes. Each agent's body starts with its boundary as one sentence and what its entry contains, as v1 did, in the glossary's words (journal entry, smoke test, backlog story, recommendation, write paths); the last story of this feature adds v1's role and stage texts after those two sentences (questionnaire 1, Q29). This covers SI4.2, keeps kept thing 6 (each role's boundary in its shipped agent file) and finishes the shipping part of R30. No skills are shipped, because the runner applies no `skills` key. The template this feature ships holds two files: `template/factory/pipeline.yml`, at the path a project reads it from (`factory/pipeline.yml`, so that the template mirrors a project's tree), and `template/CLAUDE.md`, the rules file of a Python project, which carries the Python lessons of v1.1's build (`planning/lessons-for-the-skills.md`, the human, 2026-10-14); the story and feature forms are the human's to add, and a project made from this template has no `factory/story-form.md` until the human adds it, so that `StoryFormChecker` stops every stage until then. The template replaces nothing in `factory/`.

## Interface

Each of the seven files `claude/agents/<role>.md` has this shape, with the values of the table:

```text
---
model: opus
effort: medium
budget_usd: 4
tools: [Read, Grep, Glob, Edit, Bash, Write]
---
Never edit tests; a wrong test is a question.

Your entry says what you built (the paths), the main choice and the alternative you rejected, and what you noticed but did not touch.
```

| File (role) | model | effort | budget_usd | tools |
|---|---|---|---|---|
| `intake.md` | sonnet | low | 1 | Read, Grep, Glob, Edit, Bash |
| `tester.md` | opus | medium | 2 | Read, Grep, Glob, Edit, Bash, Write |
| `coder.md` | opus | medium | 4 | Read, Grep, Glob, Edit, Bash, Write |
| `reviewer.md` | opus | high | 3 | Read, Grep, Glob, Edit, Bash |
| `documenter.md` | sonnet | medium | 1.5 | Read, Grep, Glob, Edit, Bash, Write |
| `smoke-tester.md` | opus | medium | 2 | Read, Grep, Glob, Edit, Bash |
| `acceptance-reviewer.md` | opus | high | 8 | Read, Grep, Glob, Edit, Bash, Write |

The body of each file starts with two paragraphs, the boundary sentence and the entry sentence of its role:

| Role | Boundary sentence | Entry sentence |
|---|---|---|
| intake | You do not improve the story; you accept it or ask. | Your entry starts with `accepted` and then has one line for each of the Interface, the criteria, the smoke test, the architecture and the scope; or it is the numbered questions, with the form's findings among them. |
| tester | You test what the criteria say and nothing else; a case they leave open is a question. | Your entry maps each criterion to its test function, one line each, and names the files you created and any module the test run could not import. |
| coder | Never edit tests; a wrong test is a question. | Your entry says what you built (the paths), the main choice and the alternative you rejected, and what you noticed but did not touch. |
| reviewer | You find and do not fix: you write no code, not even scratch. | Your entry is the numbered findings, each with a location, what is wrong and what would fix it, or `no findings`. |
| documenter | You write for a reader who was not there; you edit no code, no test and no comment in code. | Your entry names each file you changed and why, the documents you cross-read and found current, and stale text you noticed that is not yours to fix. |
| smoke-tester | Fix nothing: run the smoke test as written and report what you observe. | Your entry gives each command's output trimmed to 40 lines and whether it met its `Expect:` line, and numbers the findings. |
| acceptance-reviewer | You propose backlog stories and never start one; you change nothing but your report and those stories. | Your entry starts with your recommendation and the number of backlog stories you propose, then has one line for each item you judged. |

`claude/settings.json`

```json
{
  "permissions": {
    "allow": [
      "Read", "Edit", "Write", "Glob", "Grep",
      "Bash(uv run *)", "Bash(uv sync*)", "Bash(make *)", "Bash(factory-check-story *)",
      "Bash(git status*)", "Bash(git diff*)", "Bash(git log*)", "Bash(git show*)",
      "Bash(git add *)", "Bash(git commit *)", "Bash(git rev-parse*)"
    ],
    "deny": [
      "Bash(git push*)", "Bash(git checkout*)", "Bash(git switch*)", "Bash(git merge*)",
      "Bash(git pull*)", "Bash(git rebase*)", "Bash(git reset*)", "Bash(git branch -D*)",
      "Bash(gh *)", "Bash(rm -rf *)"
    ]
  },
  "env": {"CLAUDE_CODE_FORK_SUBAGENT": "0"}
}
```

`template/factory/pipeline.yml` is the pipeline definition below. Its roles are the seven files above, and nothing else is in `template/` but `CLAUDE.md` (below).

```yaml
contract: "1.0"
attempts_cap: 2
crash_cap: 2
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 10}
  lint: {time_limit: 5}
  test: {time_limit: 10}
roles:
  intake: {write_paths: ["{work_item}"]}
  tester: {write_paths: ["tests/*"]}
  coder: {write_paths: ["src/*"]}
  reviewer: {write_paths: ["{work_item}"]}
  documenter: {write_paths: ["README.md", "docs/*"]}
  smoke-tester: {write_paths: ["{work_item}"]}
  acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"]}
stages:
  intake: {role: intake, next: [tests]}
  tests: {role: tester, next: [doing], checks: [lint], reports: [test]}
  doing: {role: coder, next: [review, tests], checks: [check]}
  review: {role: reviewer, next: [docs, doing], round_cap: 3}
  docs: {role: documenter, next: [smoke-test, doing], checks: [check], round_cap: 3}
  smoke-test: {role: smoke-tester, next: [approval, doing], round_cap: 3}
  acceptance: {role: acceptance-reviewer, next: [approval]}
  approval: {approval: true, next: [done, doing]}
  done: {}
```

`template/CLAUDE.md` is exactly the following text, which sits in the fence below with four spaces in front of each line (the lines of a fence never start with `#` in these files); a test removes the four spaces from every line that has them:

```markdown
    # <project>

    <One sentence: what this repository is.> Built by the factory (github.com/pkrahmer/factory); the pipeline's rules reach every agent in its instructions, so this file holds only what is true of this project.

    ## Language
    - Everything in this repository is English: code, comments, docs, work items, commit messages.

    ## Architecture
    - <Layers, dependency direction, what is pure, where wiring happens.>
    - <Typing and validation rules.>

    ## Tests
    - <Framework; where tests live; fixtures; what may be faked and what may not.>
    - Tests pass `mypy --strict` once the code exists: never use the value of a call to a function typed `-> None` (no `assert f() is None`); call it as a statement.
    - To test that a Pydantic model refuses an unknown or a wrong-typed field, construct it through a variable typed `type[BaseModel]`; assign to a field of a frozen model with `setattr(instance, field, value)`, the field's name in a variable; call an abstract class through a variable typed `type[object]`. None of these needs a `type: ignore`.
    - Fake commit ids and other hexadecimal test values are low-entropy (`"a" * 40`), so that `make secrets` stays green without a baseline entry.

    ## Docs
    - `README.md` is for the newcomer: what it is, how to run it, where to look next. `docs/project-guide.md` is the guide for agents and `docs/decisions.md` the decision log. The documenter stage keeps them true from each story's docs criterion; the coder does not write them.
    - Docstrings: one per module (its purpose, a sentence) and one per public class and function in <the packages that form the interface>; none on private names or where the signature says it all. Comments say why, never what.

    ## Checks
    - `make check` must be green before any stage reports done. It runs <lint, types, sast, secrets, licenses, tests with coverage>. `make lint` and `make test` run <subset>; the pipeline knows only these three targets.

    ## Not without asking (end the stage with `question`)
    - New dependency, new top-level package, change to `factory/`, change to a test you did not write, a new entry in `.secrets.baseline` or a `pragma: allowlist secret`, a `nosemgrep` or `nosec` marker, a licence outside the allow list.
```

Rules:

- The agents are read with `FrontmatterAgentDefinitionReader(Path("claude"))`: the directory `claude/agents/` is the agent home's `agents/` folder as the entrypoint installs it.
- The keys the runner applies are shown by the call it makes. For an agent definition read from a shipped file, `ClaudeCodeRuntime` (F0001-S0009 and S0010) passes `--model <model>`, `--effort <effort>`, `--tools` with the tools, `--max-budget-usd <budget_usd>`, and the file's body in the file named by `--append-system-prompt-file`.
- The settings allow `Bash(factory-check-story *)` and no other `factory-` command: an agent may check a story's form and may not run `factory-run`, `factory-watch` or `factory-bill`.

Tests: `tests/test_claude_files.py` (reads `claude/`, `template/factory/pipeline.yml` and `template/CLAUDE.md` from the repository root), `tests/adapters/test_shipped_agents_effect.py` (runs `ClaudeCodeRuntime` against the stand-in executable of `tests/adapters/claude_stand_in.py` (`write_stand_in`, `read_calls`), which records its arguments and the content of the file named by `--append-system-prompt-file`, over each shipped agent).

## Acceptance criteria

1. `claude/agents/` holds exactly the seven files `intake.md`, `tester.md`, `coder.md`, `reviewer.md`, `documenter.md`, `smoke-tester.md` and `acceptance-reviewer.md`.
2. `FrontmatterAgentDefinitionReader(Path("claude"))` reads each of the seven without error (no dead key, SI4.1), and `names()` lists them sorted.
3. The front matter of each file holds exactly the keys `model`, `effort`, `budget_usd` and `tools`, with the values of the table (`budget_usd` of the documenter is `1.5`).
4. For each shipped agent, `ClaudeCodeRuntime` passes `--model` followed by the file's `model` (SI4.2, the key `model`).
5. For each shipped agent, it passes `--effort` followed by the file's `effort` (the key `effort`).
6. For each shipped agent, it passes `--tools` with a value that contains every tool of the file's `tools` and no other tool (the key `tools`).
7. For each shipped agent, it passes `--max-budget-usd` followed by the file's `budget_usd`, equal as a decimal number (the key `budget_usd`).
8. For each shipped agent, the file named by `--append-system-prompt-file` contains the file's body (the instructions).
9. The body of each file starts with its boundary sentence, a blank line and its entry sentence, as in the table (kept 6: the role's boundary is in its file).
10. `claude/settings.json` parses as JSON and equals the document shown above.
11. `template/factory/pipeline.yml` is read by `RuamelPipelineDefinitionReader` into a valid `PipelineDefinition` whose roles are exactly the names of the seven agent files.
12. `template/` holds exactly two files, `template/CLAUDE.md` and `template/factory/pipeline.yml`, and no other file or directory except `factory`.
13. `template/CLAUDE.md` equals the text shown in the Interface (the lines of its block with the four leading spaces removed): its `## Tests` section carries the three Python rules (no value of a call typed `-> None`; refused fields, frozen fields and abstract classes through typed variables; low-entropy hexadecimal test values); the file ends with one newline after its last line.
14. make check stays green.
15. docs: `docs/project-guide.md` lists the seven shipped agents with their model, effort, budget and tools, says that each body starts with the boundary and the entry contents and that the last story of this feature adds v1's role and stage texts after them, says that the forms (`factory/story-form.md`, `factory/feature-form.md`) are the human's to add to a project made from the template and that `StoryFormChecker` stops every stage until `factory/story-form.md` exists, and shows `template/factory/pipeline.yml` as the starting pipeline definition; `docs/operator-guide.md` says that the entrypoint installs the agents and the settings into `FACTORY_CLAUDE_HOME` at every start and that an agent may run `factory-check-story` and no other `factory-` command; `docs/project-guide.md` names `template/CLAUDE.md` as the starting rules file of a Python project.

## Demo

```bash
uv run python -c "
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
reader = FrontmatterAgentDefinitionReader(Path('claude'))
for name in reader.names():
    agent = reader.read(name)
    print(name, agent.model, agent.effort, agent.budget_usd)
"
```
Expect: seven lines in this order: `acceptance-reviewer opus high 8`, `coder opus medium 4`, `documenter sonnet medium 1.5`, `intake sonnet low 1`, `reviewer opus high 3`, `smoke-tester opus medium 2`, `tester opus medium 2`.

```bash
uv run python -c "
from pathlib import Path
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
definition = RuamelPipelineDefinitionReader().parse(Path('template/factory/pipeline.yml').read_text())
print(definition.first_stage(), sorted(definition.roles))
"
```
Expect: one line, `intake ['acceptance-reviewer', 'coder', 'documenter', 'intake', 'reviewer', 'smoke-tester', 'tester']`.

```bash
uv run python -c "
import json
settings = json.load(open('claude/settings.json'))
print(len(settings['permissions']['allow']), len(settings['permissions']['deny']), 'Bash(gh *)' in settings['permissions']['deny'])
"
```
Expect: one line, `16 10 True`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete paths (`claude/agents/<role>.md`, `claude/settings.json`, `template/factory/pipeline.yml`, `template/CLAUDE.md`). The agent table, boundary and entry sentences, settings JSON, pipeline YAML and CLAUDE.md text are given in full. The runtime flags are named (`--model`, `--effort`, `--tools`, `--max-budget-usd`, `--append-system-prompt-file`), as are the test files and the stand-in helpers.
   - Criteria: each can be tested by one test function. Criteria 4 to 8 are parametrized over the seven agents. The refusing side of every rule has a criterion. Dead keys are refused by criteria 2 and 3 (exactly four keys). The "no other `factory-` command" rule is fixed by the exact-equality criterion 10. The "template holds nothing else" rule is criterion 12. The only-one-newline rule is criterion 13.
   - Demo: all three commands are runnable. Each `Expect:` line is checkable. I counted the settings by hand: 16 allow entries and 10 deny entries, and the sorted agent order matches `names()`.
   - Architecture: only data files plus tests in the existing `tests/` layout. Nothing is placed in the layers. The agent reader and pipeline reader are the existing adapters.
   - Scope: within F0010's scope (SI4.2, kept 6, R30, decisions 16 and 17). Skills and forms are not shipped, as "Out of scope" requires. v1's role and stage texts are left to S0017.
3. tester: Wrote the red tests for the shipped agents, the shared settings and the template.

   Criterion → test:
   - criterion 1: tests/test_claude_files.py::test_agents_directory_holds_exactly_the_seven_agent_files
   - criterion 2: tests/test_claude_files.py::test_every_shipped_agent_is_read_and_listed_sorted
   - criterion 3: tests/test_claude_files.py::test_front_matter_holds_the_four_applied_keys_with_their_values. It is parametrized over the seven agents. It checks that the raw front matter keys are exactly the four keys, and that the values read through the reader match the table. `tools` is compared as a list in table order and `budget_usd` as a Decimal, so the documenter's is 1.5.
   - criterion 4: tests/adapters/test_shipped_agents_effect.py::test_call_passes_the_agent_model
   - criterion 5: tests/adapters/test_shipped_agents_effect.py::test_call_passes_the_agent_effort
   - criterion 6: tests/adapters/test_shipped_agents_effect.py::test_call_passes_exactly_the_agent_tools. The `--tools` value is split on commas and whitespace and compared as a set.
   - criterion 7: tests/adapters/test_shipped_agents_effect.py::test_call_passes_the_agent_budget. The value is compared as a Decimal.
   - criterion 8: tests/adapters/test_shipped_agents_effect.py::test_instructions_file_holds_the_agent_body
   - criterion 9: tests/test_claude_files.py::test_body_starts_with_the_boundary_and_the_entry_sentence
   - criterion 10: tests/test_claude_files.py::test_settings_are_the_shared_permissions_and_environment. It checks exact equality, which also covers "no other `factory-` command".
   - criterion 11: tests/test_claude_files.py::test_template_pipeline_definition_is_valid_with_the_shipped_roles
   - criterion 12: tests/test_claude_files.py::test_template_holds_only_the_rules_file_and_the_pipeline_definition
   - criterion 13: tests/test_claude_files.py::test_template_rules_file_is_the_python_project_text. The expected text is the Interface block with the four spaces removed. I checked it against the ticket by script, and it ends with exactly one newline.
   - criteria 14 and 15: not tested (make check, docs).

   Criteria 4 to 8 run the real `ClaudeCodeRuntime` against the stand-in from `tests/adapters/claude_stand_in.py`. A module-scoped fixture `calls` reads each shipped agent with `FrontmatterAgentDefinitionReader(Path("claude"))` and makes one run per agent, with no guard and a success reply. It runs each agent once, not once per test.

   Files created:
   - tests/shipped_agents.py: a shared table of the seven agents with their values, boundary and entry sentences, plus ROOT and AGENT_HOME.
   - tests/test_claude_files.py
   - tests/adapters/test_shipped_agents_effect.py

   Expected red state:
   - All modules import; nothing under test is missing from `src/`.
   - The tests fail because `claude/agents/`, `claude/settings.json` and `template/` do not exist yet. Every runtime-effect test errors in the `calls` fixture because there is no agents directory.

   `make lint` is green.

   Open for the coder: the files belong in `claude/` and `template/`. Those paths are outside `src/*`, which is the coder role's write path in the template pipeline. Whether the factory's own lane for this project covers them is the factory's concern, not mine.

   `make lint`: lint: green
   `make test`: ERROR tests/adapters/test_shipped_agents_effect.py::test_instructions_file_holds_the_agent_body[acceptance-reviewer]
4. coder: Built the shipped data files in commit 4635b99. No code under `src/` changed.

   Files:
   - `claude/agents/{intake,tester,coder,reviewer,documenter,smoke-tester,acceptance-reviewer}.md`: front matter with exactly `model`, `effort`, `budget_usd` and `tools`, set to the table's values. The documenter's `budget_usd` is `1.5`, and `tools` is written as a YAML flow list in table order. Each body is the boundary sentence, a blank line and the entry sentence, with nothing else; the last story of the feature adds v1's role and stage texts after them.
   - `claude/settings.json`: the Interface's JSON, kept in its line layout.
   - `template/factory/pipeline.yml`: the Interface's pipeline definition, copied verbatim.
   - `template/CLAUDE.md`: extracted by script from the ticket's fenced block with the four leading spaces removed. It ends with a single newline.

   Main choice: I generated the agent files from one table, so the values cannot drift from the Interface by a typo. I rejected writing each file by hand. The bodies carry no extra text, because the assignment leaves v1's texts to the later story.

   Refactor: nothing to refactor; the diff is data files only.

   `make check` is green (coverage 99.53 %). The two new test modules pass: 55 tests.

   Noticed, not touched: the tester's open point. `claude/` and `template/` lie outside `src/*`, the coder write path in the template pipeline. No hook refused the writes here, so this project's own lane covers them.

   `make check`: check: green
5. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (7 agent files, `claude/settings.json`, `template/CLAUDE.md`, `template/factory/pipeline.yml`, and three test modules) against the ticket.

   Groups 1 to 3 pass:
   - Acceptance criteria: every criterion from 1 to 13 has a test that checks what it is named after. Criteria 4 to 8 run the real `ClaudeCodeRuntime` against the stand-in. Criterion 6 compares the tools as sets, so it also catches an extra tool. Criterion 10 checks exact equality, which also covers "no other `factory-` command". Criterion 12 uses `rglob`, which also catches dotfiles. The coder's entry reports `make check` green.
   - Architecture: the diff is data files and tests only.
   - Security: no secrets and no suppression markers.

   Group 4 (quality) fails:

   1. `tests/shipped_agents.py:12` `_READ_ONLY_TOOLS`: the name says "read-only", but the list holds `Edit` and `Bash`, which both write. Fix: rename it to what it is, the tools without `Write` (for example `_TOOLS_WITHOUT_WRITE`). Rename `_ALL_TOOLS` to match if needed.
   2. `tests/adapters/test_shipped_agents_effect.py:67` `_body` repeats the front-matter split of `tests/test_claude_files.py:104` `_front_matter_and_body`: same file path, same `split_front_matter(RuamelYamlHandler(), …)`, same `.strip()`. Fix: move one helper that returns the raw front matter and the body into `tests/shipped_agents.py`, and use it in both modules.

   Both findings are in test code the tester wrote. Per R9, the coder ends with `tests` and names these two changes, and the tester makes exactly them. I did not check ticket hygiene (group 5), because the review stops at the first failing group.
6. coder: Both review findings are in test code the tester wrote, so per R9 I am handing them to the tester unchanged. Make exactly these two changes:
   1. `tests/shipped_agents.py`: rename `_READ_ONLY_TOOLS` to `_TOOLS_WITHOUT_WRITE`, because the list holds `Edit` and `Bash`. Rename `_ALL_TOOLS` to match only if the pair reads wrong after the first rename.
   2. Move the front-matter split into `tests/shipped_agents.py` as one shared helper. It is currently in two places: `_front_matter_and_body` in `tests/test_claude_files.py` and `_body` in `tests/adapters/test_shipped_agents_effect.py`. The shared helper reads the agent file, calls `split_front_matter(RuamelYamlHandler(), …)`, and returns the raw front matter and the stripped body. Both modules use it, and both private copies are removed.

   Behaviour stays the same and no test changes what it checks. I made no change to the data files under `claude/` and `template/` (commit 4635b99) or to `src/`.
7. tester: I made the two test changes the coder named in entry 6, which come from the reviewer's findings in entry 5. No test checks anything different from before.

   1. `tests/shipped_agents.py`: renamed `_READ_ONLY_TOOLS` to `_TOOLS_WITHOUT_WRITE`, because the list holds `Edit` and `Bash`. I kept `_ALL_TOOLS` as it is, since `_ALL_TOOLS` next to `_TOOLS_WITHOUT_WRITE` reads correctly.
   2. `tests/shipped_agents.py`: added one shared helper, `front_matter_and_body(name) -> tuple[str, str]`. It reads `claude/agents/<name>.md`, calls `split_front_matter(RuamelYamlHandler(), …)`, and returns the raw front matter and the stripped body. I removed both private copies:
      - `_front_matter_and_body` from `tests/test_claude_files.py`. The front-matter key test now loads the raw front matter itself with `RuamelYamlHandler().load`.
      - `_body` from `tests/adapters/test_shipped_agents_effect.py`.

      Both modules now import the shared helper, and the imports they no longer need are gone.

   I changed no data files under `claude/` or `template/` and nothing under `src/`.

   `make lint`: green. `make test`: green.

   `make lint`: lint: green
   `make test`: test: green
8. coder: Round 1. Both findings from entry 5 were in test code, and the tester fixed them in entry 7 as I asked in entry 6:
   - `_READ_ONLY_TOOLS` is now `_TOOLS_WITHOUT_WRITE`.
   - The front-matter split is now one shared helper, `front_matter_and_body`, in `tests/shipped_agents.py`.

   That leaves nothing for the coder to do this round. The data files under `claude/` and `template/` are unchanged since commit 4635b99, and nothing under `src/` changed.

   Refactor: nothing to refactor. My diff is still data files only.

   I ran `make check` against the tester's updated tests and it is green, with coverage at 99.53 %. It ran longer than the 120 s foreground limit, so the tool moved it to the background. I waited for it to finish and read its output.

   Noticed, not touched: nothing new.

   `make check`: check: green
9. reviewer: Round 1 re-review of `git diff main...HEAD -- . ':!factory'`. The diff has 7 agent files, `claude/settings.json`, `template/CLAUDE.md`, `template/factory/pipeline.yml`, `tests/shipped_agents.py`, `tests/test_claude_files.py` and `tests/adapters/test_shipped_agents_effect.py`. I read it against the ticket.

   No findings.

   - Acceptance criteria:
     - Criteria 1 to 13 each have a test that checks what the criterion says.
     - Criterion 3 checks two things: the raw front-matter keys are exactly the four, and the values read back through the reader match the table. `budget_usd` is compared as a Decimal, so the documenter's `1.5` is checked.
     - Criteria 4 to 8 run the real `ClaudeCodeRuntime` against the stand-in, once per shipped agent, through a module-scoped fixture.
     - Criterion 6 compares the tools as sets, so an extra tool or a missing one fails.
     - Criterion 10 checks exact equality, which also covers "no other `factory-` command".
     - Criterion 12 uses `rglob`, so it also catches dotfiles and extra directories.
     - Criterion 13 checks the exact text with one trailing newline.
     - The Interface states no numeric limit that would need a test on both sides.
     - The coder's entry 8 reports `make check` green.
   - Architecture: the diff is data files and tests only. Nothing under `src/` changed. The test helpers at the `tests/` root follow the existing convention (`human_clone.py`, `acceptance_walk.py`).
   - Security: no secrets and no suppression markers. The fake values in the tests are plain.
   - Quality: both round-1 findings are fixed.
     - The list in `tests/shipped_agents.py` is now `_TOOLS_WITHOUT_WRITE`.
     - The front-matter split is one shared helper, `front_matter_and_body`, in `tests/shipped_agents.py`. Both modules use it, and no private copy is left.
     - Module and public-name docstrings are present.
   - Ticket hygiene:
     - The log gives the main choice (agent files generated from one table) and the alternative rejected (writing each file by hand).
     - `Assignment` matches what was built. The template holds two files and nothing in `factory/` changed.
     - Criterion 15, the docs criterion, still says what the documenter must write.

   Open, not a finding: the template gives the coder role the write path `src/*` only, so a project made from the template could not have its coder write data files outside `src/`, as this story's own coder did. The ticket's Interface specifies those write paths, so this is the human's call if it matters.
