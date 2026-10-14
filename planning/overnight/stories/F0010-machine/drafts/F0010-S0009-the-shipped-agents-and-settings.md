# The shipped agents and settings

## Assignment (as of log entry 1)

Ship the seven agents of the pipeline in v1.1's names, the settings every agent run shares, and the pipeline definition template they belong to. Each agent file holds only the four keys the runner applies, and each of those keys has an effect that a test sees in the call the runner makes. Each agent's body starts with its boundary as one sentence and what its entry contains, as v1 did, in the glossary's words (journal entry, smoke test, backlog story, recommendation, write paths); the last story of this feature adds v1's role and stage texts after those two sentences (questionnaire 1, Q29). This covers SI4.2, keeps kept thing 6 (each role's boundary in its shipped agent file) and finishes the shipping part of R30. No skills are shipped, because the runner applies no `skills` key. `template/factory/pipeline.yml` is the only file of the template this feature ships, at the path a project reads it from (`factory/pipeline.yml`, so that the template mirrors a project's tree); the story and feature forms are the human's to add, and a project made from this template has no `factory/story-form.md` until the human adds it, so that `StoryFormChecker` stops every stage until then. The template replaces nothing in `factory/`.

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

`template/factory/pipeline.yml` is the pipeline definition below. Its roles are the seven files above, and nothing else is in `template/`.

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

Rules:

- The agents are read with `FrontmatterAgentDefinitionReader(Path("claude"))`: the directory `claude/agents/` is the agent home's `agents/` folder as the entrypoint installs it.
- The keys the runner applies are shown by the call it makes. For an agent definition read from a shipped file, `ClaudeCodeRuntime` (F0001-S0009 and S0010) passes `--model <model>`, `--effort <effort>`, `--tools` with the tools, `--max-budget-usd <budget_usd>`, and the file's body in the file named by `--append-system-prompt-file`.
- The settings allow `Bash(factory-check-story *)` and no other `factory-` command: an agent may check a story's form and may not run `factory-run`, `factory-watch` or `factory-bill`.

Tests: `tests/test_claude_files.py` (reads `claude/` and `template/factory/pipeline.yml` from the repository root), `tests/adapters/test_shipped_agents_effect.py` (runs `ClaudeCodeRuntime` against the stand-in executable of `tests/adapters/claude_stand_in.py` (`write_stand_in`, `read_calls`), which records its arguments and the content of the file named by `--append-system-prompt-file`, over each shipped agent).

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
12. `template/` holds exactly one file, `template/factory/pipeline.yml`, and no other file or directory except `factory`.
13. make check stays green.
14. docs: `docs/project-guide.md` lists the seven shipped agents with their model, effort, budget and tools, says that each body starts with the boundary and the entry contents and that the last story of this feature adds v1's role and stage texts after them, says that the forms (`factory/story-form.md`, `factory/feature-form.md`) are the human's to add to a project made from the template and that `StoryFormChecker` stops every stage until `factory/story-form.md` exists, and shows `template/factory/pipeline.yml` as the starting pipeline definition; `docs/operator-guide.md` says that the entrypoint installs the agents and the settings into `FACTORY_CLAUDE_HOME` at every start and that an agent may run `factory-check-story` and no other `factory-` command.

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
