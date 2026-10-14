# v1's role and stage texts in the shipped agents

## Assignment (as of log entry 1)

Carry v1's role and stage texts into the seven shipped agents, in the glossary's words (questionnaire 1, Q29: v1's texts, renamed, so that the baseline run compares with v1's run on the same instructions). The shipped agent bodies of the earlier story hold only each role's boundary sentence and entry sentence; this story adds after them what v1 preloaded into each agent as skills: the pipeline rules every stage agent works under, the role's text where v1 had one, and the stage's text. The source is v1's `claude/` tree, which the human copies into the repository as `docs/v1-texts/` (the files `agents/*.md` and `skills/*/SKILL.md`, in the same relative paths) before this story starts; the coder reads it and writes only under `claude/`. When `docs/v1-texts/` is missing the coder ends with `question`. The text is renamed with the table below, and `stuck` becomes `question` (F0005 decision 24: v1.1 has no `stuck`; an agent that cannot finish asks). Sentences that describe v1's own mechanics are rewritten to what v1.1 does or dropped when v1.1 does it in code: the factory commits, pushes and moves the work item (the prompt's end line), so no agent commits or pushes; the promotion of a story, the round caps and the pipeline files are the factory's and the human's. The acceptance reviewer's text names the report sections that F0009 reads. This story covers no condition of its own; it finishes R30's shipped agents and keeps kept thing 6. A run of the real agents is the morning observation (the baseline run). No skill file is shipped (the runner applies no `skills` key).

## Interface

Each `claude/agents/<role>.md` keeps its front matter and its first two paragraphs (the boundary sentence and the entry sentence of the earlier story), and then has these `## ` sections in this order and no other `## ` heading:

- `## Rules`: v1's pipeline rules `factory-rules` carries. R1 to R4, R6, R8, R9 and R11 are carried with the rename table; R2 is rewritten to the v1.1 contract: the agent ends with a decision, one of the `Allowed decisions` its prompt lists, which always include `question`, and with a journal entry. R5, R7, R10 and R12 to R15 describe v1's tickets, stage table, commit conventions, round caps and pipeline files: they are rewritten in the glossary's words to what the prompt, the pipeline definition and the write paths say, or dropped when v1.1 does them in code. The section says that the factory commits, pushes and moves the work item, and that the agent never pushes, checks out, switches, merges, pulls or calls `gh`.
- `## Role`: v1's role skill, for the roles that had one: `tester` (`role-tester`), `coder` (`role-coder`), `reviewer` (`role-reviewer`), `documenter` (`role-documenter`) and `acceptance-reviewer` (`role-acceptor`). `intake` and `smoke-tester` have no `## Role` section.
- `## Stage`: v1's stage skill: `intake` (`stage-intake`), `tester` (`stage-tests`), `coder` (`stage-doing`), `reviewer` (`stage-review`), `documenter` (`stage-docs`), `smoke-tester` (`stage-demo`) and `acceptance-reviewer` (`stage-feature`).

The rename table, applied to every carried text:

| v1 | v1.1 |
|---|---|
| ticket | work item |
| log | journal |
| `drafts/` | `backlog/` |
| `ongoing/` | `in-progress/` |
| promote | start |
| `stages.yml`, stage table | the pipeline definition (`factory/pipeline.yml`) |
| lane | write paths |
| gate, the stage `accept` | approval |
| demo (the stage and the agent) | smoke test |
| acceptor | acceptance reviewer |
| outcome (of an agent) | decision |
| verdict | recommendation |
| `max_rounds` | `round_cap` |
| `stuck` | `question` |

The decisions each body names, from the stage's `next` in `template/factory/pipeline.yml` and `question`: `intake` ends with `tests` or `question`; `tester` with `doing` or `question`; `coder` with `review`, `tests` or `question`; `reviewer` with `docs`, `doing` or `question`; `documenter` with `smoke-test`, `doing` or `question`; `smoke-tester` with `approval`, `doing` or `question`; `acceptance-reviewer` with `approval` or `question`.

The acceptance reviewer's body names the report sections `## Recommendation` and `## Proposed stories` (which F0009-S0001 and S0004 read), the three recommendations `accepted`, `accepted with stories` and `not accepted`, and says that proposed stories are written into the feature's `backlog/`.

Anchors, phrases that must appear in the body after the rename (they show that the text was carried, not summarised): in `## Rules` of every body `Git is the only truth.` and ``To ask the human, end with `question` ``; `intake` `Check that the story is buildable before anyone spends tokens on it.`; `tester` `You write tests, not code.` and ``Run `make test 2>&1 | tail -5` once``; `coder` `You make the failing tests pass without changing them` and `Refactor, once.`; `reviewer` `You review a diff against a work item.` and `You do not edit code, and you do not write any`; `documenter` `You write for the reader who was not there` and `Run every example you wrote or changed.`; `smoke-tester` `You run the smoke test, record what happened and judge it against the work item. You do not fix anything.`; `acceptance-reviewer` `You judge and you propose; you build nothing.` and `Do the eight checks`.

Tests: `tests/test_claude_agent_texts.py` (reads `claude/agents/*.md` and `template/factory/pipeline.yml` from the repository root; a file of its own, so that the earlier story's `tests/test_claude_files.py` stays as it is).

## Acceptance criteria

1. The body of each of the seven files still starts with its boundary sentence, a blank line and its entry sentence, exactly as in the table of the earlier story.
2. After those two paragraphs the `## ` headings of each body are, in order, `## Rules`, `## Role` and `## Stage`, with no `## Role` for `intake` and `smoke-tester` and no other `## ` heading.
3. No body contains the word `stuck`.
4. No body contains, as a whole word and in any case, any of `ticket`, `lane`, `gate`, `demo`, `acceptor`, `verdict`, `outcome` (also in the plural), `drafts`, `ongoing`, `promote`, `max_rounds` or `stages.yml`.
5. Each body names every decision of its stage in inline code, as listed under the decisions each body names: for example the body of `coder` contains `` `review` ``, `` `tests` `` and `` `question` ``, the decisions derived from the `next` of the role's stage in `template/factory/pipeline.yml`.
6. The `## Rules` section of each body contains the anchors `Git is the only truth.` and ``To ask the human, end with `question` ``.
7. The `## Rules` section of each body says that the factory commits, pushes and moves the work item, and that the agent never pushes, checks out, switches, merges, pulls or calls `gh`.
8. The `## Role` and `## Stage` sections of each body contain the anchors listed for its role (one test case for each role).
9. The body of `acceptance-reviewer` names `## Recommendation` and `## Proposed stories`, and each of `accepted`, `accepted with stories` and `not accepted`.
10. The body of `acceptance-reviewer` says that proposed stories are written into the feature's `backlog/`.
11. The body of `smoke-tester` tells the agent to compare each command's output with its `Expect:` line and to put the trimmed output into its journal entry.
12. The body of `coder` says that a test that cannot pass is a question, and that when the human's answer calls for a test change the coder ends with `tests`.
13. make check stays green.
14. docs: `docs/project-guide.md` says that each shipped agent's body carries v1's rules, role and stage texts renamed with the table above after its two sentences, lists the rename table, and says where an agent's text is changed (`claude/agents/`); `docs/decisions.md` records why v1's texts were carried over and renamed (questionnaire 1, Q29: the baseline run compares with v1's run on the same instructions) and that `stuck` does not exist in v1.1.

## Demo

```bash
uv run python -c "
import re
from pathlib import Path
for path in sorted(Path('claude/agents').glob('*.md')):
    print(path.stem, re.findall(r'^## .*', path.read_text(), re.M))
"
```
Expect: seven lines, one for each agent in sorted order. The lists are `['## Rules', '## Stage']` for `intake` and `smoke-tester`, and `['## Rules', '## Role', '## Stage']` for the other five.

```bash
uv run python -c "
import re
from pathlib import Path
banned = re.compile(r'\b(ticket|lane|gate|demo|acceptor|verdict|outcome|stuck)s?\b', re.I)
print(sum(len(banned.findall(path.read_text())) for path in Path('claude/agents').glob('*.md')))
"
```
Expect: one line, `0`.

## Log (append only)

1. 2026-10-12 human: created.
